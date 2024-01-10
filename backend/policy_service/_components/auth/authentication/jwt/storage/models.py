"""Define all our models for our storage layer.

These models construct the tables in our database.
"""

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class StorageUser(Base):
    __tablename__ = "users"

    # Autopoluated fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # User info
    email = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)

    # Security fields
    google_id = Column(String, index=True, nullable=True)
    github_id = Column(String, index=True, nullable=True)


class StorageRefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # Autopoluated fields
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Refresh token info
    token_hash = Column(String(512), unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    user_agent = Column(Text)  # User agent string can be quite long
    ip_address = Column(String(45))  # IPv6 addresses can be up to 45 chars

    # TODO: Consider adding other fields for more enhanced tracking or security measures
    # e.g., location, device fingerprint, etc.

    # Indicies
    __table_args__ = (
        # NOTE: we use this index to quickly find active refresh tokens for a user
        # so we can revoke them when a user changes their password, verifies their
        # email, etc
        Index(
            "idx_active_tokens",
            "user_id",
            unique=False,
            postgresql_where=(is_revoked is False),
        ),
    )
