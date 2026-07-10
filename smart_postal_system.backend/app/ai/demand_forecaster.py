"""
Demand Forecasting Module
===========================

Features:
- branch_id: int
- day_of_week: int (0=Monday..6=Sunday)
- month: int (1=12)
- week_of_year: int (1=53)

Model: GradientBoostingRegressor
"""

import logging
import datetime
import numpy as np
from typing import Any, Dict, List, Tuple, Optional
from sklearn.ensemble import GradientBoostingRegressor
from app.ai.model_store import ModelStore

logger = logging.getLogger(__name__)

class DemandFeatureExtractor:
    @staticmethod
    def extract_features(
        branch_id: int,
        date: datetime.date
    ) -> np.ndarray:
        """
        Extract temporal and spatial features.
        """
        day_of_week = date.weekday()
        month = date.month
        # isocalendar returns (year, week_num, day_of_week)
        week_of_year = date.isocalendar()[1]
        
        return np.array([branch_id, day_of_week, month, week_of_year], dtype=float)

class DemandModelTrainer:
    @staticmethod
    def generate_synthetic_data(n_samples: int = 400) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic demand data (number of bookings per day per branch).
        """
        np.random.seed(200)
        branch_ids = np.random.choice([1, 2, 3, 4, 5], n_samples)
        
        # Random dates over the last year
        start_date = datetime.date(2025, 1, 1)
        dates = [start_date + datetime.timedelta(days=int(x)) for x in np.random.randint(0, 365, n_samples)]
        
        X = np.zeros((n_samples, 4))
        for i in range(n_samples):
            X[i] = DemandFeatureExtractor.extract_features(branch_ids[i], dates[i])
            
        # Heuristic parcel volume:
        # - Higher on weekdays (Mon-Fri)
        # - Seasonal peak in November/December (holiday season)
        # - Vary by branch (e.g. branch 1 is busy, branch 4 is quiet)
        volumes = []
        for i in range(n_samples):
            b_id, dow, mon, woy = X[i]
            base = 15.0 if b_id == 1 else (10.0 if b_id in [2, 3] else 5.0)
            
            # Day of week factor: weekdays busy, Sunday super quiet
            dow_factor = 1.3 if dow < 5 else 0.3
            
            # Holiday season factor
            holiday_factor = 1.5 if mon in [11, 12] else 1.0
            
            vol = base * dow_factor * holiday_factor + np.random.normal(0, 2.0)
            volumes.append(max(0, int(vol)))
            
        return X, np.array(volumes, dtype=float)

    @classmethod
    def train_and_save(cls, real_data: Optional[List[Tuple[np.ndarray, float]]] = None) -> GradientBoostingRegressor:
        """
        Trains and saves the Demand Forecasting model.
        """
        X_syn, y_syn = cls.generate_synthetic_data()
        
        if real_data and len(real_data) > 0:
            X_real = np.array([item[0] for item in real_data])
            y_real = np.array([item[1] for item in real_data])
            X = np.vstack([X_syn, X_real])
            y = np.concatenate([y_syn, y_real])
        else:
            X, y = X_syn, y_syn
            
        model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        ModelStore.save_model("demand_model", model)
        return model

class DemandForecaster:
    _model = None

    @classmethod
    def get_model(cls) -> GradientBoostingRegressor:
        if cls._model is None:
            cls._model = ModelStore.load_model("demand_model")
            if cls._model is None:
                logger.info("No demand model found. Training a bootstrap model.")
                cls._model = DemandModelTrainer.train_and_save()
        return cls._model

    @classmethod
    def forecast_days(cls, branch_id: int, start_date: datetime.date, days: int = 7) -> List[Dict[str, Any]]:
        """
        Forecast parcel demand for the next N days.
        """
        model = cls.get_model()
        forecasts = []
        
        for d in range(days):
            current_date = start_date + datetime.timedelta(days=d)
            features = DemandFeatureExtractor.extract_features(branch_id, current_date)
            X = features.reshape(1, -1)
            
            predicted_volume = max(0, int(round(model.predict(X)[0])))
            
            # Simple holiday/peak day heuristic for UI display
            day_of_week = current_date.weekday()
            is_peak = day_of_week in [0, 1] and predicted_volume > 15
            
            forecasts.append({
                "date": current_date.isoformat(),
                "predicted_volume": predicted_volume,
                "is_peak_day": is_peak,
                "day_of_week": current_date.strftime("%A")
            })
            
        return forecasts
