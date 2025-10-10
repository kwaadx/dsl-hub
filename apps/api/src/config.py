from __future__ import annotations

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings

def _csv(value: str) -> List[str]:
    value = (value or "").strip()
    if value in ("", "*"):
        return ["*"]
    return [v.strip() for v in value.split(",") if v.strip()]

class Settings(BaseSettings):
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")
    DB_HOST: str = Field(default="db", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="dsl_hub", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DB_SCHEMA: Optional[str] = Field(default=None, env="DB_SCHEMA")

    @property
    def dsn(self) -> str:
        schema_q = f"?schema={self.DB_SCHEMA}" if self.DB_SCHEMA else ""
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}{schema_q}"
    @property
    def DSN(self) -> str:
        return self.dsn

    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")
    API_INIT_SCHEMA_ON_START: bool = Field(default=True, env="API_INIT_SCHEMA_ON_START")
    API_INIT_SCHEMA_PATH: str = Field(default="v1.0.0.json", env="API_INIT_SCHEMA_PATH")
    API_SCHEMA_CHANNEL: str = Field(default="stable", env="API_SCHEMA_CHANNEL")
    API_MAX_JSON_SIZE: int = Field(default=1_048_576, env="API_MAX_JSON_SIZE")
    API_SSE_PING_INTERVAL: int = Field(default=15, env="API_SSE_PING_INTERVAL")
    API_SSE_BUFFER_TTL_SEC: int = Field(default=300, env="API_SSE_BUFFER_TTL_SEC")
    API_SSE_BUFFER_MAXLEN: int = Field(default=500, env="API_SSE_BUFFER_MAXLEN")
    API_IDEMPOTENCY_TTL_SEC: int = Field(default=300, env="API_IDEMPOTENCY_TTL_SEC")
    API_IDEMPOTENCY_CACHE_MAX: int = Field(default=1000, env="API_IDEMPOTENCY_CACHE_MAX")
    API_LLM_TIMEOUT: int = Field(default=30, env="API_LLM_TIMEOUT")
    API_LLM_RETRIES: int = Field(default=3, env="API_LLM_RETRIES")
    API_OPENAI_API_KEY: Optional[str] = Field(default=None, env="API_OPENAI_API_KEY")
    API_OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="API_OPENAI_MODEL")
    API_OPENAI_BASE_URL: Optional[str] = Field(default=None, env="API_OPENAI_BASE_URL")
    API_CORS_ORIGINS: str = Field(default="*", env="API_CORS_ORIGINS")
    @property
    def CORS_ORIGINS(self) -> list[str]:
        return _csv(self.API_CORS_ORIGINS)
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()