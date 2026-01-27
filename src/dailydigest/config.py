"""Application configuration powered by pydantic settings."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_RSS_FEEDS = [
    "https://bensbites.beehiiv.com/feed",
    "https://openai.com/blog/rss",
    "https://www.oreilly.com/radar/feed/index.xml",
]


class AppConfig(BaseSettings):
    """Central configuration model for the Daily Digest application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/dailydigest",
        description="SQLAlchemy-compatible PostgreSQL connection string",
    )
    hacker_news_query: str = Field(
        default="ai OR \"artificial intelligence\" OR \"llama\"",
        description="Boolean query sent to the Algolia-powered Hacker News API",
    )
    rss_feeds: List[str] = Field(default_factory=lambda: DEFAULT_RSS_FEEDS.copy())
    request_timeout_seconds: float = Field(default=10.0, gt=0, description="HTTP timeout for source adapters")
    max_items_per_source: int = Field(default=75, ge=1, le=1000)
    default_ingestion_window_hours: int = Field(default=24, ge=1, le=168)
    
    # Email/SMTP settings
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP connection")
    smtp_username: str = Field(default="", description="SMTP authentication username")
    smtp_password: str = Field(default="", description="SMTP authentication password")
    smtp_from_email: str = Field(default="", description="From email address")
    
    # Telegram settings
    telegram_bot_token: str = Field(default="", description="Telegram bot token from @BotFather")
    telegram_default_chat_id: str = Field(default="", description="Default Telegram chat ID")

    @field_validator("rss_feeds", mode="before")
    @classmethod
    def _split_csv(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache application settings."""

    return AppConfig()


# Global settings instance
settings = get_config()
