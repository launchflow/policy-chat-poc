import datetime
import re
import uuid
from typing import List

from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.sqlalchemy import AsyncSessionDepBuilder
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser
from sqlalchemy.future import select

from components.auth.authorization.exceptions import InvalidRole, RoleNotFound
from components.auth.authorization.storage.models import (
    StoragePermission,
    StorageRole,
    role_permission_association,
    user_role_association,
)


def _validate_role_name(role_name: str) -> None:
    # role_name must match the pattern roles/{entity}.{access}
    regex_pattern = r"^roles\/[a-z]+.[a-z]+$"
    if not re.match(regex_pattern, role_name):
        raise InvalidRole()


def _validate_role_permission_name(role_name: str, permission_name: str) -> None:
    entity, resource, action = permission_name.split(".")
    role_entity, role_action = role_name.split(".")
    if entity != role_entity.split("/")[1]:
        raise InvalidRole()
    # permission_name must match the pattern {entity}.{resource}.{action}
    regex_pattern = r"^[a-z]+.[a-z]+.[a-z]+$"
    if not re.match(regex_pattern, permission_name):
        raise InvalidRole()


def AuthorizationStorageBuilder(db_primitive: CloudSQLDatabase, db_user: CloudSQLUser):
    AsyncPostgres = AsyncSessionDepBuilder(
        db_primitive=db_primitive,
        db_user=db_user.user_name,
        db_password=db_user.password,
        pool_size=5,
        max_overflow=10,
        pool_recycle=600,
    )

    @dependency(scope=Scope.PROCESS)
    class AuthorizationStorage:
        async def __init__(self, postgres: AsyncPostgres):
            # TODO: right now each method is opening and closing the connection, but we
            # may want to keep the connection open for multiple method calls. We should
            # have the caller commit or register a callback or something.
            # Should probably find a way to do this using a context manager. <-- DO THIS APPROACH
            self.db = postgres.session
            # TODO: Implement a cache using a ray actor.
            # Right now we are hammering the user table on every request.
            self.cache = {}

        async def create_role(
            self, *, role_name: str, permissions: List[str]
        ) -> StorageRole:
            _validate_role_name(role_name)
            for perm_name in permissions:
                _validate_role_permission_name(role_name, perm_name)

            role = StorageRole(name=role_name)
            self.db.add(role)
            await self.db.commit()
            await self.db.close()
            return role

        async def get_role_by_name(self, *, role_name: str) -> StorageRole:
            stmt = select(StorageRole).where(StorageRole.name == role_name)
            result = await self.db.execute(stmt)
            role = result.scalar_one_or_none()
            if role is None:
                raise RoleNotFound()
            return role

        async def add_permission_to_role(
            self, *, role_name: str, permission_name: str
        ) -> None:
            _validate_role_permission_name(role_name, permission_name)
            role = await self.get_role_by_name(role_name=role_name)

            if any(perm.name == permission_name for perm in role.permissions):
                return

            stmt = select(StoragePermission).where(
                StoragePermission.name == permission_name
            )
            result = await self.db.execute(stmt)
            permission = result.scalar_one_or_none()

            if permission is None:
                permission = StoragePermission(name=permission_name)
                self.db.add(permission)
                await self.db.commit()

            role.permissions.append(permission)
            await self.db.commit()

        async def assign_role_to_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            role = await self.get_role_by_name(role_name=role_name)
            insert_stmt = user_role_association.insert().values(
                user_id=user_id, role_id=role.id
            )
            await self.db.execute(insert_stmt)
            await self.db.commit()

        async def remove_role_from_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            role = await self.get_role_by_name(role_name=role_name)
            delete_stmt = user_role_association.delete().where(
                user_role_association.c.user_id == user_id,
                user_role_association.c.role_id == role.id,
            )
            await self.db.execute(delete_stmt)
            await self.db.commit()

        async def get_roles_for_user(
            self,
            *,
            user_id: uuid.UUID,
        ) -> List[StorageRole]:
            stmt = (
                select(StorageRole)
                .join(user_role_association)
                .where(user_role_association.c.user_id == user_id)
            )
            result = await self.db.execute(stmt)
            roles = result.scalars().all()
            return roles

        async def get_permissions_for_role(
            self, *, role_name: str
        ) -> List[StoragePermission]:
            role = await self.get_role_by_name(role_name=role_name)
            stmt = (
                select(StoragePermission)
                .join(role_permission_association)
                .where(role_permission_association.c.role_id == role.id)
            )
            result = await self.db.execute(stmt)
            permissions = result.scalars().all()
            return permissions

    return AuthorizationStorage
