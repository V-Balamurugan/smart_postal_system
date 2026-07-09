from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class TrackingHistory(Base):
    __tablename__ = "tracking_history"

    tracking_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    parcel_id: Mapped[int] = mapped_column(
        ForeignKey(
            "parcels.parcel_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "employees.employee_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    branch_id: Mapped[int] = mapped_column(
        ForeignKey(
            "branches.branch_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships

    parcel: Mapped["Parcel"] = relationship(
        "Parcel",
        back_populates="tracking_history",
    )

    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="tracking_history",
    )

    branch: Mapped["Branch"] = relationship(
        "Branch",
        back_populates="tracking_history",
    )

    __table_args__ = (
        Index("idx_tracking_parcel", "parcel_id"),
        Index("idx_tracking_employee", "employee_id"),
        Index("idx_tracking_branch", "branch_id"),
        Index("idx_tracking_status", "status"),
        Index("idx_tracking_created_at", "created_at"),
    )