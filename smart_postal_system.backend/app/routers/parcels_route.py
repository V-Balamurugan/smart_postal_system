from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user_model import User
from app.schemas.parcel_schema import ParcelCreate, ParcelResponse, ParcelUpdate
from app.services.parcel_service import (
    create_parcel,
    get_all_parcels,
    get_parcel_by_tracking,
    update_parcel,
    delete_parcel
)
from app.core.dependencies import get_current_user, role_required

router = APIRouter(
    prefix="/parcels",
    tags=["Parcels"]
)


@router.post("/", response_model=ParcelResponse)
def create_new_parcel(
    parcel: ParcelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["CUSTOMER", "ADMIN"]))
):
    return create_parcel(db, parcel, current_user.user_id)


@router.get("/", response_model=list[ParcelResponse])
def fetch_all_parcels(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"]))
):
    return get_all_parcels(db)


@router.get("/{tracking_number}", response_model=ParcelResponse)
def track_parcel(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_parcel_by_tracking(db, tracking_number)


@router.put("/{tracking_number}", response_model=ParcelResponse)
def update_existing_parcel(
    tracking_number: str,
    parcel_data: ParcelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"]))
):
    return update_parcel(db, tracking_number, parcel_data)


@router.delete("/{tracking_number}")
def remove_parcel(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"]))
):
    return delete_parcel(db, tracking_number)