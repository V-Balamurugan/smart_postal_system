from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Parcel(Base):
    __tablename__ = "parcels"

    parcel_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    tracking_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    receiver_name = Column(
        String(100),
        nullable=False
    )

    receiver_phone = Column(
        String(15),
        nullable=False
    )

    receiver_email = Column(
        String(100),
        nullable=True
    )

    pickup_address = Column(
        Text,
        nullable=False
    )

    delivery_address = Column(
        Text,
        nullable=False
    )

    source_branch = Column(
        String(100),
        nullable=False
    )

    destination_branch = Column(
        String(100),
        nullable=False
    )

    category_id = Column(
        Integer,
        nullable=True
    )

    weight = Column(
        Float,
        nullable=False
    )

    parcel_value = Column(
        Float,
        nullable=False
    )

    priority_level = Column(
        String(20),
        nullable=False,
        default="NORMAL"
    )

    status = Column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    booking_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    expected_delivery = Column(
        DateTime(timezone=True),
        nullable=True
    )

    actual_delivery = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # -------------------------
    # Relationships
    # -------------------------

    delivery_assignment = relationship(
        "DeliveryAssignment",
        back_populates="parcel",
        uselist=False,
        cascade="all, delete-orphan"
    )
    tracking_history = relationship(
        "TrackingHistory",
        back_populates="parcel",
        cascade="all, delete-orphan",
    )