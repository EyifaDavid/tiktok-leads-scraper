"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Discovery Mode
    auto_discover: bool = Field(
        default=True,
        description="Enable automatic discovery mode",
    )
    
    # Scraper Settings
    search_query: str = Field(
        default="logistics company OR freight forwarder OR shipping agent OR cargo",
        description="TikTok search query for finding leads (manual mode only)",
    )
    max_users: int = Field(default=100, ge=1, description="Maximum users to scrape")
    headless: bool = Field(default=True, description="Run browser in headless mode")

    # Delays (seconds)
    min_delay: float = Field(default=5.0, ge=0, description="Minimum delay between actions")
    max_delay: float = Field(default=15.0, ge=0, description="Maximum delay between actions")

    # Database
    db_file: str = Field(default="tiktok_leads.db", description="SQLite database filename")

    # Output
    output_dir: str = Field(default="data", description="Output directory for exported files")

    # Proxies
    proxies: Optional[str] = Field(
        default=None,
        description="Comma-separated proxy list (http://user:pass@ip:port)",
    )

    # Browser Settings
    viewport_width: int = Field(default=1280, description="Browser viewport width")
    viewport_height: int = Field(default=800, description="Browser viewport height")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        description="Browser user agent string",
    )

    # TikTok Login (required for user search)
    tiktok_email: Optional[str] = Field(default=None, description="TikTok login email")
    tiktok_password: Optional[str] = Field(default=None, description="TikTok login password")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/scraper.log", description="Log file path")

    # Custom discovery configuration (comma-separated overrides for auto-discoverer)
    discovery_queries: Optional[str] = Field(
        default=None,
        description="Comma-separated search queries for auto-discovery (overrides defaults)",
    )
    discovery_hashtags: Optional[str] = Field(
        default=None,
        description="Comma-separated hashtags for auto-discovery (overrides defaults)",
    )
    include_keywords: Optional[str] = Field(
        default=None,
        description="Comma-separated bio keywords to identify relevant accounts (overrides defaults)",
    )
    exclude_keywords: Optional[str] = Field(
        default=None,
        description="Comma-separated bio keywords to filter out irrelevant accounts (overrides defaults)",
    )

    @field_validator("proxies")
    @classmethod
    def parse_proxies(cls, v: Optional[str]) -> List[str]:
        """Parse comma-separated proxy string into list."""
        if not v or v.strip() == "":
            return []
        return [p.strip() for p in v.split(",") if p.strip()]

    @property
    def proxy_list(self) -> List[str]:
        """Get parsed proxy list."""
        return self.parse_proxies(self.proxies)

    @staticmethod
    def _parse_csv(v: Optional[str]) -> Optional[List[str]]:
        """Parse a comma-separated string into a list, or return None."""
        if not v or v.strip() == "":
            return None
        return [p.strip() for p in v.split(",") if p.strip()]

    @property
    def discovery_queries_list(self) -> Optional[List[str]]:
        """Get custom search queries list or None."""
        return self._parse_csv(self.discovery_queries)

    @property
    def discovery_hashtags_list(self) -> Optional[List[str]]:
        """Get custom hashtags list or None."""
        return self._parse_csv(self.discovery_hashtags)

    @property
    def include_keywords_list(self) -> Optional[List[str]]:
        """Get custom include keywords list or None."""
        return self._parse_csv(self.include_keywords)

    @property
    def exclude_keywords_list(self) -> Optional[List[str]]:
        """Get custom exclude keywords list or None."""
        return self._parse_csv(self.exclude_keywords)

    def get_output_path(self, filename: str) -> Path:
        """Get full output path for a file."""
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path / filename

    def get_db_path(self) -> Path:
        """Get full database path."""
        return Path(self.db_file)

    def get_log_path(self) -> Path:
        """Get full log file path."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path


def get_settings() -> Settings:
    """Get configured settings instance."""
    return Settings()
