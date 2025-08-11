"""Database connection and configuration."""

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL database connection manager."""

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Initialize connection pool."""
        try:
            self._pool = await asyncpg.create_pool(self.database_url)
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error("Failed to create database connection pool: %s", e)
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")

    async def execute_query(
        self, query: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a SQL query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries representing rows
        """
        if not self._pool:
            raise RuntimeError("Database connection not initialized")

        async with self._pool.acquire() as connection:
            try:
                if params:
                    result = await connection.fetch(query, *params)
                else:
                    result = await connection.fetch(query)

                return [dict(row) for row in result]
            except Exception as e:
                logger.error("Query execution failed: %s", e)
                logger.error("Query: %s", query)
                logger.error("Params: %s", params)
                raise

    async def execute_command(
        self, command: str, params: list[Any] | None = None
    ) -> None:
        """Execute a SQL command (INSERT, UPDATE, DELETE).

        Args:
            command: SQL command string
            params: Command parameters
        """
        if not self._pool:
            raise RuntimeError("Database connection not initialized")

        async with self._pool.acquire() as connection:
            try:
                if params:
                    await connection.execute(command, *params)
                else:
                    await connection.execute(command)
            except Exception as e:
                logger.error("Command execution failed: %s", e)
                logger.error("Command: %s", command)
                logger.error("Params: %s", params)
                raise


class DatabaseManager:
    """Singleton manager for the database connection."""

    _db_connection: DatabaseConnection | None = None

    @classmethod
    def get_database(cls) -> DatabaseConnection:
        """Get the database connection instance.

        Returns:
            Database connection instance

        Raises:
            RuntimeError: If database is not initialized
        """
        if cls._db_connection is None:
            raise RuntimeError("Database connection not initialized")
        return cls._db_connection

    @classmethod
    async def initialize_database(cls, database_url: str) -> None:
        """Initialize the database connection.

        Args:
            database_url: PostgreSQL connection URL
        """
        cls._db_connection = DatabaseConnection(database_url)
        await cls._db_connection.initialize()

    @classmethod
    async def close_database(cls) -> None:
        """Close the database connection."""
        if cls._db_connection:
            await cls._db_connection.close()
            cls._db_connection = None
