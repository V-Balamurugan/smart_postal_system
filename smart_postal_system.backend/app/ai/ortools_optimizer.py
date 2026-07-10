"""
Phase 2: Google OR-Tools CP-SAT Combinatorial Optimizer
========================================================

Uses the CP-SAT (Constraint Programming - Satisfiability) solver to find
the globally optimal assignment of vehicles and employees for a delivery
route, and to sequence parcels by minimising total weighted delivery urgency.

Architecture
------------
This module now acts as a clean **orchestrator**:

1. Validate inputs
2. Pre-compute scores via :class:`~app.ai.objective.PrecomputedScores`
3. Build decision variables via :class:`~app.ai.variable.ORToolsVariableBuilder`
4. Add hard constraints (inline — simple and readable)
5. Build objective via :class:`~app.ai.objective.ORToolsObjectiveBuilder`
6. Solve via :class:`~app.ai.solver.ORToolsSolver`
7. Extract and return results

Decision Variables
------------------
- ``vehicle_selected[v]``  : BoolVar — is vehicle *v* selected?
- ``employee_selected[e]`` : BoolVar — is employee *e* selected?
- ``parcel_pos[p]``        : IntVar  — delivery-sequence position of parcel *p*

Hard Constraints
----------------
1. Exactly one vehicle is selected.
2. Exactly one employee is selected.
3. Selected vehicle must be AVAILABLE, at the route start branch,
   and have sufficient capacity for the total parcel weight.
4. Selected employee must be available and within workload limits.
5. Parcel positions are AllDifferent.

Objective (Maximise, integer-scaled by SCALE=1000)
---------------------------------------------------
  + vehicle_capacity_headroom  × w_vehicle_capacity
  + employee_workload_headroom × w_employee_workload
  + avg_parcel_priority_score  × w_parcel_priority
  − distance_cost_score        × w_distance
  − duration_cost_score        × w_duration

Fallback
--------
Raises ``ValueError`` (INFEASIBLE / UNKNOWN) or ``ImportError`` (missing
``ortools`` package) so the caller can fall back to the Rule-Based engine.
"""

from __future__ import annotations

import logging
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
from app.ai.objective import ORToolsObjectiveBuilder, PrecomputedScores
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
    ) -> Dict[str, Any]:
        """
        Run the CP-SAT solver and return the optimized assignment result dict.

        Parameters
        ----------
        route            : SQLAlchemy Route ORM object
        vehicles         : list of Vehicle ORM objects (pre-filtered)
        employees        : list of Employee ORM objects (pre-filtered)
        parcels          : list of Parcel ORM objects assigned to the route
        weights          : scoring weight dict (keys: distance, duration,
                           employee_workload, vehicle_capacity, parcel_priority)
        max_time_seconds : solver wall-clock time limit

        Raises
        ------
        ImportError
            If the ``ortools`` package is not installed.
        ValueError
            If no feasible solution is found (caller should fall back).
        """

        # Lazy import — raises ImportError if ortools is not installed
        from ortools.sat.python import cp_model  # noqa: F401  (validates install)

        n_vehicles = len(vehicles)
        n_employees = len(employees)
        n_parcels = len(parcels)

        if n_vehicles == 0 or n_employees == 0 or n_parcels == 0:
            raise ValueError("Insufficient data for OR-Tools optimizer.")

        # ------------------------------------------------------------------ #
        #  1. Pre-compute scores & derived data
        # ------------------------------------------------------------------ #
        scores = PrecomputedScores.from_inputs(
            vehicles=vehicles,
            employees=employees,
            parcels=parcels,
            route=route,
        )

        total_weight = compute_total_weight(parcels)
        route_start_branch_id = get_route_start_branch_id(route)
        distance_km = get_route_distance(route)
        duration_min = get_route_duration(route)

        # ------------------------------------------------------------------ #
        #  2. Build CP-SAT model
        # ------------------------------------------------------------------ #
        from ortools.sat.python import cp_model as cp

        model = cp.CpModel()

        # ------------------------------------------------------------------ #
        #  3. Decision variables
        # ------------------------------------------------------------------ #
        variables = ORToolsVariableBuilder.build(
            model,
            n_vehicles=n_vehicles,
            n_employees=n_employees,
            n_parcels=n_parcels,
        )

        # ------------------------------------------------------------------ #
        #  4. Hard constraints
        # ------------------------------------------------------------------ #

        # C1 — Exactly one vehicle selected
        model.add_exactly_one(variables.vehicle_selected)

        # C2 — Exactly one employee selected
        model.add_exactly_one(variables.employee_selected)

        # C3 — Vehicle feasibility: AVAILABLE + correct branch + capacity
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

        # C4 — Employee feasibility: available + within workload cap
        for i, emp in enumerate(employees):
            ok = is_employee_available(emp) and is_employee_workload_ok(emp, n_parcels)
            if not ok:
                model.add(variables.employee_selected[i] == 0)

        # C5 — Parcel positions are all distinct
        model.add_all_different(variables.parcel_positions)

        # ------------------------------------------------------------------ #
        #  5. Objective
        # ------------------------------------------------------------------ #
        scaled_weights = ORToolsObjectiveBuilder.build(
            model, variables, scores, weights
        )

        # ------------------------------------------------------------------ #
        #  6. Solve
        # ------------------------------------------------------------------ #
        solver_wrapper = ORToolsSolver(
            max_time_seconds=max_time_seconds,
            num_workers=1,
            log_search=False,
        )
        result = solver_wrapper.solve(model)   # raises ValueError if infeasible

        # ------------------------------------------------------------------ #
        #  7. Extract results
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

        # Build the sequence using the CP-SAT-assigned positions
        parcel_positions_values = [
            result.solver.value(variables.parcel_positions[p])
            for p in range(n_parcels)
        ]
        optimized_sequence = build_optimized_sequence(
            parcels, parcel_positions_values
        )

        # Cost metrics
        metrics = compute_cost_metrics(distance_km)

        # Normalise objective value → 0-100 optimization score
        max_possible = float(
            max(
                scaled_weights.vehicle_capacity
                + scaled_weights.employee_workload
                + scaled_weights.parcel_priority,
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
            "estimated_cost":              metrics["cost"],
            "optimization_algorithm":      "OR-Tools CP-SAT",
            "solver_status":               result.status_name,
            "optimized_sequence":          optimized_sequence,
            "total_parcels":               n_parcels,
            "score_breakdown": {
                "vehicle_capacity_headroom":  round(
                    scores.vehicle_scores[selected_veh_idx] / SCALE, 4
                ),
                "employee_workload_headroom": round(
                    scores.employee_scores[selected_emp_idx] / SCALE, 4
                ),
                "avg_parcel_priority_score":  round(scores.avg_priority_raw, 2),
                "distance_km":                distance_km,
                "duration_minutes":           duration_min,
                "total_weight_kg":            total_weight,
                "solver_status":              result.status_name,
                "objective_value":            result.objective_value,
            },
        }