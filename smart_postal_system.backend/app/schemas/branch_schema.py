from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BranchBase(BaseModel):
    branch_code: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Unique Branch Code",
        examples=["MDU001"],
    )

    branch_name: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Branch Name",
        examples=["Madurai Central Branch"],
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Madurai"],
    )

    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Tamil Nadu"],
    )

    postal_code: str = Field(
        ...,
        min_length=5,
        max_length=10,
        examples=["625001"],
    )

    address: str = Field(
        ...,
        min_length=10,
        examples=["12, Anna Salai, Madurai"],
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude",
        examples=[9.9252],
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude",
        examples=[78.1198],
    )

    contact_number: str = Field(
        ...,
        min_length=8,
        max_length=20,
        examples=["9876543210"],
    )

    email: EmailStr

    manager_name: str = Field(
        ...,
        min_length=3,
        max_length=150,
        examples=["Balamurugan"],
    )


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    branch_code: Optional[str] = Field(default=None, min_length=2, max_length=20)

    branch_name: Optional[str] = Field(default=None, min_length=3, max_length=150)

    city: Optional[str] = Field(default=None, min_length=2, max_length=100)

    state: Optional[str] = Field(default=None, min_length=2, max_length=100)

    postal_code: Optional[str] = Field(default=None, min_length=5, max_length=10)

    address: Optional[str] = None

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)

    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    contact_number: Optional[str] = Field(default=None, min_length=8, max_length=20)

    email: Optional[EmailStr] = None

    manager_name: Optional[str] = Field(default=None, min_length=3, max_length=150)

    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)