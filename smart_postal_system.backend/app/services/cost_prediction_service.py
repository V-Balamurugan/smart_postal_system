from sqlalchemy.orm import Session
from app.ai.cost_predictor import CostFeatureExtractor, CostPredictor, CostModelTrainer
from app.models.cost_prediction_model import CostPrediction
from app.models.route_model import Route
from app.models.parcel_model import Parcel
from app.models.branch_model import Branch
from typing import List, Optional

class CostPredictionService:
    @staticmethod
    def predict_cost(db: Session, route_id: int, vehicle_type: str = "VAN") -> CostPrediction:
        route = db.query(Route).filter(Route.route_id == route_id).first()
        if not route:
            raise ValueError(f"Route with ID {route_id} not found.")

        # Find parcels for this route
        start_branch = route.start_branch
        end_branch = route.end_branch
        
        parcels = []
        if start_branch and end_branch:
            parcels = db.query(Parcel).filter(
                (
                    (Parcel.source_branch == start_branch.branch_code) |
                    (Parcel.source_branch == start_branch.branch_name)
                ) &
                (
                    (Parcel.destination_branch == end_branch.branch_code) |
                    (Parcel.destination_branch == end_branch.branch_name)
                )
            ).all()

        total_weight = sum(float(getattr(p, "weight", 0.0)) for p in parcels)
        parcel_count = len(parcels)
        if parcel_count == 0:
            parcel_count = 1  # default fallback

        features = CostFeatureExtractor.extract_features(
            weight=total_weight,
            distance=float(route.distance_km),
            duration=float(route.estimated_duration_minutes),
            vehicle_type=vehicle_type,
            parcel_count=parcel_count
        )

        prediction_result = CostPredictor.predict(features)

        db_prediction = CostPrediction(
            route_id=route.route_id,
            predicted_cost=prediction_result["predicted_cost"],
            cost_lower=prediction_result["cost_lower"],
            cost_upper=prediction_result["cost_upper"],
            feature_snapshot={
                "weight": total_weight,
                "distance": float(route.distance_km),
                "duration": float(route.estimated_duration_minutes),
                "vehicle_type": vehicle_type,
                "parcel_count": parcel_count
            },
            model_version="v1"
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return db_prediction

    @staticmethod
    def retrain_model(db: Session) -> str:
        # Load completed historical routes/trips to retrain
        # For simplicity, we can load from the AIRouteOptimization history if costs are recorded,
        # or we generate a dataset from DB records.
        from app.models.ai_route_optimization_model import AIRouteOptimization
        
        history = db.query(AIRouteOptimization).all()
        real_data = []
        for opt in history:
            route = db.query(Route).filter(Route.route_id == opt.route_id).first()
            if route:
                features = CostFeatureExtractor.extract_features(
                    weight=10.0,  # placeholder
                    distance=float(route.distance_km),
                    duration=float(route.estimated_duration_minutes),
                    vehicle_type="VAN",
                    parcel_count=opt.total_parcels
                )
                real_data.append((features, float(opt.estimated_cost)))
                
        CostModelTrainer.train_and_save(real_data=real_data)
        return f"Successfully retrained cost predictor model with {len(real_data)} real samples."
