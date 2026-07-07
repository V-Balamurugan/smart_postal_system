from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TrackingHistoryBase(BaseModel):
    parcel_id: int = Field(..., gt=0, description="Parcel ID")
    employee_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Employee ID (optional)"
    )
    branch_id: int = Field(..., gt=0, description="Branch ID")

    status: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Current parcel status"
    )

    remarks: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Tracking remarks"
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitude"
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitude"
    )


class TrackingHistoryCreate(TrackingHistoryBase):
    """Schema used to create a tracking history record."""
    pass


class TrackingHistoryUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    remarks: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180
    )


class TrackingHistoryResponse(TrackingHistoryBase):
    tracking_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)