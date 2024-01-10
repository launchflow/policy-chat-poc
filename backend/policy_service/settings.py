from enum import Enum
from typing import FrozenSet

import resend
import stripe
from pydantic import BaseSettings


class Environment(Enum):
    DEV = "dev"
    PROD = "prod"
    LOCAL = "local"


class Settings(BaseSettings):
    # General settings.
    env: Environment = Environment.DEV

    # Admin settings
    admin_emails: FrozenSet[str] = frozenset(["TODO"])

    # Anyscale Endpoints settings.
    anyscale_base_url = "https://api.endpoints.anyscale.com/v1"
    anyscale_api_key = "TODO"

    # User Auth / JWT settings.
    jwt_access_token_expires_minutes = 30
    jwt_refresh_token_expires_minutes = 60 * 24 * 30
    jwt_algorithm = "HS256"
    # You can generate a new secret with command: `openssl rand -hex 32`
    jwt_secret_key = "aae9c93a2065d8bd7ed27a308026bd1ae97d1a4a6fe9dafd0c623f04134ba472"

    # Google OAuth settings.
    google_oauth_client_id: str = "TODO"
    google_oauth_client_secret: str = "TODO"
    google_oauth_redirect_uri: str = "http://localhost:3001/auth/google/callback"

    # Github OAuth settings
    github_oauth_client_id: str = "TODO"
    github_oauth_client_secret: str = "TODO"

    # CloudSQL (Postgres) settings
    gcp_project_id: str = "TODO"
    db_user: str = "postgres"
    db_password: str = "postgres"
    create_db_models: bool = False

    # Stripe webhook secret: When running locally, you need to use the strip
    # cli to run `stripe listen --forward-to localhost:3001/billing/webhook`
    # to generate this.
    stripe_api_key: str = "TODO"
    stripe_webhook_signing_secret: str = "TODO"

    # PostHog settings
    posthog_api_key: str = "TODO"

    # Resend settings
    resend_api_key: str = "TODO"

    # Zapier settings
    zapier_webhook_url: str = "TODO"
    zapier_webhook_secret: str = "TODO"

    # Slack LaunchBot settings
    slack_auth_token: str = "TODO"
    slack_events_channel: str = "#events"

    class Config:
        env_file = ".env"


env = Settings()

if env.stripe_api_key:
    stripe.api_key = env.stripe_api_key
if env.resend_api_key:
    resend.api_key = env.resend_api_key
