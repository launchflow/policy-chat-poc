"""Define all our models for our storage layer.

These models construct the tables in our database.
"""

import datetime
import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class StorageAccount(Base):
    __tablename__ = "accounts"

    # Autopoluated fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Account info
    storage_bucket_dir = Column(String, nullable=False)

    # User info
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    user_name = Column(String, nullable=False)


class PolicyType(enum.Enum):
    AUTO = "Auto"
    HOME = "Home"
    RENTERS = "Renters"
    LIFE = "Life"
    HEALTH = "Health"
    BUSINESS = "Business"
    PET = "Pet"
    BOAT = "Boat"
    MOTORCYCLE = "Motorcycle"


class StoragePolicy(Base):
    __tablename__ = "policies"

    # Autopoluated fields
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Foreign keys
    account_id = Column(UUID, ForeignKey("accounts.id"), index=True)

    # Policy info
    policy_id = Column(String, nullable=False, unique=True, primary_key=True)
    policy_type = Column(Enum(PolicyType), nullable=False)
    policy_holder = Column(String, nullable=False)

    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False)
