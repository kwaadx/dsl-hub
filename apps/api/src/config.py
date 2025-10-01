from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    DATABASE_URL: str = Field(..., description="PostgreSQL DSN")
    APP_SCHEMA_CHANNEL: str = "stable"
    SIMILARITY_THRESHOLD: float = 0.75
    SSE_PING_INTERVAL: int = 15

    # LLM provider config
    LLM_PROVIDER: str = Field(default="mock", description="LLM provider: 'mock' or 'openai'")
    LLM_TIMEOUT: int = Field(default=30, description="LLM request timeout (seconds)")

    # OpenAI config (used when LLM_PROVIDER == 'openai')
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="Override base URL (e.g., for Azure or proxy)")

settings = Settings()
