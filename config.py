"""Configuration management using Pydantic and environment variables."""

import os
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    # SYB API Configuration
    syb_api_key: str = Field(..., env="SYB_API_KEY")
    syb_api_url: str = Field(default="https://api.soundtrackyourbrand.com/v2", env="SYB_API_URL")
    
    # Zone Configuration
    zone_ids: List[str] = Field(..., env="ZONE_IDS")
    
    # Monitoring Configuration
    polling_interval: int = Field(default=60, env="POLLING_INTERVAL")  # seconds
    offline_threshold: int = Field(default=600, env="OFFLINE_THRESHOLD")  # seconds (10 minutes)
    
    # Notification Configuration
    pushover_token: Optional[str] = Field(default=None, env="PUSHOVER_TOKEN")
    pushover_user_key: Optional[str] = Field(default=None, env="PUSHOVER_USER_KEY")
    
    # Email Configuration
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_to: Optional[str] = Field(default=None, env="EMAIL_TO")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    dashboard_url: str = Field(default="https://app.soundtrackyourbrand.com", env="DASHBOARD_URL")
    
    # HTTP Configuration
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(default=5, env="MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("zone_ids", pre=True)
    def parse_zone_ids(cls, v):
        """Parse comma-separated zone IDs."""
        if isinstance(v, str):
            return [zone_id.strip() for zone_id in v.split(",") if zone_id.strip()]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            syb_api_key=os.getenv("SYB_API_KEY", ""),
            zone_ids=os.getenv("ZONE_IDS", "").split(",") if os.getenv("ZONE_IDS") else [],
            polling_interval=int(os.getenv("POLLING_INTERVAL", "60")),
            offline_threshold=int(os.getenv("OFFLINE_THRESHOLD", "600")),
            pushover_token=os.getenv("PUSHOVER_TOKEN"),
            pushover_user_key=os.getenv("PUSHOVER_USER_KEY"),
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            email_from=os.getenv("EMAIL_FROM"),
            email_to=os.getenv("EMAIL_TO"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            dashboard_url=os.getenv("DASHBOARD_URL", "https://app.soundtrackyourbrand.com"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "5"))
        )