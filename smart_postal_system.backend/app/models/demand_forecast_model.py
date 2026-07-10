from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    forecast_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False, index=True)
    
    forecast_date = Column(Date, nullable=False)
    predicted_volume = Column(Integer, nullable=False)
    is_peak_day = Column(String(10), nullable=False, default="FALSE")
    
    model_version = Column(String(50), nullable=False, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    branch = relationship("Branch")
