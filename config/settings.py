"""Configuration module providing settings access and application constants."""

from services.config_service import Settings, get_settings

# Re-export settings accessor
settings: Settings = get_settings()
