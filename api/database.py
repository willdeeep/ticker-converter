"""Database connection and configuration."""

import asyncpg
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL database connection manager."""
    
    def __init__(self, database_url: str):
        """Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize connection pool."""
        try:
            self._pool = await asyncpg.create_pool(self.database_url)
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")
    
    async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
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
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise
    
    async def execute_command(self, command: str, params: Optional[List[Any]] = None) -> None:
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
                logger.error(f"Command execution failed: {e}")
                logger.error(f"Command: {command}")
                logger.error(f"Params: {params}")
                raise


# Global database instance
db_connection: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """Get the database connection instance.
    
    Returns:
        Database connection instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if db_connection is None:
        raise RuntimeError("Database connection not initialized")
    return db_connection


async def initialize_database(database_url: str) -> None:
    """Initialize the global database connection.
    
    Args:
        database_url: PostgreSQL connection URL
    """
    global db_connection
    db_connection = DatabaseConnection(database_url)
    await db_connection.initialize()


async def close_database() -> None:
    """Close the global database connection."""
    global db_connection
    if db_connection:
        await db_connection.close()
        db_connection = None
