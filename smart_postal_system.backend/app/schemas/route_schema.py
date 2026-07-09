from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteBase(BaseModel):
    route_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique Route Name",
        examples=["MDU-CHN-EXP"],
    )

    start_branch_id: int = Field(
        ...,
        gt=0,
        description="Start Branch ID",
        examples=[1],
    )

    end_branch_id: int = Field(
        ...,
        gt=0,
        description="End Branch ID",
        examples=[2],
    )

    distance_km: float = Field(
        ...,
        gt=0.0,
        description="Distance in Kilometers",
        examples=[450.5],
    )

    estimated_duration_minutes: int = Field(
        ...,
        gt=0,
        description="Estimated duration of transit in minutes",
        examples=[480],
    )


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    route_name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    start_branch_id: Optional[int] = Field(default=None, gt=0)
    end_branch_id: Optional[int] = Field(default=None, gt=0)
    distance_km: Optional[float] = Field(default=None, gt=0.0)
    estimated_duration_minutes: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class RouteResponse(RouteBase):
    route_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
