from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Route(Base):
    __tablename__ = "routes"

    route_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    route_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    start_branch_id: Mapped[int] = mapped_column(
<<<<<<< HEAD
        ForeignKey("branches.branch_id", ondelete="CASCADE"),
=======
        ForeignKey("branches.id", ondelete="CASCADE"),
>>>>>>> fbe67239cd358e5338da41924b95b8f47875abbc
        nullable=False,
    )

    end_branch_id: Mapped[int] = mapped_column(
<<<<<<< HEAD
        ForeignKey("branches.branch_id", ondelete="CASCADE"),
=======
        ForeignKey("branches.id", ondelete="CASCADE"),
>>>>>>> fbe67239cd358e5338da41924b95b8f47875abbc
        nullable=False,
    )

    distance_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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
    start_branch = relationship(
        "Branch",
        foreign_keys=[start_branch_id],
        back_populates="routes_starting",
    )

    end_branch = relationship(
        "Branch",
        foreign_keys=[end_branch_id],
        back_populates="routes_ending",
    )
