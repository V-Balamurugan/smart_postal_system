from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.user_model import User

from app.schemas.predictions_schema import (
    DelayPredictionResponse,
    CostPredictionRequest,
    CostPredictionResponse,
    DemandForecastRequest,
    DemandForecastResponse
)
from app.services.delay_prediction_service import DelayPredictionService
from app.services.cost_prediction_service import CostPredictionService
from app.services.demand_forecast_service import DemandForecastService

from app.models.delay_prediction_model import DelayPrediction
from app.models.cost_prediction_model import CostPrediction
from app.models.demand_forecast_model import DemandForecast

router = APIRouter(
    prefix="/ai",
    tags=["AI Predictions & Forecasting"]
)

# ==========================================================
# Delay Prediction Endpoints
# ==========================================================

@router.post(
    "/predict/delay/{parcel_id}",
    response_model=DelayPredictionResponse,
    status_code=status.HTTP_201_CREATED
)
def predict_delay(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict delivery delay probability and risk level for a specific parcel.
    """
    try:
        return DelayPredictionService.predict_delay(db, parcel_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get(
    "/predict/delay/{prediction_id}",
    response_model=DelayPredictionResponse
)
def get_delay_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a saved delay prediction by ID.
    """
    prediction = db.query(DelayPrediction).filter(
        DelayPrediction.prediction_id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delay prediction with ID {prediction_id} not found."
        )
    return prediction


# ==========================================================
# Cost Prediction Endpoints
# ==========================================================

@router.post(
    "/predict/cost/{route_id}",
    response_model=CostPredictionResponse,
    status_code=status.HTTP_201_CREATED
)
def predict_cost(
    route_id: int,
    request: CostPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict operational cost for a delivery route.
    """
    try:
        return CostPredictionService.predict_cost(
            db=db,
            route_id=route_id,
            vehicle_type=request.vehicle_type
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get(
    "/predict/cost/{prediction_id}",
    response_model=CostPredictionResponse
)
def get_cost_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a saved cost prediction by ID.
    """
    prediction = db.query(CostPrediction).filter(
        CostPrediction.prediction_id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost prediction with ID {prediction_id} not found."
        )
    return prediction


# ==========================================================
# Demand Forecasting Endpoints
# ==========================================================

@router.post(
    "/forecast/demand/{branch_id}",
    response_model=DemandForecastResponse,
    status_code=status.HTTP_201_CREATED
)
def forecast_demand(
    branch_id: int,
    request: DemandForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forecast daily parcel demand for the next N days at a given branch.
    """
    try:
        days = request.days if request.days else 7
        return DemandForecastService.forecast_demand(
            db=db,
            branch_id=branch_id,
            days=days
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get(
    "/forecast/demand/{branch_id}",
    response_model=List[DemandForecastResponse]
)
def list_demand_forecasts(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve recent demand forecast records for a branch.
    """
    # Group forecasts by created_at time to construct historical runs
    # To keep it simple, we group by branch_id and return the forecast runs.
    # But since list response matches schema, let's query the table:
    forecast_records = db.query(DemandForecast).filter(
        DemandForecast.branch_id == branch_id
    ).order_by(DemandForecast.forecast_date.asc()).all()

    if not forecast_records:
        return []

    # Map database flat rows back to the grouped response structure
    # For simplicity, we wrap all current records in a single run
    from datetime import date
    days = []
    for r in forecast_records:
        from datetime import datetime
        d_obj = r.forecast_date
        # date object string representation or date
        days.append({
            "date": d_obj,
            "predicted_volume": r.predicted_volume,
            "is_peak_day": r.is_peak_day == "TRUE",
            # dummy day of week for mapping
            "day_of_week": d_obj.strftime("%A") if isinstance(d_obj, (date, datetime)) else "Unknown"
        })
        
    # Return a list of forecast runs
    latest_record = forecast_records[-1] if forecast_records else None
    created_at = latest_record.created_at if latest_record else datetime.now()
    
    return [{
        "branch_id": branch_id,
        "forecasts": days,
        "model_version": "v1",
        "created_at": created_at
    }]


# ==========================================================
# ML Retraining Endpoints
# ==========================================================

@router.post("/retrain/delay")
def retrain_delay_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger retraining for the delay prediction classifier model.
    """
    msg = DelayPredictionService.retrain_model(db)
    return {"status": "success", "message": msg}


@router.post("/retrain/cost")
def retrain_cost_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger retraining for the cost prediction regressor model.
    """
    msg = CostPredictionService.retrain_model(db)
    return {"status": "success", "message": msg}


@router.post("/retrain/demand/{branch_id}")
def retrain_demand_model(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger retraining for the demand forecaster model for a branch.
    """
    try:
        msg = DemandForecastService.retrain_model(db, branch_id)
        return {"status": "success", "message": msg}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
