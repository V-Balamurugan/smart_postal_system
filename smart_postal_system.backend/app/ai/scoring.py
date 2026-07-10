from typing import Dict, List, Any


class OptimizationScoring:
    """
    Production-ready weighted scoring engine.

    Every score is normalized to 0-100.

    Higher score = Better optimization candidate.
    """

    DEFAULT_WEIGHTS = {
        "distance": 25,
        "duration": 20,
        "employee_workload": 20,
        "vehicle_capacity": 15,
        "parcel_priority": 20
    }

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    @staticmethod
    def _clamp(value: float) -> float:
        """
        Clamp value to range [0,100]
        """
        return max(0.0, min(100.0, value))

    # --------------------------------------------------
    # Distance
    # --------------------------------------------------

    @staticmethod
    def distance_score(distance_km: float) -> float:
        """
        Shorter distance -> Higher score

        0 km -> 100
        100 km -> 0
        """

        score = 100 - distance_km
        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Duration
    # --------------------------------------------------

    @staticmethod
    def duration_score(duration_minutes: float) -> float:
        """
        Shorter duration -> Higher score

        0 min -> 100
        120 min -> 0
        """

        score = 100 - (duration_minutes / 1.2)
        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Employee
    # --------------------------------------------------

    @staticmethod
    def employee_workload_score(employee) -> float:

        current = getattr(employee, "current_workload", 0)
        maximum = getattr(employee, "max_workload", 1)

        utilization = current / max(maximum, 1)

        score = 100 - (utilization * 100)

        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Vehicle
    # --------------------------------------------------

    @staticmethod
    def vehicle_capacity_score(
        vehicle,
        total_weight: float
    ) -> float:

        capacity = getattr(vehicle, "capacity_kg", getattr(vehicle, "capacity", 1))

        utilization = total_weight / max(capacity, 1)

        if utilization > 1:
            return 0

        score = 100 - (utilization * 100)

        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Parcel Priority
    # --------------------------------------------------

    @staticmethod
    def parcel_priority_score(
        parcels: List[Any]
    ) -> float:

        priority_map = {
            "HIGH": 100,
            "MEDIUM": 70,
            "NORMAL": 70,
            "LOW": 40
        }

        if not parcels:
            return 0

        total = 0

        for parcel in parcels:
            total += priority_map.get(
                getattr(parcel, "priority_level", getattr(parcel, "priority", "LOW")),
                40
            )

        return total / len(parcels)

    # --------------------------------------------------
    # Final Score
    # --------------------------------------------------

    @classmethod
    def calculate_score(
        cls,
        *,
        route,
        vehicle,
        employee,
        parcels: List[Any],
        total_weight: float,
        weights: Dict[str, float] | None = None
    ) -> Dict[str, Any]:
        """
        Calculate complete weighted optimization score.
        """

        weights = weights or cls.DEFAULT_WEIGHTS

        distance = cls.distance_score(
            getattr(route, "distance_km", getattr(route, "distance", 0))
        )

        duration = cls.duration_score(
            getattr(route, "estimated_duration_minutes", getattr(route, "estimated_duration", 0))
        )

        employee_score = cls.employee_workload_score(
            employee
        )

        vehicle_score = cls.vehicle_capacity_score(
            vehicle,
            total_weight
        )

        priority_score = cls.parcel_priority_score(
            parcels
        )

        final_score = (
            distance * weights["distance"] +
            duration * weights["duration"] +
            employee_score * weights["employee_workload"] +
            vehicle_score * weights["vehicle_capacity"] +
            priority_score * weights["parcel_priority"]
        ) / 100

        return {
            "distance_score": round(distance, 2),
            "duration_score": round(duration, 2),
            "employee_score": round(employee_score, 2),
            "vehicle_score": round(vehicle_score, 2),
            "priority_score": round(priority_score, 2),
            "final_score": round(final_score, 2)
        }