from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"

    assignment_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    parcel_id = Column(
        Integer,
        ForeignKey("parcels.parcel_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    assignment_status = Column(
        String(30),
        nullable=False,
        default="ASSIGNED"
    )

    priority = Column(
        String(20),
        nullable=False,
        default="MEDIUM"
    )

    remarks = Column(
        Text,
        nullable=True
    )

    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ---------------- Relationships ---------------- #

    parcel = relationship(
        "Parcel",
        back_populates="delivery_assignment"
    )

    employee = relationship(
        "Employee",
        back_populates="delivery_assignments"
    )

    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_by],
        back_populates="delivery_assignments"
    )