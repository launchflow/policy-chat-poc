import logging
from dataclasses import dataclass
from typing import Optional

from buildflow.dependencies import Scope, dependency
from buildflow.exceptions import HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib import flow as google_auth_flow
from googleapiclient.errors import HttpError

from policy_service.settings import env

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@dataclass
class GoogleUser:
    google_account_id: str
    email: str
    email_verified: bool = False
    name: Optional[str] = None


def GoogleOAuthFlowBuilder(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scopes: list[str] = SCOPES,
):
    @dependency(scope=Scope.REPLICA)
    class GoogleOAuthFlow:
        def __init__(self):
            self._client = google_auth_flow.Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": [redirect_uri],
                        "javascript_origins": "http://localhost:8000",
                    }
                },
                scopes=scopes,
            )
            print("\n\nredirect_uri", redirect_uri)
            self._client.redirect_uri = redirect_uri

        def google_login_url(self) -> str:
            return self._client.authorization_url(
                include_granted_scopes="true",
                approval_prompt="force",
            )[0]

        def google_info(self, code: str) -> GoogleUser:
            print("\n\ncode", code)
            auth_token_info = dict(self._client.fetch_token(code=code))
            try:
                google_token_info = id_token.verify_oauth2_token(
                    auth_token_info["id_token"], requests.Request()
                )
                if google_token_info["iss"] not in [
                    "accounts.google.com",
                    "https://accounts.google.com",
                ]:
                    raise HTTPException(status_code=401, detail="Wrong issuer.")
                if google_token_info["aud"] not in [client_id]:
                    raise HTTPException(status_code=401, detail="Wrong audience.")
                if not google_token_info["email_verified"]:
                    raise HTTPException(403, "email is not verified")

                return GoogleUser(
                    google_account_id=google_token_info["sub"],
                    email=google_token_info["email"],
                    name=google_token_info.get("name"),
                    email_verified=google_token_info["email_verified"],
                )

            except HttpError as e:
                logging.exception("Failed to verify token")
                raise HTTPException(status_code=401, detail=str(e))

    return GoogleOAuthFlow


def OAuthFlowBuilder():
    GoogleOAuthFlow = GoogleOAuthFlowBuilder(
        env.google_oauth_client_id,
        env.google_oauth_client_secret,
        env.google_oauth_redirect_uri,
    )

    @dependency(scope=Scope.REPLICA)
    class OAuthFlow:
        def __init__(self, google_oauth: GoogleOAuthFlow):
            self._google_oauth = google_oauth

        def google_login_url(self) -> str:
            return self._google_oauth.google_login_url()

        def google_info(self, code: str) -> GoogleUser:
            return self._google_oauth.google_info(code=code)

    return OAuthFlow
