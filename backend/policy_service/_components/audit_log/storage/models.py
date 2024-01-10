"""Define all our models for our storage layer.

These models construct the tables in our database.
"""


from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class AuditLogEvent(Base):
    __tablename__ = "audit_log_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    resource_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSONB, nullable=False)
