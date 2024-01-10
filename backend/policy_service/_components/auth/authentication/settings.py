from enum import Enum

from pydantic import BaseSettings


class Environment(Enum):
    DEV = "dev"
    PROD = "prod"
    LOCAL = "local"


class Settings(BaseSettings):
    # General settings.
    env: Environment = Environment.DEV

    # User Auth / JWT settings.
    jwt_access_token_expires_minutes = 30
    jwt_refresh_token_expires_minutes = 60 * 24 * 30
    jwt_algorithm = "HS256"
    # You can generate a new secret with command: `openssl rand -hex 32`
    jwt_secret_key = "8e1ccf6808f486522f70ff1d8742e355d2c61d48d7d414cfbfaf9ff9ee41a46d"

    # Google OAuth settings.
    google_oauth_client_id: str = "TODO"
    google_oauth_client_secret: str = "TODO"
    google_oauth_redirect_uri: str = "http://localhost:3001/auth/google/callback"

    # Github OAuth settings
    github_oauth_client_id: str = "TODO"
    github_oauth_client_secret: str = "TODO"

    class Config:
        env_file = ".env"


env = Settings()
