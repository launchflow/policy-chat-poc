"""Define all our models for our storage layer.

These models construct the tables in our database.
"""


from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Association table for the many-to-many relationship between User IDs and Roles
user_role_association = Table(
    "user_role",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
)


class StorageRole(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    # Relationships
    permissions = relationship(
        "Permission", secondary="role_permission", back_populates="roles"
    )


role_permission_association = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
)


class StoragePermission(Base):
    __tablename__ = "permission"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    # Relationships
    roles = relationship(
        "Role", secondary="role_permission", back_populates="permissions"
    )
