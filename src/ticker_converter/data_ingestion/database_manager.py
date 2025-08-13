"""Database manager for data ingestion operations.

This module handles database connectivity and operations for the data ingestion
pipeline, including checking if the database needs initial setup.
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()


# Simple config class for database operations
class SimpleConfig:
    """Simple configuration class for database operations."""

    def __init__(self) -> None:
        self.DATABASE_URL = os.getenv("DATABASE_URL")


config = SimpleConfig()


class DatabaseManager:
    """Manager for database operations during data ingestion."""

    def __init__(self, connection_string: str | None = None) -> None:
        """Initialize the database manager.

        Args:
            connection_string: Database connection string. If None, uses config.
        """
        self.connection_string = connection_string or self._get_default_connection()
        self.is_sqlite = "sqlite" in self.connection_string.lower()
        self.logger = logging.getLogger(__name__)

    def _get_default_connection(self) -> str:
        """Get default database connection from config."""
        if hasattr(config, "DATABASE_URL") and config.DATABASE_URL:
            return config.DATABASE_URL

        # Fall back to SQLite for development
        db_path = Path("data/ticker_converter.db")
        db_path.parent.mkdir(exist_ok=True)
        return f"sqlite:///{db_path}"

    def get_connection(self) -> sqlite3.Connection | psycopg2.extensions.connection:
        """Get database connection based on connection string."""
        if self.is_sqlite:
            # Extract path from sqlite:///path format
            db_path = self.connection_string.replace("sqlite:///", "")
            return sqlite3.connect(db_path)

        # PostgreSQL connection
        return psycopg2.connect(self.connection_string)

    def execute_query(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with self.get_connection() as conn:
            if self.is_sqlite:
                assert isinstance(conn, sqlite3.Connection)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]

            # PostgreSQL connection
            assert isinstance(conn, psycopg2.extensions.connection)
            with conn.cursor(cursor_factory=RealDictCursor) as pg_cursor:
                pg_cursor.execute(query, params or ())
                return [dict(row) for row in pg_cursor.fetchall()]

    def execute_insert(self, query: str, records: list[dict[str, Any]]) -> int:
        """Execute bulk insert operation.

        Args:
            query: SQL insert query
            records: List of record dictionaries to insert

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if self.is_sqlite:
                # SQLite bulk insert
                cursor.executemany(query, records)
                inserted_count = cursor.rowcount
            else:
                # PostgreSQL bulk insert
                from psycopg2.extras import (  # pylint: disable=import-outside-toplevel
                    execute_values,
                )

                # Convert dict records to tuple values
                columns = list(records[0].keys())
                values = [[record[col] for col in columns] for record in records]

                execute_values(cursor, query, values)
                inserted_count = cursor.rowcount

            conn.commit()
            return inserted_count

    def is_database_empty(self) -> bool:
        """Check if the database has any stock or currency data.

        Returns:
            True if database is empty (needs initial setup)
        """
        try:
            # Check for stock data
            stock_result = self.execute_query(
                "SELECT COUNT(*) as count FROM raw_stock_data"
            )
            stock_count = int(stock_result[0]["count"])

            # Check for currency data
            currency_result = self.execute_query(
                "SELECT COUNT(*) as count FROM raw_currency_data"
            )
            currency_count = int(currency_result[0]["count"])

            is_empty = stock_count == 0 and currency_count == 0
            self.logger.info(
                "Database check: %d stock records, %d currency records",
                stock_count,
                currency_count,
            )

            return is_empty

        except (sqlite3.Error, psycopg2.Error, OSError) as e:
            self.logger.warning("Error checking database status: %s", e)
            # Assume empty if we can't check
            return True

    def get_latest_stock_date(self, symbol: str | None = None) -> datetime | None:
        """Get the latest date for stock data.

        Args:
            symbol: Specific symbol to check, or None for any symbol

        Returns:
            Latest date or None if no data
        """
        try:
            if symbol:
                query = "SELECT MAX(data_date) as latest_date FROM raw_stock_data WHERE symbol = ?"
                params = (symbol,)
            else:
                query = "SELECT MAX(data_date) as latest_date FROM raw_stock_data"
                params = None

            result = self.execute_query(query, params)
            latest_date = result[0]["latest_date"] if result else None

            if isinstance(latest_date, str):
                return datetime.strptime(latest_date, "%Y-%m-%d")
            if isinstance(latest_date, datetime):
                return latest_date

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting latest stock date: %s", e)

        return None

    def get_latest_currency_date(self) -> datetime | None:
        """Get the latest date for currency data.

        Returns:
            Latest date or None if no data
        """
        try:
            result = self.execute_query(
                "SELECT MAX(data_date) as latest_date FROM raw_currency_data"
            )
            latest_date = result[0]["latest_date"] if result else None

            if isinstance(latest_date, str):
                return datetime.strptime(latest_date, "%Y-%m-%d")
            if isinstance(latest_date, datetime):
                return latest_date

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting latest currency date: %s", e)

        return None

    def insert_stock_data(self, records: list[dict[str, Any]]) -> int:
        """Insert stock data records.

        Args:
            records: List of stock data records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        # Prepare insert query for raw_stock_data table
        insert_query = """
        INSERT INTO raw_stock_data
        (symbol, data_date, open_price, high_price, low_price, close_price, volume, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, data_date, source) DO NOTHING
        """

        if not self.is_sqlite:
            # PostgreSQL syntax
            insert_query = """
            INSERT INTO raw_stock_data
            (symbol, data_date, open_price, high_price, low_price, close_price, volume, source, created_at)
            VALUES %s
            ON CONFLICT (symbol, data_date, source) DO NOTHING
            """

        try:
            inserted = self.execute_insert(insert_query, records)
            self.logger.info("Inserted %d stock data records", inserted)
            return inserted
        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error inserting stock data: %s", e)
            return 0

    def insert_currency_data(self, records: list[dict[str, Any]]) -> int:
        """Insert currency data records.

        Args:
            records: List of currency data records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        # Prepare insert query for raw_currency_data table
        insert_query = """
        INSERT INTO raw_currency_data
        (from_currency, to_currency, data_date, exchange_rate, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (from_currency, to_currency, data_date, source) DO NOTHING
        """

        if not self.is_sqlite:
            # PostgreSQL syntax
            insert_query = """
            INSERT INTO raw_currency_data
            (from_currency, to_currency, data_date, exchange_rate, source, created_at)
            VALUES %s
            ON CONFLICT (from_currency, to_currency, data_date, source) DO NOTHING
            """

        try:
            inserted = self.execute_insert(insert_query, records)
            self.logger.info("Inserted %d currency data records", inserted)
            return inserted
        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error inserting currency data: %s", e)
            return 0

    def get_missing_dates_for_symbol(
        self, symbol: str, days_back: int = 10
    ) -> list[datetime]:
        """Get list of missing dates for a symbol within the last N days.

        Args:
            symbol: Stock symbol to check
            days_back: Number of days to check back

        Returns:
            List of missing dates
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            # Get existing dates for this symbol
            existing_query = """
            SELECT DISTINCT data_date
            FROM raw_stock_data
            WHERE symbol = ? AND data_date >= ? AND data_date <= ?
            """

            existing_results = self.execute_query(
                existing_query, (symbol, start_date, end_date)
            )
            existing_dates = {
                (
                    datetime.strptime(row["data_date"], "%Y-%m-%d").date()
                    if isinstance(row["data_date"], str)
                    else row["data_date"]
                )
                for row in existing_results
            }

            # Generate all business days in range (rough approximation)
            all_dates = []
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends (rough filter)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    all_dates.append(current_date)
                current_date += timedelta(days=1)

            # Find missing dates
            missing_dates = [date for date in all_dates if date not in existing_dates]

            return [
                datetime.combine(date, datetime.min.time()) for date in missing_dates
            ]

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error finding missing dates for %s: %s", symbol, e)
            return []

    def health_check(self) -> dict[str, Any]:
        """Perform database health check.

        Returns:
            Dictionary with health check results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Basic connectivity test
                cursor.execute("SELECT 1")

                # Get table counts
                stock_count = self.execute_query(
                    "SELECT COUNT(*) as count FROM raw_stock_data"
                )[0]["count"]
                currency_count = self.execute_query(
                    "SELECT COUNT(*) as count FROM raw_currency_data"
                )[0]["count"]

                # Get date ranges
                latest_stock = self.get_latest_stock_date()
                latest_currency = self.get_latest_currency_date()

                return {
                    "status": "healthy",
                    "stock_records": stock_count,
                    "currency_records": currency_count,
                    "latest_stock_date": (
                        latest_stock.isoformat() if latest_stock else None
                    ),
                    "latest_currency_date": (
                        latest_currency.isoformat() if latest_currency else None
                    ),
                    "is_empty": self.is_database_empty(),
                }

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            return {"status": "error", "error": str(e)}
