from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.ai_route_optimization_schema import (
    AIRouteOptimizationRequest,
    AIRouteOptimizationResponse,
)

from app.services.ai_route_optimization_service import (
    AIRouteOptimizationService,
)

# --------------------------------------------------------------------
# Replace these imports with your existing authentication dependencies
# --------------------------------------------------------------------
from app.core.security import get_current_user
from app.models.user_model import User

router = APIRouter(
    prefix="/ai-route-optimization",
    tags=["AI Route Optimization"]
)


@router.post(
    "/optimize/{route_id}",
    response_model=AIRouteOptimizationResponse,
    status_code=status.HTTP_201_CREATED
)
def optimize_route(
    route_id: int,
    request: AIRouteOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimize a delivery route using the AI optimization engine.
    """

    try:
        return AIRouteOptimizationService.optimize_route(
            db=db,
            route_id=route_id,
            request=request
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get(
    "/{optimization_id}",
    response_model=AIRouteOptimizationResponse
)
def get_optimization(
    optimization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get an optimization by ID.
    """

    try:
        return AIRouteOptimizationService.get_optimization(
            db=db,
            optimization_id=optimization_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.get(
    "/",
    response_model=list[AIRouteOptimizationResponse]
)
def list_optimizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all optimization records.
    """

    return AIRouteOptimizationService.list_optimizations(
        db=db
    )