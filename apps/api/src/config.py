from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    DATABASE_URL: str = Field(..., description="PostgreSQL DSN")
    APP_SCHEMA_CHANNEL: str = "stable"
    SIMILARITY_THRESHOLD: float = 0.75
    SSE_PING_INTERVAL: int = 15

settings = Settings()
