from pydantic import BaseModel, ConfigDict, Field


class RouteOptimizationRequest(BaseModel):
    """
    Request schema for route optimization.
    """

    route_id: int = Field(
        ...,
        gt=0,
        description="Unique Route ID"
    )


class RouteOptimizationResponse(BaseModel):
    """
    Response schema returned after successful optimization.
    """

    route_id: int

    route_name: str

    start_branch_id: int

    end_branch_id: int

    distance_km: float

    estimated_duration_minutes: int

    route_geometry: str

    optimization_status: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "route_id": 1,
                "route_name": "MDU-CHN-EXP",
                "start_branch_id": 1,
                "end_branch_id": 2,
                "distance_km": 451.23,
                "estimated_duration_minutes": 472,
                "route_geometry": "encoded_polyline_here",
                "optimization_status": "SUCCESS"
            }
        }
    )