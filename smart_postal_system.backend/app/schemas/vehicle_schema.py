from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class FuelType(str, Enum):
    PETROL = "PETROL"
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    CNG = "CNG"


class VehicleBase(BaseModel):
    vehicle_number: str = Field(
        ...,
        min_length=5,
        max_length=20,
        examples=["TN58AB1234"],
    )

    vehicle_type: str = Field(
        ...,
        max_length=50,
        examples=["VAN"],
    )

    brand: str = Field(
        ...,
        max_length=100,
        examples=["Tata"],
    )

    model: str = Field(
        ...,
        max_length=100,
        examples=["Ace Gold"],
    )

    capacity_kg: float = Field(
        ...,
        gt=0,
        examples=[750],
    )

    current_branch_id: int = Field(
        ...,
        gt=0,
        examples=[1],
    )

    fuel_type: FuelType

    insurance_expiry: date

    registration_expiry: date

    current_latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        examples=[9.9252],
    )

    current_longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        examples=[78.1198],
    )

    last_service_date: Optional[date] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = Field(default=None, min_length=5, max_length=20)
    vehicle_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    capacity_kg: Optional[float] = Field(default=None, gt=0)
    current_branch_id: Optional[int] = Field(default=None, gt=0)
    fuel_type: Optional[FuelType] = None
    insurance_expiry: Optional[date] = None
    registration_expiry: Optional[date] = None
    current_latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    current_longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    last_service_date: Optional[date] = None


class AssignDriverSchema(BaseModel):
    driver_id: int = Field(
        ...,
        gt=0,
        examples=[5],
    )


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class VehicleResponse(VehicleBase):
    vehicle_id: int
    driver_id: Optional[int]
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)