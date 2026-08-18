"""Unit tests for services/config_service.py configuration service."""

from services.config_service import Settings


def test_config_defaults():
    """Test configuration default values and missing API key state."""
    settings = Settings(OPENAI_API_KEY="")
    assert settings.OPENAI_API_KEY == ""
    assert settings.OPENAI_MODEL == "gpt-4o-mini"
    assert settings.AI_TEMPERATURE == 0.2
    assert settings.AI_MAX_TOKENS == 1500
    assert settings.AI_TIMEOUT_SECONDS == 30
    assert settings.AI_MAX_RETRIES == 2
    assert settings.MAX_FILE_SIZE_KB == 200
    assert settings.MAX_CODE_CHARS == 50000
    assert settings.ENVIRONMENT == "development"
    assert settings.is_openai_configured is False
    assert settings.get_masked_api_key() == "<NOT_SET>"


def test_config_api_key_masking():
    """Test API key masking to prevent leaking secrets in logs."""
    settings = Settings(OPENAI_API_KEY="sk-proj-1234567890abcdef")
    assert settings.is_openai_configured is True
    masked = settings.get_masked_api_key()
    assert masked.startswith("sk-p")
    assert masked.endswith("cdef")
    assert "1234567890" not in masked
