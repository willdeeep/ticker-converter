"""API dependencies and configuration."""

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from api.database import DatabaseConnection, DatabaseManager


def get_sql_query(filename: str) -> str:
    """Load SQL query from file.

    Args:
        filename: Name of the SQL file (e.g., 'top_performers.sql')

    Returns:
        SQL query string

    Raises:
        FileNotFoundError: If SQL file doesn't exist
    """
    # Get the project root (parent of api directory)
    project_root = Path(__file__).parent.parent
    sql_file = project_root / "sql" / "queries" / filename

    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    return sql_file.read_text()


async def get_db() -> AsyncGenerator[DatabaseConnection, None]:
    """FastAPI dependency to get database connection.

    Yields:
        Database connection instance
    """
    db = DatabaseManager.get_database()
    try:
        yield db
    finally:
        # Connection is managed by the global pool, no cleanup needed
        pass


def get_database_url() -> str:
    """Get database URL from environment variables.

    Returns:
        PostgreSQL connection URL

    Raises:
        ValueError: If required environment variables are missing
    """
    # Check for full DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "ticker_converter")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")

    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    return f"postgresql://{user}@{host}:{port}/{database}"


def get_api_settings() -> dict[str, Any]:
    """Get API configuration settings.

    Returns:
        Dictionary of API settings
    """
    return {
        "title": "Ticker Converter API",
        "description": "SQL-first API for Magnificent Seven stock data and currency conversion",
        "version": "0.3.0",
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
    }
