from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.tracking_model import TrackingHistory
from app.schemas.tracking_schema import TrackingHistoryCreate, TrackingHistoryUpdate


def create_tracking_history(db: Session, tracking: TrackingHistoryCreate):
    new_tracking = TrackingHistory(
        parcel_id=tracking.parcel_id,
        employee_id=tracking.employee_id,
        branch_id=tracking.branch_id,
        status=tracking.status,
        remarks=tracking.remarks,
        latitude=tracking.latitude,
        longitude=tracking.longitude,
    )
    db.add(new_tracking)
    db.commit()
    db.refresh(new_tracking)
    return new_tracking


def get_tracking_by_id(db: Session, tracking_id: int):
    tracking = db.query(TrackingHistory).filter(
        TrackingHistory.tracking_id == tracking_id
    ).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    return tracking


def get_tracking_history_for_parcel(db: Session, parcel_id: int):
    return db.query(TrackingHistory).filter(
        TrackingHistory.parcel_id == parcel_id
    ).order_by(TrackingHistory.created_at.desc()).all()


def update_tracking_history(db: Session, tracking_id: int, tracking_data: TrackingHistoryUpdate):
    tracking = db.query(TrackingHistory).filter(
        TrackingHistory.tracking_id == tracking_id
    ).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    update_data = tracking_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracking, key, value)
        
    db.commit()
    db.refresh(tracking)
    return tracking


def delete_tracking_history(db: Session, tracking_id: int):
    tracking = db.query(TrackingHistory).filter(
        TrackingHistory.tracking_id == tracking_id
    ).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
        
    db.delete(tracking)
    db.commit()
    return {"message": "Tracking record deleted successfully"}
