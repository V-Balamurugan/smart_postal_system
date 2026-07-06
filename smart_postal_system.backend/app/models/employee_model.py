from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    employee_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    designation = Column(
        String(100),
        nullable=False,
    )

    branch = Column(
        String(100),
        nullable=False,
    )

    vehicle_type = Column(
        String(50),
        nullable=True,
    )

    vehicle_number = Column(
        String(30),
        unique=True,
        nullable=True,
    )

    latitude = Column(
        Float,
        nullable=True,
    )

    longitude = Column(
        Float,
        nullable=True,
    )

    is_available = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    current_workload = Column(
        Integer,
        default=0,
        nullable=False,
    )

    max_workload = Column(
        Integer,
        default=20,
        nullable=False,
    )

    status = Column(
        String(30),
        default="ACTIVE",
        nullable=False,
    )

    joining_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # One-to-One Relationship with User
    user = relationship(
        "User",
        back_populates="employee",
        uselist=False,
        passive_deletes=True,
    )

    delivery_assignments = relationship(
        "DeliveryAssignment",
        back_populates="employee",
        cascade="all, delete-orphan"
    )
    vehicles = relationship(
        "Vehicle",
        back_populates="driver",
    )