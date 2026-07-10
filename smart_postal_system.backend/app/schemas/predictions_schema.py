from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime, date

# ==========================================================
# Delay Prediction Schemas
# ==========================================================

class DelayPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    parcel_id: int
    route_id: Optional[int]
    predicted_delay: bool
    delay_probability: float
    risk_level: str
    feature_snapshot: Optional[Dict[str, Any]]
    model_version: str
    created_at: datetime

# ==========================================================
# Cost Prediction Schemas
# ==========================================================

class CostPredictionRequest(BaseModel):
    vehicle_type: Optional[str] = "VAN"

class CostPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    route_id: int
    predicted_cost: float
    cost_lower: float
    cost_upper: float
    feature_snapshot: Optional[Dict[str, Any]]
    model_version: str
    created_at: datetime

# ==========================================================
# Demand Forecasting Schemas
# ==========================================================

class DemandForecastRequest(BaseModel):
    days: Optional[int] = 7

class DemandForecastDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    date: date
    predicted_volume: int
    is_peak_day: bool
    day_of_week: str

class DemandForecastResponse(BaseModel):
    branch_id: int
    forecasts: List[DemandForecastDay]
    model_version: str
    created_at: datetime
