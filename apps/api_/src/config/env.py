import os
from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional

class NodeEnv(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"

class Settings(BaseSettings):
    NODE_ENV: NodeEnv = NodeEnv.DEVELOPMENT
    PORT: int = 8080
    # Make DATABASE_URL optional to allow app to start without DB configured
    DATABASE_URL: Optional[str] = None
    CORS_ORIGIN: str = "*"
    ARCHIVE_AFTER_MIN: int = 30
    # Accept lowercase values from .env; logger will normalize
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

env = Settings()
