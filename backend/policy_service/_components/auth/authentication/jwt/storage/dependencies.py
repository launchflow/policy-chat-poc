import datetime
import uuid
from typing import List

from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.sqlalchemy import AsyncSessionDepBuilder, engine
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser
from sqlalchemy.future import select

from policy_service._components.auth.authentication.exceptions import (
    RefreshTokenNotFound,
    UserNotFound,
)
from policy_service._components.auth.authentication.jwt.storage.models import (
    Base,
    StorageRefreshToken,
    StorageUser,
)


def AuthStorageBuilder(db_primitive: CloudSQLDatabase, db_user: CloudSQLUser):
    AsyncPostgres = AsyncSessionDepBuilder(
        db_primitive=db_primitive,
        db_user=db_user.user_name,
        db_password=db_user.password,
        pool_size=5,
        max_overflow=10,
        pool_recycle=600,
    )

    # NOTE: There's a try catch to handle the case where the infra create step is
    # running. Might be nice if we could check the env if its a infra create step
    # and throw an error if its not.
    try:
        Base.metadata.drop_all(
            bind=engine(db_primitive, db_user.user_name, db_user.password),
            tables=[
                StorageRefreshToken.__table__,
                StorageUser.__table__,
            ],
        )
        Base.metadata.create_all(
            bind=engine(db_primitive, db_user.user_name, db_user.password),
            tables=[
                StorageRefreshToken.__table__,
                StorageUser.__table__,
            ],
        )
    except Exception as e:
        print("Failed to drop / create tables: ", e)
        pass

    @dependency(scope=Scope.PROCESS)
    class AuthenticationStorage:
        async def __init__(self, postgres: AsyncPostgres):
            # TODO: right now each method is opening and closing the connection, but we
            # may want to keep the connection open for multiple method calls. We should
            # have the caller commit or register a callback or something.
            # Should probably find a way to do this using a context manager. <-- DO THIS APPROACH
            self.db = postgres.session
            # TODO: Implement a cache using a ray actor.
            # Right now we are hammering the user table on every request.
            self.cache = {}

        async def create_storage_user(
            self, *, email: str, name: str, google_id: str = None, github_id: str = None
        ) -> StorageUser:
            user = StorageUser(
                email=email, name=name, google_id=google_id, github_id=github_id
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.close()
            return user

        async def get_storage_user(self, *, user_id: str) -> StorageUser:
            stmt = select(StorageUser).where(StorageUser.id == uuid.UUID(user_id))
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            await self.db.close()
            if user is None:
                raise UserNotFound()
            return user

        async def lookup_storage_user(
            self, *, email: str | None, google_id: str | None, github_id: str | None
        ) -> StorageUser:
            where_clauses = []
            if email is not None:
                where_clauses.append(StorageUser.email == email)
            if google_id is not None:
                where_clauses.append(StorageUser.google_id == google_id)
            if github_id is not None:
                where_clauses.append(StorageUser.github_id == github_id)
            if len(where_clauses) == 0:
                raise ValueError("Must provide at least one lookup field")

            stmt = select(StorageUser).where(*where_clauses)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            await self.db.close()
            if user is None:
                raise UserNotFound()
            return user

        async def create_storage_refresh_token(
            self,
            *,
            token_hash: str,
            user_id: str,
            expires_at: datetime.datetime,
            user_agent: str,
            ip_address: str,
        ) -> StorageRefreshToken:
            refresh_token = StorageRefreshToken(
                token_hash=token_hash,
                user_id=uuid.UUID(user_id),
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            self.db.add(refresh_token)
            await self.db.commit()
            await self.db.close()
            return refresh_token

        async def lookup_storage_refresh_token_by_hash(
            self, *, token_hash: str
        ) -> StorageRefreshToken:
            stmt = select(StorageRefreshToken).where(
                StorageRefreshToken.token_hash == token_hash
            )
            result = await self.db.execute(stmt)
            refresh_token = result.scalar_one_or_none()
            await self.db.close()
            if refresh_token is None:
                raise RefreshTokenNotFound()
            return refresh_token

        # NOTE: This function is not used in the template, but is included for
        # completeness.
        # This function should be used if you ever need to revoke all refresh tokens for
        # a user (e.g. if they change their password).
        async def lookup_active_storage_refresh_tokens_for_user(
            self, *, user_id: int
        ) -> List[StorageRefreshToken]:
            stmt = select(StorageRefreshToken).where(
                StorageRefreshToken.user_id == user_id,
                StorageRefreshToken.is_revoked is False,
            )
            result = await self.db.execute(stmt)
            refresh_tokens = result.scalars().all()
            await self.db.close()
            return refresh_tokens

    return AuthenticationStorage
