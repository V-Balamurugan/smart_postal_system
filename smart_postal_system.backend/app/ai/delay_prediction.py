"""
Delay Prediction Module
=======================

Features:
- weight: float
- distance: float
- duration: float
- priority: int (1=LOW, 2=NORMAL/MEDIUM, 3=HIGH)
- day_of_week: int (0=Monday..6=Sunday)
- parcel_count: int

Model: GradientBoostingClassifier
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from sklearn.ensemble import GradientBoostingClassifier
from app.ai.model_store import ModelStore

logger = logging.getLogger(__name__)

class DelayFeatureExtractor:
    @staticmethod
    def extract_features(
        parcel: Any,
        route: Any,
        parcel_count: int,
        day_of_week: int
    ) -> np.ndarray:
        """
        Extract features as a 1D numpy array:
        [weight, distance, duration, priority_val, day_of_week, parcel_count]
        """
        weight = float(getattr(parcel, "weight", 1.0))
        distance = float(getattr(route, "distance_km", getattr(route, "distance", 10.0)))
        duration = float(getattr(route, "estimated_duration_minutes", getattr(route, "estimated_duration", 30.0)))
        
        priority = getattr(parcel, "priority_level", getattr(parcel, "priority", "NORMAL"))
        priority_map = {"HIGH": 3, "MEDIUM": 2, "NORMAL": 2, "LOW": 1}
        priority_val = priority_map.get(priority, 2)
        
        return np.array([weight, distance, duration, priority_val, day_of_week, parcel_count], dtype=float)

class DelayModelTrainer:
    @staticmethod
    def generate_synthetic_data(n_samples: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for bootstrap.
        Rules:
        - Longer distance & duration -> higher delay probability.
        - Higher weight -> slightly higher delay.
        - Higher parcel_count -> slightly higher delay.
        - Priority HIGH -> lower delay probability (hurried).
        """
        np.random.seed(42)
        weights = np.random.uniform(0.1, 50.0, n_samples)
        distances = np.random.uniform(5.0, 500.0, n_samples)
        durations = distances * np.random.uniform(1.0, 1.5, n_samples) + np.random.uniform(5.0, 60.0, n_samples)
        priorities = np.random.choice([1, 2, 3], n_samples, p=[0.2, 0.6, 0.2])
        days = np.random.randint(0, 7, n_samples)
        parcel_counts = np.random.randint(1, 30, n_samples)
        
        X = np.column_stack([weights, distances, durations, priorities, days, parcel_counts])
        
        # Calculate raw delay risk score
        risk = (distances / 200.0) + (durations / 300.0) + (weights / 40.0) + (parcel_counts / 15.0) - (priorities * 0.3)
        risk += np.random.normal(0, 0.3, n_samples)
        
        # Binary target: 1 = delayed, 0 = on-time
        y = (risk > 1.2).astype(int)
        
        return X, y

    @classmethod
    def train_and_save(cls, real_data: Optional[List[Tuple[np.ndarray, int]]] = None) -> GradientBoostingClassifier:
        """
        Trains the GradientBoostingClassifier on real + synthetic data and saves it.
        """
        X_syn, y_syn = cls.generate_synthetic_data()
        
        if real_data and len(real_data) > 0:
            X_real = np.array([item[0] for item in real_data])
            y_real = np.array([item[1] for item in real_data])
            X = np.vstack([X_syn, X_real])
            y = np.concatenate([y_syn, y_real])
        else:
            X, y = X_syn, y_syn
            
        model = GradientBoostingClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        ModelStore.save_model("delay_model", model)
        return model

class DelayPredictor:
    _model = None

    @classmethod
    def get_model(cls) -> GradientBoostingClassifier:
        if cls._model is None:
            cls._model = ModelStore.load_model("delay_model")
            if cls._model is None:
                logger.info("No delay prediction model found. Training a bootstrap model.")
                cls._model = DelayModelTrainer.train_and_save()
        return cls._model

    @classmethod
    def predict(cls, features: np.ndarray) -> Dict[str, Any]:
        """
        Predicts if a parcel will be delayed.
        """
        model = cls.get_model()
        X = features.reshape(1, -1)
        
        # Prediction
        is_delayed = bool(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][1])
        
        # Determine risk level
        if prob < 0.3:
            risk_level = "LOW"
        elif prob < 0.7:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "is_delayed": is_delayed,
            "delay_probability": round(prob, 4),
            "risk_level": risk_level
        }
