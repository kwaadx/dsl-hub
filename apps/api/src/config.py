from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/dsl_hub",
        description="PostgreSQL DSN",
        validation_alias=AliasChoices("API_DATABASE_URL", "DATABASE_URL"),
    )
    APP_SCHEMA_CHANNEL: str = Field(
        default="stable",
        validation_alias=AliasChoices("API_APP_SCHEMA_CHANNEL", "APP_SCHEMA_CHANNEL"),
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.75,
        validation_alias=AliasChoices("API_SIMILARITY_THRESHOLD", "SIMILARITY_THRESHOLD"),
    )
    SSE_PING_INTERVAL: int = Field(
        default=15,
        validation_alias=AliasChoices("API_SSE_PING_INTERVAL", "SSE_PING_INTERVAL"),
    )
    APP_VERSION: str = Field(
        default="0.1.0", description="Application version reported by /version",
        validation_alias=AliasChoices("API_APP_VERSION", "APP_VERSION"),
    )
    MAX_JSON_SIZE: int = Field(
        default=1048576, description="Max JSON request body size in bytes",
        validation_alias=AliasChoices("API_MAX_JSON_SIZE", "MAX_JSON_SIZE"),
    )

    # API initialization options
    INIT_ON_START: bool = Field(
        default=True,
        description="Run DB/schema initialization on API container start",
        validation_alias=AliasChoices("API_INIT_ON_START", "INIT_ON_START"),
    )
    INIT_SCHEMA_PATH: Optional[str] = Field(
        default=None,
        description="Path to initial schema JSON file to seed (inside API container)",
        validation_alias=AliasChoices("API_INIT_SCHEMA_PATH", "INIT_SCHEMA_PATH"),
    )

    # LLM provider config
    LLM_PROVIDER: str = Field(
        default="mock", description="LLM provider: 'mock' or 'openai'",
        validation_alias=AliasChoices("API_LLM_PROVIDER", "LLM_PROVIDER"),
    )
    LLM_TIMEOUT: int = Field(
        default=30, description="LLM request timeout (seconds)",
        validation_alias=AliasChoices("API_LLM_TIMEOUT", "LLM_TIMEOUT"),
    )

    # OpenAI config (used when LLM_PROVIDER == 'openai')
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, description="OpenAI API key",
        validation_alias=AliasChoices("API_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini", description="OpenAI model name",
        validation_alias=AliasChoices("API_OPENAI_MODEL", "OPENAI_MODEL"),
    )
    OPENAI_BASE_URL: Optional[str] = Field(
        default=None, description="Override base URL (e.g., for Azure or proxy)",
        validation_alias=AliasChoices("API_OPENAI_BASE_URL", "OPENAI_BASE_URL"),
    )

settings = Settings()
