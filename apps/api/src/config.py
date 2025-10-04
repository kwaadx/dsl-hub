from __future__ import annotations
import os
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field
from sqlalchemy.engine import URL


def _assemble_dsn() -> str:
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "dsl_hub")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip().lower()
    return v in ("1", "true", "yes", "on")


def _csv_env(name: str, default: str) -> list[str]:
    """Parse CSV env var into a list; returns ["*"] if value is "*" or empty."""
    raw = os.getenv(name, default)
    if raw is None:
        return ["*"] if default.strip() in ("*", "") else [p.strip() for p in default.split(",") if p.strip()]
    raw = raw.strip()
    if raw in ("*", ""):
        return ["*"]
    return [p.strip() for p in raw.split(",") if p.strip()]


class Settings(BaseSettings):
    # Database config (завжди з DB_*)
    DB_HOST: str = Field(default="db")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="dsl_hub")
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="postgres")

    @property
    def dsn(self) -> str:
        """DSN для SQLAlchemy/psycopg2."""
        return _assemble_dsn()

    # App options (load from environment with API_* prefix where applicable)
    SCHEMA_CHANNEL: str = os.getenv("API_SCHEMA_CHANNEL", "stable")
    SIMILARITY_THRESHOLD: float = float(os.getenv("API_SIMILARITY_THRESHOLD", "0.75"))
    SSE_PING_INTERVAL: int = int(os.getenv("API_SSE_PING_INTERVAL", "15"))
    SSE_BUFFER_TTL_SEC: int = int(os.getenv("API_SSE_BUFFER_TTL_SEC", "300"))
    SSE_BUFFER_MAXLEN: int = int(os.getenv("API_SSE_BUFFER_MAXLEN", "500"))
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    MAX_JSON_SIZE: int = int(os.getenv("API_MAX_JSON_SIZE", "1048576"))

    # Idempotency / Security
    IDEMPOTENCY_TTL_SEC: int = int(os.getenv("API_IDEMPOTENCY_TTL_SEC", "300"))
    IDEMPOTENCY_CACHE_MAX: int = int(os.getenv("API_IDEMPOTENCY_CACHE_MAX", "1000"))
    AUTH_TOKEN: Optional[str] = os.getenv("API_AUTH_TOKEN") or None

    # Init seed
    INIT_SCHEMA_ON_START: bool = _get_bool("API_INIT_SCHEMA_ON_START", True)
    INIT_SCHEMA_PATH: Optional[str] = os.getenv("API_INIT_SCHEMA_PATH") or None

    # LLM
    LLM_PROVIDER: str = os.getenv("API_LLM_PROVIDER", "mock")
    LLM_TIMEOUT: int = int(os.getenv("API_LLM_TIMEOUT", "30"))
    LLM_RETRIES: int = int(os.getenv("API_LLM_RETRIES", "3"))
    OPENAI_API_KEY: Optional[str] = os.getenv("API_OPENAI_API_KEY") or None
    OPENAI_MODEL: str = os.getenv("API_OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: Optional[str] = os.getenv("API_OPENAI_BASE_URL") or None

    # CORS
    @property
    def CORS_ORIGINS(self) -> list[str]:
        # CSV list; "*" means allow all
        return _csv_env("API_CORS_ORIGINS", "*")


settings = Settings()
