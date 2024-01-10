import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

from buildflow.dependencies import Scope, dependency
from buildflow.exceptions import HTTPException
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser
from buildflow.requests import Request
from jose import ExpiredSignatureError, JWTError, jwt
from policy_service._components.auth.authentication.exceptions import (
    ExpiredTokenError,
    RefreshTokenNotFound,
    UserNotFound,
)
from policy_service._components.auth.authentication.jwt.storage.dependencies import (
    AuthStorageBuilder,
)
from policy_service._components.auth.authentication.schemas import (
    AuthenticatedUser,
    Credentials,
)


def JWTAuthenticationBuilder(
    db_primitive: CloudSQLDatabase,
    db_user: CloudSQLUser,
    jwt_secret_key: str,
    jwt_algorithm: str,
    jwt_access_expires_minutes: int,
    jwt_refresh_expires_minutes: int,
):
    AuthStorage = AuthStorageBuilder(db_primitive, db_user)

    @dependency(scope=Scope.PROCESS)
    class JWTAuthentication:
        async def __init__(
            self,
            request: Request,
            storage: AuthStorage,
        ):
            # Private attributes
            self._request = request
            self._storage = storage

        async def authenticate_user(self, access_token: str) -> AuthenticatedUser:
            credentials_exception = HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            try:
                payload = self._decode_token(access_token)
                user_id: str = payload.get("sub")
                print("\n\n\nUSER ID: ", user_id)

                if user_id is None:
                    raise credentials_exception

                storage_user = await self._storage.get_storage_user(user_id=user_id)
                print("\n\n\nSTORAGE USER: ", storage_user)

                return AuthenticatedUser(
                    user_id=str(storage_user.id),
                    email=storage_user.email,
                    name=storage_user.name,
                )

            except ExpiredTokenError as e:
                raise e

        async def lookup_or_create_user(
            self,
            email: str | None,
            name: str | None,
            google_id: str | None,
            github_id: str | None,
        ) -> AuthenticatedUser:
            try:
                storage_user = await self._storage.lookup_storage_user(
                    email=email, google_id=google_id, github_id=github_id
                )
            except UserNotFound:
                storage_user = await self._storage.create_storage_user(
                    email=email,
                    name=name or "Anonymous User",
                    google_id=google_id,
                    github_id=github_id,
                )

            return AuthenticatedUser(
                user_id=str(storage_user.id),
                email=storage_user.email,
                name=storage_user.name,
            )

        async def create_credentials(
            self, authenticated_user: AuthenticatedUser, payload: Optional[dict] = None
        ) -> Credentials:
            # Create the access token
            access_token, access_expires_at = self._create_access_token(
                authenticated_user.user_id, payload
            )
            # Create and store the refresh token
            refresh_token, refresh_expires_at = self._create_refresh_token(
                authenticated_user.user_id, payload
            )
            refresh_token_hash = self._hash_token(refresh_token)
            storage_refresh_token = await self._storage.create_storage_refresh_token(
                token_hash=refresh_token_hash,
                user_id=authenticated_user.user_id,
                expires_at=refresh_expires_at,
                user_agent=self._request.headers.get("User-Agent"),
                ip_address=self._request.client.host,
            )

            return Credentials(
                access_token=access_token,
                access_expires_at=access_expires_at,
                refresh_token=refresh_token,
                refresh_expires_at=refresh_expires_at,
            )

        async def refresh_credentials(self, refresh_token: str) -> Credentials:
            credentials_exception = HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

            try:
                payload = self._decode_token(refresh_token)
                user_id: str = payload.get("sub")

                if user_id is None:
                    raise credentials_exception

                storage_user = await self._storage.get_storage_user(user_id=user_id)
                user = AuthenticatedUser(
                    user_id=str(storage_user.id),
                    email=storage_user.email,
                    name=storage_user.name,
                )

                refresh_token_hash = self._hash_token(refresh_token)
                storage_refresh_token = (
                    await self._storage.lookup_storage_refresh_token_by_hash(
                        token_hash=refresh_token_hash,
                    )
                )

                if storage_refresh_token.is_revoked:
                    raise credentials_exception

                credentials = await self.create_credentials(
                    user_id=user.user_id,
                    payload={
                        "email": user.email,
                        "name": user.name,
                    },
                )

                refresh_token_hash = self._hash_token(credentials.refresh_token)
                storage_refresh_token = (
                    await self._storage.create_storage_refresh_token(
                        token_hash=refresh_token_hash,
                        user_id=user.user_id,
                        expires_at=credentials.refresh_expires_at,
                        user_agent=self._request.headers.get("User-Agent"),
                        ip_address=self._request.client.host,
                    )
                )

                await self._storage.db.commit()

                return credentials

            except Exception as e:
                raise e

        async def revoke_refresh_token(self, refresh_token: str) -> bool:
            refresh_token_hash = self._hash_token(refresh_token)
            try:
                storage_refresh_token = (
                    await self._storage.lookup_storage_refresh_token_by_hash(
                        token_hash=refresh_token_hash
                    )
                )
            except RefreshTokenNotFound:
                return True
            except Exception:
                return False

            # invalidate the refresh token when the user logs out
            storage_refresh_token.is_revoked = True
            await self._storage.db.commit()

            return True

        def check_token(self, token: str):
            try:
                payload = self._decode_token(token)
                return True
            except Exception:
                return False

        def _create_access_token(self, sub: str, payload: Optional[dict] = None):
            access_expires_at = datetime.utcnow() + timedelta(
                minutes=jwt_access_expires_minutes
            )
            to_encode = {
                "sub": sub,
                "exp": access_expires_at,
                "type": "access",
                "jti": str(uuid.uuid4()),
            }
            if payload is not None:
                to_encode["payload"] = payload
            return (
                jwt.encode(to_encode, jwt_secret_key, algorithm=jwt_algorithm),
                access_expires_at,
            )

        def _create_refresh_token(self, sub: str, payload: Optional[dict] = None):
            refresh_expires_at = datetime.utcnow() + timedelta(
                minutes=jwt_refresh_expires_minutes
            )
            to_encode = {
                "sub": sub,
                "exp": refresh_expires_at,
                "type": "refresh",
                "jti": str(uuid.uuid4()),
            }
            if payload is not None:
                to_encode["payload"] = payload
            return (
                jwt.encode(to_encode, jwt_secret_key, algorithm=jwt_algorithm),
                refresh_expires_at,
            )

        def _decode_token(self, token: str):
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret_key,
                    algorithms=jwt_algorithm,
                )
                return payload
            except ExpiredSignatureError:
                raise ExpiredTokenError()
            except JWTError:
                raise HTTPException(
                    status_code=401,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        def _hash_token(self, token: str):
            return hashlib.sha256(token.encode("utf-8")).hexdigest()

    return JWTAuthentication
