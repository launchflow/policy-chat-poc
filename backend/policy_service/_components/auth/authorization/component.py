import uuid

from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.sqlalchemy import engine
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser

from components.auth.authorization.storage.dependencies import (
    AuthorizationStorageBuilder,
)
from components.auth.authorization.storage.models import (
    Base,
    StoragePermission,
    StorageRole,
    role_permission_association,
    user_role_association,
)


def AuthorizationComponentBuilder(
    cloud_sql_database: CloudSQLDatabase, cloud_sql_user: CloudSQLUser
):
    AuthorizationStorage = AuthorizationStorageBuilder(
        cloud_sql_database, cloud_sql_user
    )

    # NOTE: There's a try catch to handle the case where the infra create step is
    # running. Might be nice if we could check the env if its a infra create step
    # and throw an error if its not.
    try:
        Base.metadata.drop_all(
            bind=engine(
                cloud_sql_database, cloud_sql_user.user_name, cloud_sql_user.password
            ),
            tables=[
                StoragePermission.__table__,
                StorageRole.__table__,
                role_permission_association,
                user_role_association,
            ],
        )
        Base.metadata.create_all(
            bind=engine(
                cloud_sql_database, cloud_sql_user.user_name, cloud_sql_user.password
            ),
            tables=[
                StoragePermission.__table__,
                StorageRole.__table__,
                role_permission_association,
                user_role_association,
            ],
        )
    except Exception as e:
        print("Failed to drop / create tables: ", e)
        pass

    @dependency(scope=Scope.PROCESS)
    class AuthorizationConsumer:
        async def __init__(self, storage: AuthorizationStorage):
            # Private attributes
            self._storage = storage

        async def check_permission(
            self, *, user_id: uuid.UUID, permission: str
        ) -> bool:
            roles = await self._storage.get_roles_for_user(user_id=user_id)
            for role in roles:
                permissions = await self._storage.get_permissions_for_role(
                    ole_name=role.name
                )
                for role_permission in permissions:
                    if role_permission.name == permission:
                        return True
            return False

        async def assign_role_to_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            await self._storage.assign_role_to_user(
                user_id=user_id, role_name=role_name
            )

        async def remove_role_from_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            await self._storage.remove_role_from_user(
                user_id=user_id, role_name=role_name
            )

    @dependency(scope=Scope.PROCESS)
    class AuthorizationAdmin:
        async def __init__(self, storage: AuthorizationStorage):
            # Private attributes
            self._storage = storage

        async def create_role(self, *, role_name: str) -> None:
            await self._storage.create_role(role_name=role_name)

        async def add_permission_to_role(
            self, *, role_name: str, permission_name: str
        ) -> None:
            await self._storage.add_permission_to_role(
                role_name=role_name, permission_name=permission_name
            )

        async def assign_role_to_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            await self._storage.assign_role_to_user(
                user_id=user_id, role_name=role_name
            )

        async def remove_role_from_user(
            self, *, user_id: uuid.UUID, role_name: str
        ) -> None:
            await self._storage.remove_role_from_user(
                user_id=user_id, role_name=role_name
            )

    @dependency(scope=Scope.NO_SCOPE)
    class AuthorizationComponent:
        def __init__(self, consumer: AuthorizationConsumer, admin: AuthorizationAdmin):
            self.consumer = consumer
            self.admin = admin

    return AuthorizationComponent
