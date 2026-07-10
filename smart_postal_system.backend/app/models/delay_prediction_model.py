from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class DelayPrediction(Base):
    __tablename__ = "delay_predictions"

    prediction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey("parcels.parcel_id", ondelete="CASCADE"), nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id", ondelete="SET NULL"), nullable=True)
    
    predicted_delay = Column(Boolean, nullable=False)
    delay_probability = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    
    feature_snapshot = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=False, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    parcel = relationship("Parcel")
    route = relationship("Route")
