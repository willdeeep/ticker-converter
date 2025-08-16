#!/usr/bin/env python3
"""FastAPI application startup script with database initialization."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

# pylint: disable=wrong-import-position
from .api.database import DatabaseManager
from .api.dependencies import get_database_url
from .api.main import app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:  # pylint: disable=unused-argument
    """Manage application lifecycle with database initialization."""
    logger.info("Starting Magnificent Seven Stock Performance API...")

    try:
        # Initialize database connection
        database_url = get_database_url()
        logger.info("Initializing database connection...")
        await DatabaseManager.initialize_database(database_url)
        logger.info("Database connection established successfully")

        yield

    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise
    finally:
        # Cleanup database connection
        logger.info("Shutting down database connections...")
        await DatabaseManager.close_database()
        logger.info("Application shutdown complete")


# Update the app with lifespan events
app.router.lifespan_context = lifespan


async def main() -> None:
    """Run the FastAPI application."""
    logger.info("Magnificent Seven Stock Performance API starting up...")

    config = uvicorn.Config(
        app=app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
