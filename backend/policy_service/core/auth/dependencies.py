from buildflow import Service
from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.headers import BearerCredentials
from buildflow.exceptions import HTTPException
from buildflow.requests import Request
from policy_service._components.auth.authentication.component import (
    AuthenticationComponentBuilder,
)
from policy_service.core.primitives import cloud_sql_auth_database, cloud_sql_auth_user

# Define a separate service container for our auth extension.
auth_service = Service(base_route="/auth", service_id="auth-service")

Authentication = AuthenticationComponentBuilder(
    auth_service, cloud_sql_auth_database, cloud_sql_auth_user
)


@dependency(scope=Scope.PROCESS)
class AuthenticatedRequest:
    async def __init__(
        self,
        request: Request,
        bearer_credentials: BearerCredentials,
        auth: Authentication,
    ):
        access_token = bearer_credentials.token
        if access_token is None:
            raise HTTPException(401)
        self.user = await auth.authenticate_user(access_token)
        self.request = request
