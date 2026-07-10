from sqlalchemy.orm import Session
from datetime import datetime
from app.ai.delay_prediction import DelayFeatureExtractor, DelayPredictor, DelayModelTrainer
from app.models.delay_prediction_model import DelayPrediction
from app.models.parcel_model import Parcel
from app.models.route_model import Route
from app.models.branch_model import Branch
from app.schemas.predictions_schema import DelayPredictionResponse

class DelayPredictionService:
    @staticmethod
    def predict_delay(db: Session, parcel_id: int) -> DelayPrediction:
        # Load parcel
        parcel = db.query(Parcel).filter(Parcel.parcel_id == parcel_id).first()
        if not parcel:
            raise ValueError(f"Parcel with ID {parcel_id} not found.")

        # Find source and destination branches
        start_branch = db.query(Branch).filter(
            (Branch.branch_code == parcel.source_branch) | 
            (Branch.branch_name == parcel.source_branch)
        ).first()

        end_branch = db.query(Branch).filter(
            (Branch.branch_code == parcel.destination_branch) | 
            (Branch.branch_name == parcel.destination_branch)
        ).first()

        route = None
        if start_branch and end_branch:
            route = db.query(Route).filter(
                Route.start_branch_id == start_branch.branch_id,
                Route.end_branch_id == end_branch.branch_id
            ).first()

        # Fallback values if route doesn't exist
        dummy_route = type('DummyRoute', (), {
            'distance_km': 100.0,
            'estimated_duration_minutes': 120.0
        })()
        route_to_use = route if route else dummy_route

        # Count total parcels in transit for context
        parcel_count = db.query(Parcel).filter(Parcel.status == "IN_TRANSIT").count()
        if parcel_count == 0:
            parcel_count = 5  # default baseline

        day_of_week = datetime.now().weekday()

        # Extract features
        features = DelayFeatureExtractor.extract_features(
            parcel=parcel,
            route=route_to_use,
            parcel_count=parcel_count,
            day_of_week=day_of_week
        )

        # Run model prediction
        prediction_result = DelayPredictor.predict(features)

        # Save to DB
        db_prediction = DelayPrediction(
            parcel_id=parcel.parcel_id,
            route_id=route.route_id if route else None,
            predicted_delay=prediction_result["is_delayed"],
            delay_probability=prediction_result["delay_probability"],
            risk_level=prediction_result["risk_level"],
            feature_snapshot={
                "weight": float(getattr(parcel, "weight", 0.0)),
                "distance": float(getattr(route_to_use, "distance_km", 0.0)),
                "duration": float(getattr(route_to_use, "estimated_duration_minutes", 0.0)),
                "parcel_count": parcel_count,
                "day_of_week": day_of_week
            },
            model_version="v1"
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return db_prediction

    @staticmethod
    def retrain_model(db: Session) -> str:
        # Load past deliveries with tracking history to verify if they were delayed.
        # Since we might not have a lot of completed deliveries, we'll build a dataset
        # of whatever completed deliveries we have, plus the synthetic bootstrap.
        completed_parcels = db.query(Parcel).filter(Parcel.status == "DELIVERED").all()
        
        real_data = []
        for p in completed_parcels:
            # Check if actual delivery exceeded expected delivery
            if p.expected_delivery and p.actual_delivery:
                is_delayed = 1 if p.actual_delivery > p.expected_delivery else 0
                
                # Fetch route
                start_branch = db.query(Branch).filter(
                    (Branch.branch_code == p.source_branch) | 
                    (Branch.branch_name == p.source_branch)
                ).first()
                end_branch = db.query(Branch).filter(
                    (Branch.branch_code == p.destination_branch) | 
                    (Branch.branch_name == p.destination_branch)
                ).first()
                
                route = None
                if start_branch and end_branch:
                    route = db.query(Route).filter(
                        Route.start_branch_id == start_branch.branch_id,
                        Route.end_branch_id == end_branch.branch_id
                    ).first()
                
                dummy_route = type('DummyRoute', (), {
                    'distance_km': 100.0,
                    'estimated_duration_minutes': 120.0
                })()
                route_to_use = route if route else dummy_route
                
                features = DelayFeatureExtractor.extract_features(
                    parcel=p,
                    route=route_to_use,
                    parcel_count=10,
                    day_of_week=p.booking_date.weekday() if p.booking_date else 0
                )
                real_data.append((features, is_delayed))
                
        DelayModelTrainer.train_and_save(real_data=real_data)
        return f"Successfully retrained delay prediction model with {len(real_data)} real samples."
