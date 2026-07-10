from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.ai.demand_forecaster import DemandForecaster, DemandModelTrainer, DemandFeatureExtractor
from app.models.demand_forecast_model import DemandForecast
from app.models.branch_model import Branch
from app.models.parcel_model import Parcel
from sqlalchemy import func
from typing import List, Dict, Any

class DemandForecastService:
    @staticmethod
    def forecast_demand(db: Session, branch_id: int, days: int = 7) -> Dict[str, Any]:
        branch = db.query(Branch).filter(Branch.branch_id == branch_id).first()
        if not branch:
            raise ValueError(f"Branch with ID {branch_id} not found.")

        start_date = date.today()
        forecasts = DemandForecaster.forecast_days(branch_id, start_date, days)

        db_forecasts = []
        for f in forecasts:
            f_date = date.fromisoformat(f["date"])
            
            # Check if forecast already exists for this branch and date
            existing = db.query(DemandForecast).filter(
                DemandForecast.branch_id == branch_id,
                DemandForecast.forecast_date == f_date
            ).first()

            if existing:
                existing.predicted_volume = f["predicted_volume"]
                existing.is_peak_day = "TRUE" if f["is_peak_day"] else "FALSE"
                db_forecast = existing
            else:
                db_forecast = DemandForecast(
                    branch_id=branch_id,
                    forecast_date=f_date,
                    predicted_volume=f["predicted_volume"],
                    is_peak_day="TRUE" if f["is_peak_day"] else "FALSE",
                    model_version="v1"
                )
                db.add(db_forecast)
                
            db_forecasts.append(db_forecast)

        db.commit()
        
        # Format response
        return {
            "branch_id": branch_id,
            "forecasts": [
                {
                    "date": f_date,
                    "predicted_volume": f["predicted_volume"],
                    "is_peak_day": f["is_peak_day"],
                    "day_of_week": f["day_of_week"]
                }
                for f in forecasts
            ],
            "model_version": "v1",
            "created_at": datetime.now()
        }

    @staticmethod
    def retrain_model(db: Session, branch_id: int) -> str:
        # Get historical bookings for this branch from the parcels table
        # We group parcels by branch and booking date
        branch = db.query(Branch).filter(Branch.branch_id == branch_id).first()
        if not branch:
            raise ValueError(f"Branch with ID {branch_id} not found.")

        # Query all parcels sent from this branch, group by booking_date date-only
        # Booking date is a DateTime, so we cast to Date
        from sqlalchemy import cast, Date
        history = db.query(
            cast(Parcel.booking_date, Date).label("b_date"),
            func.count(Parcel.parcel_id).label("cnt")
        ).filter(
            (Parcel.source_branch == branch.branch_code) |
            (Parcel.source_branch == branch.branch_name)
        ).group_by("b_date").all()

        real_data = []
        for row in history:
            if row.b_date:
                features = DemandFeatureExtractor.extract_features(branch_id, row.b_date)
                real_data.append((features, float(row.cnt)))

        DemandModelTrainer.train_and_save(real_data=real_data)
        return f"Successfully retrained demand forecaster with {len(real_data)} real daily samples."
