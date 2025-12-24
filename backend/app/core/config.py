"""
Application configuration using Pydantic Settings.

Supports environment variable overrides for all settings.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WikidataSettings(BaseSettings):
    """Wikidata API settings."""

    model_config = SettingsConfigDict(env_prefix="WIKIDATA_")

    base_url: str = "https://www.wikidata.org/w/api.php"
    timeout: float = 30.0
    max_retries: int = 3
    default_language: str = "en"
    # Rate limiting
    requests_per_second: float = 5.0


class MatchingSettings(BaseSettings):
    """Matching algorithm settings."""

    model_config = SettingsConfigDict(env_prefix="MATCHING_")

    # Score thresholds (0-100)
    auto_accept_threshold: int = 95
    high_confidence_threshold: int = 80
    low_confidence_threshold: int = 50

    # Weights for composite scoring (must sum to 1.0)
    name_weight: float = 0.5
    date_weight: float = 0.3
    property_weight: float = 0.2

    # Name matching settings
    name_exact_score: int = 100
    name_fuzzy_threshold: int = 70  # Min fuzzy ratio to consider a match

    # Date matching settings
    date_exact_score: int = 100
    date_year_only_score: int = 80
    date_tolerance_days: int = 3  # Days tolerance for "close enough" match


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Record Linker"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/record_linker"

    # Nested settings
    wikidata: WikidataSettings = WikidataSettings()
    matching: MatchingSettings = MatchingSettings()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
