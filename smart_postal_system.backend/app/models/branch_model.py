from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.database import Base


class Branch(Base):

    __tablename__ = "branches"

    branch_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    branch_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    branch_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    contact_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    manager_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    vehicles = relationship(
        "Vehicle",
        back_populates="branch",
    )
    tracking_history = relationship(
        "TrackingHistory",
        back_populates="branch",
    )
    routes_starting = relationship(
        "Route",
        foreign_keys="[Route.start_branch_id]",
        back_populates="start_branch",
    )
    routes_ending = relationship(
        "Route",
        foreign_keys="[Route.end_branch_id]",
        back_populates="end_branch",
    )