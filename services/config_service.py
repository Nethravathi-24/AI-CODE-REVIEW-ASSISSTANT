"""Centralized Configuration Service using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # API Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    HF_MODEL_NAME: str = "distilbert-base-uncased"

    # AI Execution Tuning
    AI_TEMPERATURE: float = 0.2
    AI_MAX_TOKENS: int = 1500
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2

    # Input Boundaries
    MAX_FILE_SIZE_KB: int = 200
    MAX_CODE_CHARS: int = 50000

    # Environment Mode
    ENVIRONMENT: str = "development"

    def get_masked_api_key(self) -> str:
        """Returns a safe, masked representation of the API key for logging."""
        if not self.OPENAI_API_KEY:
            return "<NOT_SET>"
        if len(self.OPENAI_API_KEY) <= 8:
            return "***"
        return f"{self.OPENAI_API_KEY[:4]}...{self.OPENAI_API_KEY[-4:]}"

    @property
    def is_openai_configured(self) -> bool:
        """Helper to check if OpenAI API key is present."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Returns the singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
