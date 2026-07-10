import logging
from typing import Dict, Any, List

from app.ai.constrains import OptimizationConstraints
from app.ai.scoring import OptimizationScoring

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """
    Main AI Route Optimization Engine.

    Dispatch strategy
    -----------------
    1. If ``use_ortools=True`` (default), attempt the OR-Tools CP-SAT solver
       (Phase 2).  Falls back to Rule-Based automatically if:
         - ``ortools`` package is not installed (ImportError)
         - solver returns INFEASIBLE / UNKNOWN (ValueError)
    2. If ``use_ortools=False``, run the Rule-Based greedy scorer directly
       (Phase 1).
    """

    FUEL_CONSUMPTION_PER_KM = 0.12      # Liters/km
    COST_PER_KM = 12.5                  # Currency/km

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    @classmethod
    def optimize(
        cls,
        *,
        route,
        vehicles: List,
        employees: List,
        parcels: List,
        weights: Dict[str, float],
        use_ortools: bool = True,
    ) -> Dict[str, Any]:
        """
        Returns the best optimization plan dict.

        Parameters
        ----------
        route       : SQLAlchemy Route ORM object
        vehicles    : list of Vehicle ORM objects (pre-filtered to AVAILABLE)
        employees   : list of Employee ORM objects (pre-filtered to available)
        parcels     : list of Parcel ORM objects assigned to the route
        weights     : scoring weight dict (keys: distance, duration,
                      employee_workload, vehicle_capacity, parcel_priority)
        use_ortools : if True, attempt CP-SAT solver first; fall back to
                      rule-based on failure
        """
        if not vehicles:
            raise ValueError("No vehicles available.")
        if not employees:
            raise ValueError("No employees available.")
        if not parcels:
            raise ValueError("No parcels assigned to the route.")

        if use_ortools:
            result = cls._try_ortools(route, vehicles, employees, parcels, weights)
            if result is not None:
                return result
            # Fell through — use rule-based
            logger.warning(
                "OR-Tools CP-SAT unavailable or infeasible; "
                "falling back to Rule-Based optimizer."
            )

        return cls._rule_based(route, vehicles, employees, parcels, weights)

    # ---------------------------------------------------------------------- #
    # OR-Tools path
    # ---------------------------------------------------------------------- #

    @classmethod
    def _try_ortools(
        cls,
        route,
        vehicles: List,
        employees: List,
        parcels: List,
        weights: Dict[str, float],
    ) -> Dict[str, Any] | None:
        """
        Attempt the OR-Tools CP-SAT optimizer.
        Returns result dict on success, or None to signal fallback.
        """
        try:
            from app.ai.ortools_optimizer import ORToolsOptimizer
            return ORToolsOptimizer.optimize(
                route=route,
                vehicles=vehicles,
                employees=employees,
                parcels=parcels,
                weights=weights,
            )
        except ImportError:
            logger.warning("ortools package not installed; falling back to Rule-Based.")
            return None
        except ValueError as exc:
            logger.warning("OR-Tools returned no feasible solution: %s", exc)
            return None
        except Exception as exc:                          # noqa: BLE001
            logger.exception("Unexpected OR-Tools error: %s", exc)
            return None

    # ---------------------------------------------------------------------- #
    # Rule-Based (Phase 1) path
    # ---------------------------------------------------------------------- #

    @classmethod
    def _rule_based(
        cls,
        route,
        vehicles: List,
        employees: List,
        parcels: List,
        weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Brute-force Phase-1 rule-based optimizer.
        Iterates all (vehicle, employee) pairs, scores them, picks the best.
        """

        total_weight = OptimizationConstraints.validate_parcel_weights(parcels)
        prioritized_parcels = OptimizationConstraints.validate_priority_parcels(parcels)

        best_candidate = None
        best_score = -1.0

        for vehicle in vehicles:
            for employee in employees:

                report = OptimizationConstraints.build_constraint_report(
                    vehicle, employee, route, parcels
                )

                if not report["all_constraints_passed"]:
                    continue

                score = OptimizationScoring.calculate_score(
                    route=route,
                    vehicle=vehicle,
                    employee=employee,
                    parcels=parcels,
                    total_weight=total_weight,
                    weights=weights,
                )

                if score["final_score"] > best_score:
                    best_score = score["final_score"]
                    best_candidate = {
                        "vehicle":  vehicle,
                        "employee": employee,
                        "score":    score,
                    }

        if best_candidate is None:
            raise ValueError("No valid optimization candidate found.")

        optimized_sequence = [
            {
                "position":    idx,
                "parcel_id":   parcel.parcel_id,
                "priority":    getattr(parcel, "priority_level",
                                       getattr(parcel, "priority", "LOW")),
                "destination": getattr(
                    parcel,
                    "delivery_address",
                    getattr(parcel, "destination_address", None),
                ),
                "weight_kg":   getattr(parcel, "weight", 0.0),
            }
            for idx, parcel in enumerate(prioritized_parcels)
        ]

        distance = getattr(route, "distance_km", getattr(route, "distance", 0.0))
        fuel = round(distance * cls.FUEL_CONSUMPTION_PER_KM, 2)
        cost = round(distance * cls.COST_PER_KM, 2)

        return {
            "selected_vehicle_id":       best_candidate["vehicle"].vehicle_id,
            "selected_employee_id":      best_candidate["employee"].employee_id,
            "optimization_score":        best_candidate["score"]["final_score"],
            "estimated_fuel_consumption": fuel,
            "estimated_cost":            cost,
            "optimization_algorithm":    "Rule-Based",
            "solver_status":             "RULE_BASED",
            "optimized_sequence":        optimized_sequence,
            "total_parcels":             len(parcels),
            "score_breakdown":           best_candidate["score"],
        }