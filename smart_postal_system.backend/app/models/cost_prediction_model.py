from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class CostPrediction(Base):
    __tablename__ = "cost_predictions"

    prediction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False, index=True)
    
    predicted_cost = Column(Float, nullable=False)
    cost_lower = Column(Float, nullable=False)
    cost_upper = Column(Float, nullable=False)
    
    feature_snapshot = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=False, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    route = relationship("Route")
