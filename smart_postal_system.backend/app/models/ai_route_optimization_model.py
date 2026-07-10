from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class AIRouteOptimization(Base):
    __tablename__ = "ai_route_optimizations"

    optimization_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    route_id = Column(
        Integer,
        ForeignKey("routes.route_id", ondelete="CASCADE"),
        nullable=False
    )

    selected_vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.vehicle_id"),
        nullable=False
    )

    selected_employee_id = Column(
        Integer,
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    optimization_score = Column(
        Float,
        nullable=False
    )

    estimated_fuel_consumption = Column(
        Float,
        nullable=False
    )

    estimated_cost = Column(
        Float,
        nullable=False
    )

    total_parcels = Column(
        Integer,
        nullable=False
    )

    optimization_algorithm = Column(
        String(100),
        nullable=False,
        default="Rule-Based"
    )

    optimized_sequence = Column(
        JSON,
        nullable=False
    )

    solver_status = Column(
        String(50),
        nullable=True,
        default="RULE_BASED"
    )

    score_breakdown = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships

    route = relationship(
        "Route",
        back_populates="ai_route_optimizations"
    )

    vehicle = relationship(
        "Vehicle",
        back_populates="ai_route_optimizations"
    )

    employee = relationship(
        "Employee",
        back_populates="ai_route_optimizations"
    )