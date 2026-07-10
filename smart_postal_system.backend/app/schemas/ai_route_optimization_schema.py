from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Optimization Weights
# ==========================================================

class OptimizationWeights(BaseModel):
    """
    Configurable weights used by the AI scoring engine.
    Total should ideally equal 100.
    """

    distance: float = Field(default=25.0, ge=0, le=100)
    duration: float = Field(default=20.0, ge=0, le=100)
    employee_workload: float = Field(default=20.0, ge=0, le=100)
    vehicle_capacity: float = Field(default=15.0, ge=0, le=100)
    parcel_priority: float = Field(default=20.0, ge=0, le=100)


# ==========================================================
# Request Schema
# ==========================================================

class AIRouteOptimizationRequest(BaseModel):
    """
    Request payload for AI Route Optimization.
    """

    optimization_algorithm: str = Field(
        default="Rule-Based",
        max_length=100
    )

    use_ortools: bool = Field(
        default=True,
        description=(
            "If True (default), attempt the OR-Tools CP-SAT solver first "
            "and fall back to Rule-Based if unavailable or infeasible. "
            "Set to False to always use the Rule-Based engine."
        )
    )

    weights: OptimizationWeights = Field(
        default_factory=OptimizationWeights
    )


# ==========================================================
# Response Schema
# ==========================================================

class AIRouteOptimizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    optimization_id: int

    route_id: int

    selected_vehicle_id: int

    selected_employee_id: int

    optimization_score: float

    estimated_fuel_consumption: float

    estimated_cost: float

    total_parcels: int

    optimization_algorithm: str

    optimized_sequence: List[Dict[str, Any]]

    solver_status: Optional[str] = None

    score_breakdown: Optional[Dict[str, Any]] = None

    created_at: datetime

    updated_at: Optional[datetime]


# ==========================================================
# List Response
# ==========================================================

class AIRouteOptimizationListResponse(BaseModel):
    total_records: int

    optimizations: List[AIRouteOptimizationResponse]


# ==========================================================
# Summary Schema
# ==========================================================

class OptimizationSummary(BaseModel):

    total_optimizations: int

    average_score: float

    best_score: float

    total_estimated_cost: float

    total_estimated_fuel: float