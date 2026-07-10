from typing import Dict, Any, List

from app.ai.constrains import OptimizationConstraints
from app.ai.scoring import OptimizationScoring


class RouteOptimizer:
    """
    Main AI Route Optimization Engine.
    """

    FUEL_CONSUMPTION_PER_KM = 0.12      # Liters/km
    COST_PER_KM = 12.5                  # Currency/km

    @classmethod
    def optimize(
        cls,
        *,
        route,
        vehicles: List,
        employees: List,
        parcels: List,
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Returns the best optimization plan.
        """

        if not vehicles:
            raise ValueError("No vehicles available.")

        if not employees:
            raise ValueError("No employees available.")

        if not parcels:
            raise ValueError("No parcels assigned to the route.")

        total_weight = OptimizationConstraints.validate_parcel_weights(
            parcels
        )

        prioritized_parcels = (
            OptimizationConstraints.validate_priority_parcels(
                parcels
            )
        )

        best_candidate = None
        best_score = -1

        for vehicle in vehicles:

            for employee in employees:

                report = (
                    OptimizationConstraints.build_constraint_report(
                        vehicle,
                        employee,
                        route,
                        parcels
                    )
                )

                if not report["all_constraints_passed"]:
                    continue

                score = OptimizationScoring.calculate_score(
                    route=route,
                    vehicle=vehicle,
                    employee=employee,
                    parcels=parcels,
                    total_weight=total_weight,
                    weights=weights
                )

                if score["final_score"] > best_score:

                    best_score = score["final_score"]

                    best_candidate = {
                        "vehicle": vehicle,
                        "employee": employee,
                        "score": score
                    }

        if best_candidate is None:
            raise ValueError(
                "No valid optimization candidate found."
            )

        optimized_sequence = [
            {
                "parcel_id": parcel.parcel_id,
                "priority": getattr(parcel, "priority_level", getattr(parcel, "priority", "LOW")),
                "destination": getattr(
                    parcel,
                    "delivery_address",
                    getattr(parcel, "destination_address", None)
                )
            }
            for parcel in prioritized_parcels
        ]

        distance = getattr(route, "distance_km", getattr(route, "distance", 0))

        fuel = round(
            distance * cls.FUEL_CONSUMPTION_PER_KM,
            2
        )

        cost = round(
            distance * cls.COST_PER_KM,
            2
        )

        return {

            "selected_vehicle_id":
                best_candidate["vehicle"].vehicle_id,

            "selected_employee_id":
                best_candidate["employee"].employee_id,

            "optimization_score":
                best_candidate["score"]["final_score"],

            "estimated_fuel_consumption":
                fuel,

            "estimated_cost":
                cost,

            "optimization_algorithm":
                "Rule-Based",

            "optimized_sequence":
                optimized_sequence,

            "total_parcels":
                len(parcels),

            "score_breakdown":
                best_candidate["score"]
        }