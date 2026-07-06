from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# Create Delivery Assignment
# --------------------------------------------------
class DeliveryAssignmentCreate(BaseModel):
    parcel_id: int

    employee_id: int

    priority: str = Field(
        default="MEDIUM",
        max_length=20
    )

    remarks: Optional[str] = None


# --------------------------------------------------
# Update Delivery Assignment
# --------------------------------------------------
class DeliveryAssignmentUpdate(BaseModel):

    employee_id: Optional[int] = None

    priority: Optional[str] = Field(
        default=None,
        max_length=20
    )

    remarks: Optional[str] = None


# --------------------------------------------------
# Update Assignment Status
# --------------------------------------------------
class AssignmentStatusUpdate(BaseModel):

    assignment_status: str = Field(
        ...,
        max_length=30
    )


# --------------------------------------------------
# Response Model
# --------------------------------------------------
class DeliveryAssignmentResponse(BaseModel):

    assignment_id: int

    parcel_id: int

    employee_id: int

    assigned_by: Optional[int]

    assignment_status: str

    priority: str

    remarks: Optional[str]

    assigned_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )