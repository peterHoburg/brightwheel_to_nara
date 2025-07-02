"""Configuration management for Brightwheel to Nara transfer."""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Brightwheel credentials
    brightwheel_username: str = Field(..., env="BRIGHTWHEEL_USERNAME")
    brightwheel_password: str = Field(..., env="BRIGHTWHEEL_PASSWORD")
    brightwheel_session_cookie: Optional[str] = Field(None, env="BRIGHTWHEEL_SESSION_COOKIE")
    
    # Nara credentials
    nara_email: Optional[str] = Field(None, env="NARA_EMAIL")
    nara_password: Optional[str] = Field(None, env="NARA_PASSWORD")
    
    # API endpoints (can be overridden for testing)
    brightwheel_base_url: str = Field(
        "https://schools.mybrightwheel.com",
        env="BRIGHTWHEEL_BASE_URL"
    )
    nara_base_url: str = Field(
        "https://api.nara.com",
        env="NARA_BASE_URL"
    )
    
    # Transfer settings
    sync_days_back: int = Field(7, env="SYNC_DAYS_BACK")
    batch_size: int = Field(50, env="BATCH_SIZE")
    retry_max_attempts: int = Field(3, env="RETRY_MAX_ATTEMPTS")
    retry_delay_seconds: float = Field(1.0, env="RETRY_DELAY_SECONDS")
    
    # Feature flags
    sync_photos: bool = Field(True, env="SYNC_PHOTOS")
    sync_notes: bool = Field(True, env="SYNC_NOTES")
    dry_run: bool = Field(False, env="DRY_RUN")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings instance
    """
    # Load from .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        return Settings(_env_file=env_file)
    return Settings()


# Activity type mappings
ACTIVITY_TYPE_MAPPING = {
    # Brightwheel -> Nara
    "diaper": "diaper",
    "bottle": "feeding",
    "food": "feeding",
    "nap": "sleep",
    "temperature": "health",
    "photo": "photo",
    "note": "note",
    "potty": "diaper",  # Map potty to diaper in Nara
    "mood": "mood",
    "incident": "health",
    "medication": "health"
}


# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    "brightwheel": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
    },
    "nara": {
        "requests_per_minute": 100,
        "requests_per_hour": 2000,
    }
}


# Date/time formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
TIMEZONE = "UTC"  # Can be overridden per school/user