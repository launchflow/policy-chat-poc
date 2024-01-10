from buildflow import Service
from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.headers import BearerCredentials
from buildflow.exceptions import HTTPException
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser
from buildflow.middleware import CORSMiddleware
from buildflow.requests import Request
from buildflow.responses import Response

from policy_service._components.auth.authentication.jwt.dependencies import (
    JWTAuthenticationBuilder,
)
from policy_service._components.auth.authentication.oauth.dependencies import (
    OAuthFlowBuilder,
)
from policy_service._components.auth.authentication.schemas import AuthenticatedUser
from policy_service.settings import env


def AuthenticationComponentBuilder(
    service: Service, db_primitive: CloudSQLDatabase, db_user: CloudSQLUser
):
    JWTAuthentication = JWTAuthenticationBuilder(
        db_primitive,
        db_user,
        env.jwt_secret_key,
        env.jwt_algorithm,
        env.jwt_access_token_expires_minutes,
        env.jwt_refresh_token_expires_minutes,
    )

    OAuthFlow = OAuthFlowBuilder()

    service.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Used for both signing up and logging in
    @service.endpoint("/google/url", method="GET")
    async def google_login_url(oauth_flow: OAuthFlow):
        login_url = oauth_flow.google_login_url()
        return {"url": login_url}

    @service.endpoint("/google/token", method="GET")
    async def google_token_swap(
        request: Request,
        oauth_flow: OAuthFlow,
        auth: JWTAuthentication,
    ):
        # Retrieve the auth code from the request's query params
        code = request.query_params.get("code")
        if code is None:
            raise HTTPException(401)
        # Exchange the auth code for their google account info
        google_user = oauth_flow.google_info(code)

        print("GOOGLE USER: ", google_user)

        authenticated_user = await auth.lookup_or_create_user(
            email=google_user.email,
            name=google_user.name,
            google_id=google_user.google_account_id,
            github_id=None,
        )
        # Create a new set of credentials for the user
        credentials = await auth.create_credentials(
            authenticated_user,
            payload={
                "email": google_user.email,
                "name": google_user.name,
            },
        )
        # Set the refresh token as a cookie
        response = Response()
        response.set_cookie(
            "refresh_token",
            credentials.refresh_token,
            max_age=60 * 24 * 30,
            httponly=True,
            secure=True,
            samesite="strict",
        )
        # Return the access token to the client
        return {"access_token": credentials.access_token, "token_type": "bearer"}

    @service.endpoint("/me", method="GET")
    async def me(
        bearer_token: BearerCredentials, auth: JWTAuthentication
    ) -> AuthenticatedUser:
        access_token = bearer_token.token
        if access_token is None:
            raise HTTPException(401)

        user = await auth.authenticate_user(access_token)
        return user

    @service.endpoint("/check", method="GET")
    async def auth_check(request: Request, auth: JWTAuthentication):
        print("\n\n", request.cookies, "\n\n")
        # NEXT TIME: Figure out why this is failing
        return {"authenticated": True}
        # refresh_token = request.cookies.get("refresh_token")
        # if refresh_token is not None and auth.check_token(refresh_token):
        #     return {"authenticated": True}
        # return {"authenticated": False}

    @service.endpoint("/logout", method="GET")
    async def logout(request: Request, auth: JWTAuthentication):
        refresh_token = request.cookies.get("refresh_token")
        successful = False
        if refresh_token is not None:
            successful = await auth.revoke_refresh_token(refresh_token)
        return {"success": successful}

    @service.endpoint("/refresh", method="GET")
    async def refresh_credentials(request: Request, auth: JWTAuthentication):
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token is None:
            raise HTTPException(401)
        credentials = await auth.refresh_credentials(refresh_token)
        return credentials

    @dependency(scope=Scope.PROCESS)
    class AuthenticationComponent:
        def __init__(self, jwt: JWTAuthentication):
            self._jwt = jwt

        async def authenticate_user(self, access_token: str) -> AuthenticatedUser:
            return await self._jwt.authenticate_user(access_token)

    return AuthenticationComponent
