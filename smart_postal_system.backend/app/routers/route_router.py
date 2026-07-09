from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user, role_required

from app.models.user_model import User
from app.schemas.route_schema import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
)
from app.services.route_service import RouteService

router = APIRouter(
    prefix="/routes",
    tags=["Route Management"],
)


# ==========================================================
# Create Route
# ADMIN
# ==========================================================
@router.post(
    "/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"])),
):
    return RouteService.create_route(db, route)


# ==========================================================
# Get All Routes
# ADMIN / EMPLOYEE
# ==========================================================
@router.get(
    "/",
    response_model=List[RouteResponse],
)
def get_all_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"])),
):
    return RouteService.get_all_routes(db)


# ==========================================================
# Get Route By ID
# ADMIN / EMPLOYEE
# ==========================================================
@router.get(
    "/{route_id}",
    response_model=RouteResponse,
)
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"])),
):
    return RouteService.get_route_by_id(db, route_id)


# ==========================================================
# Update Route
# ADMIN
# ==========================================================
@router.put(
    "/{route_id}",
    response_model=RouteResponse,
)
def update_route(
    route_id: int,
    route: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"])),
):
    return RouteService.update_route(db, route_id, route)


# ==========================================================
# Activate Route
# ADMIN
# ==========================================================
@router.patch(
    "/{route_id}/activate",
    response_model=RouteResponse,
)
def activate_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"])),
):
    return RouteService.activate_route(db, route_id)


# ==========================================================
# Deactivate Route
# ADMIN
# ==========================================================
@router.patch(
    "/{route_id}/deactivate",
    response_model=RouteResponse,
)
def deactivate_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"])),
):
    return RouteService.deactivate_route(db, route_id)


# ==========================================================
# Delete Route
# ADMIN
# ==========================================================
@router.delete(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
)
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"])),
):
    return RouteService.delete_route(db, route_id)
