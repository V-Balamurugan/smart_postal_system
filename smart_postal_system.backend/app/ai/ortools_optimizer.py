"""
Phase 4: Google OR-Tools CP-SAT Combinatorial Optimizer (Hybrid Mode)
======================================================================

Uses the CP-SAT (Constraint Programming - Satisfiability) solver to find
the globally optimal assignment of vehicles and employees for a delivery
route, incorporating ML predictions (delay risk, operational costs, and
demand-based dynamic weighting).
"""

from __future__ import annotations

import logging
import datetime
from typing import Any, Dict, List

from app.ai.ai_utils import (
    SCALE,
    build_optimized_sequence,
    compute_cost_metrics,
    compute_total_weight,
    get_route_distance,
    get_route_duration,
    get_route_start_branch_id,
    get_vehicle_branch,
    get_vehicle_capacity,
    is_employee_available,
    is_employee_workload_ok,
    is_vehicle_available,
)
from app.ai.objective import ORToolsObjectiveBuilder, PrecomputedScores, ScaledWeights
from app.ai.solver import ORToolsSolver
from app.ai.variable import ORToolsVariableBuilder

logger = logging.getLogger(__name__)


class ORToolsOptimizer:
    """
    CP-SAT based combinatorial optimizer for postal route assignment.
    """

    @classmethod
    def optimize(
        cls,
        *,
        route: Any,
        vehicles: List[Any],
        employees: List[Any],
        parcels: List[Any],
        weights: Dict[str, float],
        max_time_seconds: float = 5.0,
        use_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the CP-SAT solver and return the optimized assignment result dict.
        """
        # Lazy import — raises ImportError if ortools is not installed
        from ortools.sat.python import cp_model  # noqa: F401  (validates install)

        n_vehicles = len(vehicles)
        n_employees = len(employees)
        n_parcels = len(parcels)

        if n_vehicles == 0 or n_employees == 0 or n_parcels == 0:
            raise ValueError("Insufficient data for OR-Tools optimizer.")

        total_weight = compute_total_weight(parcels)
        route_start_branch_id = get_route_start_branch_id(route)
        distance_km = get_route_distance(route)
        duration_min = get_route_duration(route)

        # ------------------------------------------------------------------ #
        #  1. Dynamic Weighting (ML Demand Forecast)
        # ------------------------------------------------------------------ #
        is_peak_day = False
        weights_copy = weights.copy()

        if use_hybrid:
            try:
                from app.ai.demand_forecaster import DemandForecaster
                branch_id = getattr(route, "start_branch_id", None)
                if branch_id:
                    forecasts = DemandForecaster.forecast_days(branch_id, datetime.date.today(), days=1)
                    if forecasts and forecasts[0].get("is_peak_day"):
                        is_peak_day = True
            except Exception as e:
                logger.warning("Could not determine peak day status: %s", e)

        if use_hybrid and is_peak_day:
            original_workload = weights_copy.get("employee_workload", 20.0)
            boost = 15.0
            weights_copy["employee_workload"] = original_workload + boost
            
            # Decrease other weights proportionally so they still sum to 100
            other_keys = [k for k in weights_copy.keys() if k != "employee_workload"]
            total_others = sum(weights_copy[k] for k in other_keys)
            if total_others > 0:
                for k in other_keys:
                    weights_copy[k] -= (weights_copy[k] / total_others) * boost

        # Precompute standard headroom scores
        scores = PrecomputedScores.from_inputs(
            vehicles=vehicles,
            employees=employees,
            parcels=parcels,
            route=route,
        )

        # ------------------------------------------------------------------ #
        #  2. Pre-compute ML Costs & Delay Risks (ML Predictions)
        # ------------------------------------------------------------------ #
        vehicle_cost_scores = []
        actual_predicted_costs = []
        for veh in vehicles:
            if use_hybrid:
                try:
                    from app.ai.cost_predictor import CostFeatureExtractor, CostPredictor
                    v_type = getattr(veh, "vehicle_type", "VAN")
                    features = CostFeatureExtractor.extract_features(
                        weight=total_weight,
                        distance=distance_km,
                        duration=duration_min,
                        vehicle_type=v_type,
                        parcel_count=n_parcels
                    )
                    pred_res = CostPredictor.predict(features)
                    p_cost = pred_res["predicted_cost"]
                    actual_predicted_costs.append(p_cost)
                    
                    # Convert cost to score (lower cost -> higher score)
                    cost_score = max(0.0, 100.0 - (p_cost / 50.0))
                    vehicle_cost_scores.append(int(cost_score * SCALE))
                except Exception as e:
                    logger.warning("Failed to predict cost: %s", e)
                    vehicle_cost_scores.append(int(max(0.0, 100.0 - distance_km) * SCALE))
                    actual_predicted_costs.append(distance_km * 12.5)
            else:
                vehicle_cost_scores.append(int(max(0.0, 100.0 - distance_km) * SCALE))
                actual_predicted_costs.append(distance_km * 12.5)

        delay_scores = []
        for i, veh in enumerate(vehicles):
            row = []
            for j, emp in enumerate(employees):
                if use_hybrid:
                    try:
                        from app.ai.delay_prediction import DelayFeatureExtractor, DelayPredictor
                        day_of_week = datetime.date.today().weekday()
                        dummy_parcel = type('DummyParcel', (), {'weight': total_weight})()
                        features = DelayFeatureExtractor.extract_features(
                            parcel=dummy_parcel,
                            route=route,
                            parcel_count=n_parcels,
                            day_of_week=day_of_week
                        )
                        prob = DelayPredictor.predict(features)["delay_probability"]
                        row.append(int((1.0 - prob) * SCALE))
                    except Exception as e:
                        logger.warning("Failed to predict delay: %s", e)
                        row.append(int(0.8 * SCALE))
                else:
                    row.append(int(1.0 * SCALE))
            delay_scores.append(row)

        # ------------------------------------------------------------------ #
        #  3. Build CP-SAT model
        # ------------------------------------------------------------------ #
        from ortools.sat.python import cp_model as cp

        model = cp.CpModel()

        variables = ORToolsVariableBuilder.build(
            model,
            n_vehicles=n_vehicles,
            n_employees=n_employees,
            n_parcels=n_parcels,
        )

        # ------------------------------------------------------------------ #
        #  4. Hard constraints
        # ------------------------------------------------------------------ #
        model.add_exactly_one(variables.vehicle_selected)
        model.add_exactly_one(variables.employee_selected)

        # Vehicle availability, branch co-location, capacity constraints
        for i, veh in enumerate(vehicles):
            ok = (
                is_vehicle_available(veh)
                and get_vehicle_capacity(veh) >= total_weight
                and (
                    route_start_branch_id is None
                    or get_vehicle_branch(veh) == route_start_branch_id
                )
            )
            if not ok:
                model.add(variables.vehicle_selected[i] == 0)

        # Employee availability, workload constraints
        for i, emp in enumerate(employees):
            ok = is_employee_available(emp) and is_employee_workload_ok(emp, n_parcels)
            if not ok:
                model.add(variables.employee_selected[i] == 0)

        # Parcel sequencing
        model.add_all_different(variables.parcel_positions)

        # ------------------------------------------------------------------ #
        #  5. Objective Function (Hybrid vs Normal)
        # ------------------------------------------------------------------ #
        sw = ScaledWeights(weights_copy)

        # Headroom components
        veh_headroom = model.new_int_var(0, SCALE, "veh_headroom")
        model.add(
            veh_headroom == cp.LinearExpr.weighted_sum(
                variables.vehicle_selected,
                scores.vehicle_scores,
            )
        )

        emp_headroom = model.new_int_var(-SCALE, SCALE, "emp_headroom")
        model.add(
            emp_headroom == cp.LinearExpr.weighted_sum(
                variables.employee_selected,
                scores.employee_scores,
            )
        )

        if use_hybrid:
            # Linearization variables for vehicle-employee pairs
            pair_sel = {}
            for i in range(n_vehicles):
                for j in range(n_employees):
                    pair_sel[i, j] = model.new_bool_var(f"pair_{i}_{j}")
                    model.add(pair_sel[i, j] <= variables.vehicle_selected[i])
                    model.add(pair_sel[i, j] <= variables.employee_selected[j])
                    model.add(pair_sel[i, j] >= variables.vehicle_selected[i] + variables.employee_selected[j] - 1)

            # Delay risk score component
            delay_risk_val = model.new_int_var(0, SCALE, "delay_risk_val")
            model.add(
                delay_risk_val == sum(
                    pair_sel[i, j] * delay_scores[i][j]
                    for i in range(n_vehicles)
                    for j in range(n_employees)
                )
            )

            # Cost score component
            cost_score_val = model.new_int_var(0, 100 * SCALE, "cost_score_val")
            model.add(
                cost_score_val == cp.LinearExpr.weighted_sum(
                    variables.vehicle_selected,
                    vehicle_cost_scores,
                )
            )

            # Maximise hybrid objective:
            # 80% goes to standard weighted headroom/priority/duration,
            # 20% goes to delay risk score.
            # We scale the delay term by weights_sum to match scale of headroom components.
            weights_sum = (
                sw.vehicle_capacity
                + sw.employee_workload
                + sw.parcel_priority
                + sw.distance
            )
            model.maximize(
                8 * (
                    sw.vehicle_capacity * veh_headroom
                    + sw.employee_workload * emp_headroom
                    + sw.parcel_priority * scores.priority_score_scaled
                    + sw.distance * cost_score_val
                    - sw.duration * scores.dur_cost_scaled
                )
                + 2 * weights_sum * delay_risk_val
            )
        else:
            # Standard Phase 2 objective
            model.maximize(
                sw.vehicle_capacity * veh_headroom
                + sw.employee_workload * emp_headroom
                + sw.parcel_priority * scores.priority_score_scaled
                - sw.distance * scores.dist_cost_scaled
                - sw.duration * scores.dur_cost_scaled
            )

        # ------------------------------------------------------------------ #
        #  6. Solve
        # ------------------------------------------------------------------ #
        solver_wrapper = ORToolsSolver(
            max_time_seconds=max_time_seconds,
            num_workers=1,
            log_search=False,
        )
        result = solver_wrapper.solve(model)

        # ------------------------------------------------------------------ #
        #  7. Extract Results
        # ------------------------------------------------------------------ #
        selected_veh_idx = next(
            i for i in range(n_vehicles)
            if result.solver.value(variables.vehicle_selected[i])
        )
        selected_emp_idx = next(
            i for i in range(n_employees)
            if result.solver.value(variables.employee_selected[i])
        )

        selected_vehicle = vehicles[selected_veh_idx]
        selected_employee = employees[selected_emp_idx]

        # Parcel sequencing
        parcel_positions_values = [
            result.solver.value(variables.parcel_positions[p])
            for p in range(n_parcels)
        ]
        optimized_sequence = build_optimized_sequence(
            parcels, parcel_positions_values
        )

        # Cost metrics
        metrics = compute_cost_metrics(distance_km)
        predicted_cost_val = actual_predicted_costs[selected_veh_idx]

        # Calculate delay risk score value
        sel_delay_prob = 1.0 - (delay_scores[selected_veh_idx][selected_emp_idx] / SCALE)

        # Normalise objective value → 0-100 optimization score
        max_possible = float(
            max(
                sw.vehicle_capacity
                + sw.employee_workload
                + sw.parcel_priority
                + sw.distance,
                1,
            )
            * SCALE
            * SCALE
        )
        optimization_score = round(
            min(max(result.objective_value / max(max_possible, 1) * 100, 0), 100), 2
        )

        return {
            "selected_vehicle_id":        selected_vehicle.vehicle_id,
            "selected_employee_id":        selected_employee.employee_id,
            "optimization_score":          optimization_score,
            "estimated_fuel_consumption":  metrics["fuel"],
            "estimated_cost":              round(predicted_cost_val, 2) if use_hybrid else metrics["cost"],
            "optimization_algorithm":      "OR-Tools CP-SAT (Hybrid)" if use_hybrid else "OR-Tools CP-SAT",
            "solver_status":               result.status_name,
            "optimized_sequence":          optimized_sequence,
            "total_parcels":               n_parcels,
            "score_breakdown": {
                "vehicle_capacity_headroom":  round(scores.vehicle_scores[selected_veh_idx] / SCALE, 4),
                "employee_workload_headroom": round(scores.employee_scores[selected_emp_idx] / SCALE, 4),
                "avg_parcel_priority_score":  round(scores.avg_priority_raw, 2),
                "distance_km":                distance_km,
                "duration_minutes":           duration_min,
                "total_weight_kg":            total_weight,
                "delay_probability":          round(sel_delay_prob, 4) if use_hybrid else None,
                "is_peak_day":                is_peak_day,
                "solver_status":              result.status_name,
                "objective_value":            result.objective_value,
            },
        }