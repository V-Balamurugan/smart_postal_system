from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user, role_required
from app.models.user_model import User
from app.schemas.route_optimization_schema import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
)
from app.services.route_optimization_service import RouteOptimizationService

router = APIRouter(
    prefix="/routes",
    tags=["Route Management"],
)


# ==========================================================
# Optimize Route
# ADMIN / EMPLOYEE
# ==========================================================
@router.post(
    "/optimize",
    response_model=RouteOptimizationResponse,
    status_code=status.HTTP_200_OK,
)
async def optimize_route(
    request: RouteOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"])),
):
    """
    Optimize an existing route using OpenRouteService API.
    Updates the route distance and duration based on driving directions.
    """
    return await RouteOptimizationService.optimize_route(db, request)
