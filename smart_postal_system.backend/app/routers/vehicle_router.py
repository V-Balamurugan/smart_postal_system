from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user

from app.models.user_model import User

from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    AssignDriverSchema,
    VehicleStatusUpdate,
)

from app.services.vehicle_service import VehicleService

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicle Management"],
)


# ==========================================================
# Create Vehicle
# ADMIN
# ==========================================================
@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create vehicles."
        )

    return VehicleService.create_vehicle(db, vehicle)


# ==========================================================
# Get All Vehicles
# ADMIN / EMPLOYEE
# ==========================================================
@router.get(
    "/",
    response_model=List[VehicleResponse],
)
def get_all_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    return VehicleService.get_all_vehicles(db)


# ==========================================================
# Get Vehicle By ID
# ADMIN / EMPLOYEE
# ==========================================================
@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["ADMIN", "EMPLOYEE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    return VehicleService.get_vehicle_by_id(
        db,
        vehicle_id,
    )


# ==========================================================
# Update Vehicle
# ADMIN
# ==========================================================
@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update vehicles."
        )

    return VehicleService.update_vehicle(
        db,
        vehicle_id,
        vehicle,
    )


# ==========================================================
# Assign Driver
# ADMIN
# ==========================================================
@router.patch(
    "/{vehicle_id}/assign-driver",
    response_model=VehicleResponse,
)
def assign_driver(
    vehicle_id: int,
    request: AssignDriverSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can assign drivers."
        )

    return VehicleService.assign_driver(
        db,
        vehicle_id,
        request.driver_id,
    )


# ==========================================================
# Update Vehicle Status
# ADMIN
# ==========================================================
@router.patch(
    "/{vehicle_id}/status",
    response_model=VehicleResponse,
)
def update_vehicle_status(
    vehicle_id: int,
    request: VehicleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update vehicle status."
        )

    return VehicleService.update_vehicle_status(
        db,
        vehicle_id,
        request.status,
    )


# ==========================================================
# Delete Vehicle
# ADMIN
# ==========================================================
@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_200_OK,
)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete vehicles."
        )

    return VehicleService.delete_vehicle(
        db,
        vehicle_id,
    )