from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------
# Create Employee
# -----------------------------------
class EmployeeCreate(BaseModel):
    user_id: int

    designation: str = Field(..., min_length=1, max_length=100)

    branch: str = Field(..., min_length=1, max_length=100)

    vehicle_type: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    vehicle_number: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    max_workload: int = Field(
        default=20,
        ge=1,
    )

    model_config = ConfigDict(extra="forbid")


# -----------------------------------
# Update Employee
# -----------------------------------
class EmployeeUpdate(BaseModel):
    designation: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    branch: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    vehicle_type: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    vehicle_number: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    status: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    max_workload: Optional[int] = Field(
        default=None,
        ge=1,
    )

    model_config = ConfigDict(extra="forbid")


# -----------------------------------
# Update Employee GPS
# -----------------------------------
class EmployeeLocationUpdate(BaseModel):
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )

    model_config = ConfigDict(extra="forbid")


# -----------------------------------
# Update Availability
# -----------------------------------
class EmployeeAvailabilityUpdate(BaseModel):
    is_available: bool

    model_config = ConfigDict(extra="forbid")


# -----------------------------------
# Employee Response
# -----------------------------------
class EmployeeResponse(BaseModel):
    employee_id: int
    user_id: int

    employee_code: str

    designation: str
    branch: str

    vehicle_type: Optional[str]
    vehicle_number: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    is_available: bool

    current_workload: int
    max_workload: int

    status: str

    joining_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)