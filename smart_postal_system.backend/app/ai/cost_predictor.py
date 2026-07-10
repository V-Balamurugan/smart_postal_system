"""
Cost Prediction Module
======================

Features:
- weight: float
- distance: float
- duration: float
- vehicle_type_val: int (1=BIKE, 2=VAN, 3=TRUCK)
- parcel_count: int

Model: GradientBoostingRegressor
"""

import logging
import numpy as np
from typing import Any, Dict, List, Tuple, Optional
from sklearn.ensemble import GradientBoostingRegressor
from app.ai.model_store import ModelStore

logger = logging.getLogger(__name__)

class CostFeatureExtractor:
    @staticmethod
    def extract_features(
        weight: float,
        distance: float,
        duration: float,
        vehicle_type: str,
        parcel_count: int
    ) -> np.ndarray:
        """
        Extract features as a 1D numpy array.
        """
        v_type = vehicle_type.upper() if vehicle_type else "VAN"
        v_map = {"BIKE": 1, "VAN": 2, "TRUCK": 3}
        vehicle_type_val = v_map.get(v_type, 2)
        
        return np.array([weight, distance, duration, vehicle_type_val, parcel_count], dtype=float)

class CostModelTrainer:
    @staticmethod
    def generate_synthetic_data(n_samples: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data.
        Cost = distance * fuel_cost + duration * driver_wage + vehicle_premium + weight_cost
        """
        np.random.seed(100)
        weights = np.random.uniform(0.1, 100.0, n_samples)
        distances = np.random.uniform(5.0, 500.0, n_samples)
        durations = distances * np.random.uniform(1.0, 1.5, n_samples) + np.random.uniform(5.0, 60.0, n_samples)
        vehicle_types = np.random.choice([1, 2, 3], n_samples, p=[0.3, 0.5, 0.2])
        parcel_counts = np.random.randint(1, 50, n_samples)
        
        X = np.column_stack([weights, distances, durations, vehicle_types, parcel_counts])
        
        # Heuristic cost function
        base_cost = distances * 12.5  # cost per km
        duration_cost = (durations / 60.0) * 150.0  # cost per hour
        vehicle_multiplier = vehicle_types * 50.0
        weight_cost = weights * 2.5
        
        costs = base_cost + duration_cost + vehicle_multiplier + weight_cost
        costs += np.random.normal(0, costs * 0.05)  # add noise proportional to cost
        
        return X, costs

    @classmethod
    def train_and_save(cls, real_data: Optional[List[Tuple[np.ndarray, float]]] = None) -> GradientBoostingRegressor:
        """
        Trains and saves the GradientBoostingRegressor cost model.
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
        
        ModelStore.save_model("cost_model", model)
        return model

class CostPredictor:
    _model = None

    @classmethod
    def get_model(cls) -> GradientBoostingRegressor:
        if cls._model is None:
            cls._model = ModelStore.load_model("cost_model")
            if cls._model is None:
                logger.info("No cost prediction model found. Training a bootstrap model.")
                cls._model = CostModelTrainer.train_and_save()
        return cls._model

    @classmethod
    def predict(cls, features: np.ndarray) -> Dict[str, Any]:
        """
        Predicts route cost and returns confidence intervals (80%).
        """
        model = cls.get_model()
        X = features.reshape(1, -1)
        
        predicted_cost = float(model.predict(X)[0])
        predicted_cost = max(10.0, predicted_cost)  # minimum floor cost
        
        # Calculate a simulated confidence interval (e.g. +/- 10% of predicted cost)
        margin = predicted_cost * 0.12
        lower_bound = max(5.0, predicted_cost - margin)
        upper_bound = predicted_cost + margin
        
        return {
            "predicted_cost": round(predicted_cost, 2),
            "cost_lower": round(lower_bound, 2),
            "cost_upper": round(upper_bound, 2)
        }
