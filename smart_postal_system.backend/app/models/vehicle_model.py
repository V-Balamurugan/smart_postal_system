from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.database import Base


class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Vehicle(Base):

    __tablename__ = "vehicles"

    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    vehicle_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    capacity_kg: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    current_branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.branch_id"),
        nullable=False,
    )

    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=True,
    )

    fuel_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[VehicleStatus] = mapped_column(
        SqlEnum(VehicleStatus),
        default=VehicleStatus.AVAILABLE,
    )

    current_latitude: Mapped[float | None] = mapped_column(
        Float,
    )

    current_longitude: Mapped[float | None] = mapped_column(
        Float,
    )

    last_service_date: Mapped[date | None] = mapped_column(
        Date,
    )

    insurance_expiry: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    registration_expiry: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    branch = relationship(
        "Branch",
        back_populates="vehicles",
    )

    driver = relationship(
        "Employee",
        back_populates="vehicles",
    )
    ai_route_optimizations = relationship(
        "AIRouteOptimization",
        back_populates="vehicle"
    )