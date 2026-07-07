from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user_model import User
from app.schemas.tracking_schema import (
    TrackingHistoryCreate,
    TrackingHistoryResponse,
    TrackingHistoryUpdate
)
from app.services.tracking_service import (
    create_tracking_history,
    get_tracking_by_id,
    get_tracking_history_for_parcel,
    update_tracking_history,
    delete_tracking_history
)
from app.core.dependencies import get_current_user, role_required

router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"]
)


@router.post("/", response_model=TrackingHistoryResponse)
def create_new_tracking_record(
    tracking: TrackingHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"]))
):
    return create_tracking_history(db, tracking)


@router.get("/parcel/{parcel_id}", response_model=list[TrackingHistoryResponse])
def get_parcel_tracking_history(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_tracking_history_for_parcel(db, parcel_id)


@router.get("/{tracking_id}", response_model=TrackingHistoryResponse)
def get_tracking_record(
    tracking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_tracking_by_id(db, tracking_id)


@router.put("/{tracking_id}", response_model=TrackingHistoryResponse)
def update_existing_tracking_record(
    tracking_id: int,
    tracking_data: TrackingHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN", "EMPLOYEE"]))
):
    return update_tracking_history(db, tracking_id, tracking_data)


@router.delete("/{tracking_id}")
def remove_tracking_record(
    tracking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["ADMIN"]))
):
    return delete_tracking_history(db, tracking_id)
