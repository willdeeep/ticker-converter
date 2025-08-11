"""API dependencies and configuration."""

import os
from typing import AsyncGenerator
from api.database import get_database, DatabaseConnection


async def get_db() -> AsyncGenerator[DatabaseConnection, None]:
    """FastAPI dependency to get database connection.
    
    Yields:
        Database connection instance
    """
    db = get_database()
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
    else:
        return f"postgresql://{user}@{host}:{port}/{database}"


def get_api_settings() -> dict:
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
