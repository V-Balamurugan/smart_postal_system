import logging
from typing import Any, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.route_model import Route
from app.models.branch_model import Branch
from app.schemas.route_optimization_schema import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
)
from utils.ors_client import ors_client

logger = logging.getLogger(__name__)


class RouteOptimizationService:

    @staticmethod
    async def optimize_route(
        db: Session,
        request: RouteOptimizationRequest,
    ) -> Dict[str, Any]:
        """
        Optimize route distance and duration using OpenRouteService API.
        """
        # Fetch the route
        route = db.query(Route).filter(Route.route_id == request.route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route with ID {request.route_id} not found."
            )

        # Fetch start and end branch coordinates
        start_branch = db.query(Branch).filter(Branch.branch_id == route.start_branch_id).first()
        if not start_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Start branch with ID {route.start_branch_id} not found."
            )

        end_branch = db.query(Branch).filter(Branch.branch_id == route.end_branch_id).first()
        if not end_branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"End branch with ID {route.end_branch_id} not found."
            )

        # Call OpenRouteService API
        try:
            logger.info(
                f"Calling ORS to optimize route {route.route_name} "
                f"from ({start_branch.longitude}, {start_branch.latitude}) "
                f"to ({end_branch.longitude}, {end_branch.latitude})"
            )
            
            ors_response = await ors_client.get_driving_route(
                start_longitude=start_branch.longitude,
                start_latitude=start_branch.latitude,
                end_longitude=end_branch.longitude,
                end_latitude=end_branch.latitude
            )

            routes = ors_response.get("routes", [])
            if not routes:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No routing path returned by OpenRouteService."
                )

            summary = routes[0].get("summary", {})
            distance_meters = summary.get("distance", 0.0)
            duration_seconds = summary.get("duration", 0)
            geometry = routes[0].get("geometry", "")

            # Convert to required units
            distance_km = round(distance_meters / 1000.0, 2)
            estimated_duration_minutes = int(round(duration_seconds / 60.0))

            # Update route attributes in the database
            route.distance_km = distance_km
            route.estimated_duration_minutes = estimated_duration_minutes
            
            db.commit()
            db.refresh(route)

            optimization_status = "SUCCESS"

        except HTTPException as he:
            # Let FastAPI HTTPException bubble up
            raise he
        except Exception as exc:
            logger.exception("Unexpected error during route optimization.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected optimization error: {str(exc)}"
            )

        return {
            "route_id": route.route_id,
            "route_name": route.route_name,
            "start_branch_id": route.start_branch_id,
            "end_branch_id": route.end_branch_id,
            "distance_km": route.distance_km,
            "estimated_duration_minutes": route.estimated_duration_minutes,
            "route_geometry": geometry,
            "optimization_status": optimization_status,
        }
