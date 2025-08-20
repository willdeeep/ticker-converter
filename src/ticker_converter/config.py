"""Centralized configuration management for ticker-converter.

This module provides type-safe configuration management using Pydantic Settings
with comprehensive environment variable validation and documentation.
"""

# pylint: disable=no-member  # Pydantic fields cause false positives

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database connection settings
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="ticker_converter", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: SecretStr = Field(default=SecretStr(""), description="Database password")

    # Connection pool settings
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max pool overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    # SQLite fallback
    sqlite_path: Path = Field(
        default=Path("data/ticker_converter.db"),
        description="SQLite database path for local development",
    )

    def get_url(self) -> str:
        """Get the database URL."""
        # Check for explicit DATABASE_URL first
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        # Build PostgreSQL URL if password is provided
        password_value = self.password.get_secret_value()
        if password_value:
            return f"postgresql://{self.user}:{password_value}" f"@{self.host}:{self.port}/{self.name}"

        # Fall back to SQLite for local development
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.sqlite_path}"

    @field_validator("sqlite_path", mode="before")
    @classmethod
    def resolve_sqlite_path(cls, v: Any) -> Path:
        """Resolve SQLite path relative to project root."""
        if isinstance(v, str):
            path = Path(v)
            if not path.is_absolute():
                # Make relative to project root
                project_root = Path(__file__).parent.parent.parent
                path = project_root / path
            return path
        return Path(v) if not isinstance(v, Path) else v


class APISettings(BaseSettings):
    """Alpha Vantage API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="ALPHA_VANTAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API authentication
    api_key: SecretStr = Field(
        default=SecretStr("demo"),
        description="Alpha Vantage API key",
        alias="ALPHA_VANTAGE_API_KEY",
    )

    # API endpoints
    base_url: str = Field(
        default="https://www.alphavantage.co/query",
        description="Alpha Vantage API base URL",
    )

    # Request configuration
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of retry attempts")
    rate_limit_delay: int = Field(
        default=12,
        ge=1,
        le=60,
        description="Delay between requests in seconds (free tier: 5 req/min)",
    )

    # Request batching
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for bulk operations")

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: Any) -> SecretStr:
        """Validate API key format."""
        if isinstance(v, SecretStr):
            key = v.get_secret_value()
        else:
            key = str(v) if v else ""

        # Allow demo key for testing
        if key == "demo":
            return SecretStr(key)

        # Validate real API key format (Alpha Vantage keys are typically 16 chars)
        if key and len(key) < 8:
            raise ValueError("API key must be at least 8 characters long")

        return SecretStr(key)


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file_path: Path | None = Field(default=None, description="Log file path (None for console only)")
    max_bytes: int = Field(default=10_000_000, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files to keep")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = v.upper()
        if level not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return level


class AppSettings(BaseSettings):
    """Application-wide configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    name: str = Field(default="ticker-converter", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Environment
    environment: str = Field(default="development", description="Application environment")

    # Data directory
    data_dir: Path = Field(default=Path("data"), description="Data directory path")

    # Worker configuration
    max_workers: int = Field(default=4, ge=1, le=32, description="Maximum number of worker threads")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_envs = {"development", "testing", "staging", "production"}
        env = v.lower()
        if env not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return env

    @field_validator("data_dir", mode="before")
    @classmethod
    def resolve_data_dir(cls, v: Any) -> Path:
        """Resolve data directory path."""
        if isinstance(v, str):
            path = Path(v)
            if not path.is_absolute():
                # Make relative to project root
                project_root = Path(__file__).parent.parent.parent
                path = project_root / path
            return path
        return Path(v) if not isinstance(v, Path) else v

    @model_validator(mode="after")
    def create_data_directory(self) -> "AppSettings":
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self


class Settings(BaseModel):
    """Main settings class that combines all configuration sections."""

    # Configuration sections
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    This function uses LRU cache to ensure settings are only loaded once
    during the application lifecycle.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience functions for backward compatibility
def get_api_config() -> APISettings:
    """Get API configuration settings."""
    return get_settings().api


def get_database_config() -> DatabaseSettings:
    """Get database configuration settings."""
    return get_settings().database


def get_app_config() -> AppSettings:
    """Get application configuration settings."""
    return get_settings().app


def get_logging_config() -> LoggingSettings:
    """Get logging configuration settings."""
    return get_settings().logging
