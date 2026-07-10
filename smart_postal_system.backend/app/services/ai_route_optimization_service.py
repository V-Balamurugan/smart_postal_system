from sqlalchemy.orm import Session

from app.ai.optimizer import RouteOptimizer
from app.models.ai_route_optimization_model import AIRouteOptimization
from app.models.employee_model import Employee
from app.models.parcel_model import Parcel
from app.models.route_model import Route
from app.models.vehicle_model import Vehicle
from app.schemas.ai_route_optimization_schema import (
    AIRouteOptimizationRequest,
    AIRouteOptimizationResponse,
)


class AIRouteOptimizationService:
    """
    Service layer for AI Route Optimization.
    """

    @staticmethod
    def optimize_route(
        db: Session,
        route_id: int,
        request: AIRouteOptimizationRequest
    ) -> AIRouteOptimizationResponse:

        # ----------------------------------------------------
        # Load Route
        # ----------------------------------------------------
        route = (
            db.query(Route)
            .filter(Route.route_id == route_id)
            .first()
        )

        if route is None:
            raise ValueError("Route not found.")

        # ----------------------------------------------------
        # Load Parcels
        # ----------------------------------------------------
        start_branch = route.start_branch
        end_branch = route.end_branch
        if not start_branch or not end_branch:
            raise ValueError("Route branches not found.")

        parcels = (
            db.query(Parcel)
            .filter(
                (
                    (Parcel.source_branch == start_branch.branch_code)
                    | (Parcel.source_branch == start_branch.branch_name)
                )
                & (
                    (Parcel.destination_branch == end_branch.branch_code)
                    | (Parcel.destination_branch == end_branch.branch_name)
                )
            )
            .all()
        )

        if not parcels:
            raise ValueError(
                "No parcels assigned to this route."
            )

        # ----------------------------------------------------
        # Available Vehicles
        # ----------------------------------------------------
        vehicles = (
            db.query(Vehicle)
            .filter(Vehicle.status == "AVAILABLE")
            .all()
        )

        if not vehicles:
            raise ValueError(
                "No available vehicles."
            )

        # ----------------------------------------------------
        # Available Employees
        # ----------------------------------------------------
        employees = (
            db.query(Employee)
            .filter(Employee.is_available.is_(True))
            .all()
        )

        if not employees:
            raise ValueError(
                "No available employees."
            )

        # ----------------------------------------------------
        # Run AI Optimizer
        # ----------------------------------------------------
        result = RouteOptimizer.optimize(
            route=route,
            vehicles=vehicles,
            employees=employees,
            parcels=parcels,
            weights=request.weights.model_dump(),
            use_ortools=request.use_ortools,
            use_hybrid=request.use_hybrid,
        )

        # ----------------------------------------------------
        # Save Result
        # ----------------------------------------------------
        optimization = AIRouteOptimization(
            route_id=route.route_id,
            selected_vehicle_id=result["selected_vehicle_id"],
            selected_employee_id=result["selected_employee_id"],
            optimization_score=result["optimization_score"],
            estimated_fuel_consumption=result[
                "estimated_fuel_consumption"
            ],
            estimated_cost=result["estimated_cost"],
            total_parcels=result["total_parcels"],
            optimization_algorithm=result[
                "optimization_algorithm"
            ],
            optimized_sequence=result[
                "optimized_sequence"
            ],
            solver_status=result.get("solver_status"),
            score_breakdown=result.get("score_breakdown"),
        )

        db.add(optimization)
        db.commit()
        db.refresh(optimization)

        return AIRouteOptimizationResponse.model_validate(
            optimization
        )

    @staticmethod
    def get_optimization(
        db: Session,
        optimization_id: int
    ) -> AIRouteOptimizationResponse:

        optimization = (
            db.query(AIRouteOptimization)
            .filter(
                AIRouteOptimization.optimization_id
                == optimization_id
            )
            .first()
        )

        if optimization is None:
            raise ValueError(
                "Optimization not found."
            )

        return AIRouteOptimizationResponse.model_validate(
            optimization
        )

    @staticmethod
    def list_optimizations(
        db: Session
    ) -> list[AIRouteOptimizationResponse]:

        optimizations = (
            db.query(AIRouteOptimization)
            .order_by(
                AIRouteOptimization.created_at.desc()
            )
            .all()
        )

        return [
            AIRouteOptimizationResponse.model_validate(item)
            for item in optimizations
        ]