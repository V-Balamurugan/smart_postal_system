from typing import Dict, List, Any, Optional

class OptimizationScoring:
    """
    Production-ready weighted scoring engine.
    Supports hybrid mode incorporating ML predictions (delay risk and peak workload priority).

    Every score is normalized to 0-100.
    Higher score = Better optimization candidate.
    """

    DEFAULT_WEIGHTS = {
        "distance": 25.0,
        "duration": 20.0,
        "employee_workload": 20.0,
        "vehicle_capacity": 15.0,
        "parcel_priority": 20.0
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
        score = 100.0 - distance_km
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
        score = 100.0 - (duration_minutes / 1.2)
        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Employee
    # --------------------------------------------------

    @staticmethod
    def employee_workload_score(employee) -> float:
        current = getattr(employee, "current_workload", 0)
        maximum = getattr(employee, "max_workload", 1)

        utilization = current / max(maximum, 1)
        score = 100.0 - (utilization * 100.0)

        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Vehicle
    # --------------------------------------------------

    @staticmethod
    def vehicle_capacity_score(
        vehicle,
        total_weight: float
    ) -> float:
        capacity = getattr(vehicle, "capacity_kg", getattr(vehicle, "capacity", 1.0))
        utilization = total_weight / max(capacity, 1.0)

        if utilization > 1.0:
            return 0.0

        score = 100.0 - (utilization * 100.0)
        return OptimizationScoring._clamp(score)

    # --------------------------------------------------
    # Parcel Priority
    # --------------------------------------------------

    @staticmethod
    def parcel_priority_score(
        parcels: List[Any]
    ) -> float:
        priority_map = {
            "HIGH": 100.0,
            "MEDIUM": 70.0,
            "NORMAL": 70.0,
            "LOW": 40.0
        }

        if not parcels:
            return 0.0

        total = 0.0
        for parcel in parcels:
            total += priority_map.get(
                getattr(parcel, "priority_level", getattr(parcel, "priority", "LOW")),
                40.0
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
        weights: Optional[Dict[str, float]] = None,
        use_hybrid: bool = False,
        delay_risk_score: float = 100.0,
        is_peak_day: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate complete weighted optimization score.
        """
        raw_weights = (weights or cls.DEFAULT_WEIGHTS).copy()

        # Dynamic weighting based on demand forecast:
        # Boost employee workload weight during peak days
        if use_hybrid and is_peak_day:
            original_workload = raw_weights.get("employee_workload", 20.0)
            boost = 15.0
            raw_weights["employee_workload"] = original_workload + boost
            
            # Decrease other weights proportionally so they still sum to 100
            other_keys = [k for k in raw_weights.keys() if k != "employee_workload"]
            total_others = sum(raw_weights[k] for k in other_keys)
            if total_others > 0:
                for k in other_keys:
                    raw_weights[k] -= (raw_weights[k] / total_others) * boost

        distance = cls.distance_score(
            getattr(route, "distance_km", getattr(route, "distance", 0.0))
        )

        duration = cls.duration_score(
            getattr(route, "estimated_duration_minutes", getattr(route, "estimated_duration", 0.0))
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

        if use_hybrid:
            # Under hybrid mode:
            # 20% weight goes to ML Delay Risk, 80% goes to normal optimization criteria
            base_score = (
                distance * raw_weights.get("distance", 25.0) +
                duration * raw_weights.get("duration", 20.0) +
                employee_score * raw_weights.get("employee_workload", 20.0) +
                vehicle_score * raw_weights.get("vehicle_capacity", 15.0) +
                priority_score * raw_weights.get("parcel_priority", 20.0)
            ) / 100.0
            
            final_score = base_score * 0.8 + delay_risk_score * 0.2
        else:
            final_score = (
                distance * raw_weights.get("distance", 25.0) +
                duration * raw_weights.get("duration", 20.0) +
                employee_score * raw_weights.get("employee_workload", 20.0) +
                vehicle_score * raw_weights.get("vehicle_capacity", 15.0) +
                priority_score * raw_weights.get("parcel_priority", 20.0)
            ) / 100.0

        return {
            "distance_score": round(distance, 2),
            "duration_score": round(duration, 2),
            "employee_score": round(employee_score, 2),
            "vehicle_score": round(vehicle_score, 2),
            "priority_score": round(priority_score, 2),
            "delay_risk_score": round(delay_risk_score, 2) if use_hybrid else None,
            "final_score": round(final_score, 2),
            "is_peak_day": is_peak_day,
            "applied_weights": {k: round(v, 2) for k, v in raw_weights.items()}
        }