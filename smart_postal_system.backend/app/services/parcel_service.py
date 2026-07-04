from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
import random

from app.models.parcel_model import Parcel
from app.schemas.parcel_schema import ParcelCreate, ParcelUpdate


def generate_tracking_number():
    return f"TRK{random.randint(100000, 999999)}"


def create_parcel(db: Session, parcel: ParcelCreate, sender_id: int):
    tracking_number = generate_tracking_number()
    expected_delivery = datetime.utcnow() + timedelta(days=3)

    new_parcel = Parcel(
        tracking_number=tracking_number,
        sender_id=sender_id,
        receiver_name=parcel.receiver_name,
        receiver_phone=parcel.receiver_phone,
        receiver_email=parcel.receiver_email,
        pickup_address=parcel.pickup_address,
        delivery_address=parcel.delivery_address,
        source_branch=parcel.source_branch,
        destination_branch=parcel.destination_branch,
        category_id=parcel.category_id,
        weight=parcel.weight,
        parcel_value=parcel.parcel_value,
        priority_level=parcel.priority_level,
        status="PENDING",
        expected_delivery=expected_delivery
    )

    db.add(new_parcel)
    db.commit()
    db.refresh(new_parcel)

    return new_parcel


def get_all_parcels(db: Session):
    return db.query(Parcel).all()


def get_parcel_by_tracking(db: Session, tracking_number: str):
    parcel = db.query(Parcel).filter(
        Parcel.tracking_number == tracking_number
    ).first()

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return parcel


def update_parcel(db: Session, tracking_number: str, parcel_data: ParcelUpdate):
    parcel = db.query(Parcel).filter(
        Parcel.tracking_number == tracking_number
    ).first()

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    update_data = parcel_data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(parcel, key, value)

    db.commit()
    db.refresh(parcel)

    return parcel


def delete_parcel(db: Session, tracking_number: str):
    parcel = db.query(Parcel).filter(
        Parcel.tracking_number == tracking_number
    ).first()

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    db.delete(parcel)
    db.commit()

    return {"message": "Parcel deleted successfully"}