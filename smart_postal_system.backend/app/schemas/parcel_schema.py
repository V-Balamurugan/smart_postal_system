from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ParcelCreate(BaseModel):
    receiver_name: str
    receiver_phone: str
    receiver_email: Optional[EmailStr] = None

    pickup_address: str
    delivery_address: str

    source_branch: str
    destination_branch: str

    category_id: Optional[int] = None

    weight: float
    parcel_value: float

    priority_level: Optional[str] = "NORMAL"


class ParcelResponse(BaseModel):
    parcel_id: int
    tracking_number: str
    sender_id: int

    receiver_name: str
    receiver_phone: str
    receiver_email: Optional[EmailStr]

    pickup_address: str
    delivery_address: str

    source_branch: str
    destination_branch: str

    category_id: Optional[int]

    weight: float
    parcel_value: float

    priority_level: str
    status: str

    booking_date: datetime
    expected_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]

    class Config:
        from_attributes = True


class ParcelUpdate(BaseModel):
    status: Optional[str] = None
    expected_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None