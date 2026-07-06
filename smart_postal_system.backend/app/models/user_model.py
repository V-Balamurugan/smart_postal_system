from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    full_name = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    phone = Column(
        String(15),
        unique=True,
        nullable=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
        default="CUSTOMER",
    )

    address = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # One-to-One Relationship with Employee
    employee = relationship(
        "Employee",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )