from typing import Dict, List, Any


class OptimizationConstraints:
    """
    Business constraints used by the AI optimization engine.

    This class only validates constraints.
    It does NOT perform optimization.
    """

    @staticmethod
    def validate_vehicle_availability(vehicle) -> bool:
        """
        Check whether the vehicle is available.
        """
        status = getattr(vehicle, "status", None)
        if status is not None:
            return status == "AVAILABLE" or getattr(status, "value", None) == "AVAILABLE"
        return bool(getattr(vehicle, "is_available", False))

    @staticmethod
    def validate_vehicle_capacity(vehicle, total_weight: float) -> bool:
        """
        Ensure the vehicle can carry the total parcel weight.
        """
        capacity = getattr(vehicle, "capacity_kg", getattr(vehicle, "capacity", 0))
        return total_weight <= capacity

    @staticmethod
    def validate_vehicle_branch(vehicle, route) -> bool:
        """
        Ensure the vehicle belongs to the same branch as the route.
        """
        vehicle_branch = getattr(vehicle, "current_branch_id", getattr(vehicle, "branch_id", None))
        route_branch = getattr(route, "start_branch_id", getattr(route, "branch_id", None))
        return vehicle_branch is not None and vehicle_branch == route_branch

    @staticmethod
    def validate_employee_availability(employee) -> bool:
        """
        Check whether the employee is available.
        """
        return bool(getattr(employee, "is_available", False))

    @staticmethod
    def validate_employee_workload(
        employee,
        additional_parcels: int
    ) -> bool:
        """
        Ensure assigning new parcels does not exceed
        the employee's maximum workload.
        """

        current = getattr(employee, "current_workload", 0)
        maximum = getattr(employee, "max_workload", 0)

        return (current + additional_parcels) <= maximum

    @staticmethod
    def validate_employee_branch(employee, route) -> bool:
        """
        Employee should belong to the same branch.
        """
        employee_branch = getattr(employee, "branch", None)
        start_branch = getattr(route, "start_branch", None)
        if employee_branch is not None and start_branch is not None:
            if employee_branch in (start_branch.branch_code, start_branch.branch_name):
                return True

        emp_branch_id = getattr(employee, "branch_id", None)
        route_branch_id = getattr(route, "start_branch_id", getattr(route, "branch_id", None))
        return emp_branch_id is not None and emp_branch_id == route_branch_id

    @staticmethod
    def validate_route(route) -> bool:
        """
        Basic route validation.
        """
        distance = getattr(route, "distance_km", getattr(route, "distance", 0))
        duration = getattr(route, "estimated_duration_minutes", getattr(route, "estimated_duration", 0))
        return (
            distance > 0 and
            duration > 0
        )

    @staticmethod
    def validate_parcel_weights(parcels: List[Any]) -> float:
        """
        Calculate total parcel weight.
        """

        return sum(
            getattr(parcel, "weight", 0)
            for parcel in parcels
        )

    @staticmethod
    def validate_priority_parcels(parcels: List[Any]) -> List[Any]:
        """
        Return parcels sorted by priority and deadline.

        Expected priority values:
            HIGH
            MEDIUM
            NORMAL
            LOW
        """
        from datetime import datetime, timezone

        priority_order = {
            "HIGH": 3,
            "MEDIUM": 2,
            "NORMAL": 2,
            "LOW": 1
        }

        def get_sort_key(parcel):
            prio = getattr(parcel, "priority_level", getattr(parcel, "priority", "LOW"))
            prio_val = priority_order.get(prio, 0)
            
            deadline = getattr(parcel, "expected_delivery", getattr(parcel, "delivery_deadline", None))
            if deadline is None:
                # Use a far future date matching the timezone awareness of deadline if possible
                deadline = datetime.max.replace(tzinfo=timezone.utc)
            else:
                # If deadline has timezone info, ensure a standard timezone comparison or fallback
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
            return (-prio_val, deadline)

        return sorted(parcels, key=get_sort_key)

    @staticmethod
    def validate_weights(weights: Dict[str, float]) -> bool:
        """
        Ensure optimization weights are valid.

        Total must equal 100.
        """

        total = sum(weights.values())

        return abs(total - 100.0) < 0.001

    @staticmethod
    def build_constraint_report(
        vehicle,
        employee,
        route,
        parcels
    ) -> Dict[str, Any]:
        """
        Returns a complete validation report
        for debugging and logging.
        """

        total_weight = OptimizationConstraints.validate_parcel_weights(
            parcels
        )

        report = {
            "vehicle_available":
                OptimizationConstraints.validate_vehicle_availability(vehicle),

            "vehicle_capacity":
                OptimizationConstraints.validate_vehicle_capacity(
                    vehicle,
                    total_weight
                ),

            "vehicle_branch":
                OptimizationConstraints.validate_vehicle_branch(
                    vehicle,
                    route
                ),

            "employee_available":
                OptimizationConstraints.validate_employee_availability(
                    employee
                ),

            "employee_workload":
                OptimizationConstraints.validate_employee_workload(
                    employee,
                    len(parcels)
                ),

            "employee_branch":
                OptimizationConstraints.validate_employee_branch(
                    employee,
                    route
                ),

            "route_valid":
                OptimizationConstraints.validate_route(route),

            "total_weight":
                total_weight,

            "parcel_count":
                len(parcels)
        }

        report["all_constraints_passed"] = all([
            report["vehicle_available"],
            report["vehicle_capacity"],
            report["vehicle_branch"],
            report["employee_available"],
            report["employee_workload"],
            report["employee_branch"],
            report["route_valid"]
        ])

        return report