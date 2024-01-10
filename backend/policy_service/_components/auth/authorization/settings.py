from enum import Enum

from pydantic import BaseSettings


class Environment(Enum):
    DEV = "dev"
    PROD = "prod"
    LOCAL = "local"


class Settings(BaseSettings):
    # General settings.
    env: Environment = Environment.DEV

    class Config:
        env_file = ".env"


env = Settings()
