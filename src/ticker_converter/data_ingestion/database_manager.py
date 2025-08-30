"""Database manager for data ingestion operations.

This module handles database connectivity and operations for the data ingestion
pipeline, including checking if the database needs initial setup.
"""

import logging
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables from project root
# Find project root by looking for pyproject.toml
_current_file = Path(__file__).resolve()
_project_root = None
for parent in _current_file.parents:
    if (parent / "pyproject.toml").exists():
        _project_root = parent
        break

if _project_root:
    load_dotenv(_project_root / ".env")
else:
    # Fallback to default behavior
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
        """Get database connection from config.

        Raises:
            RuntimeError: If no DATABASE_URL is configured.
        """
        if hasattr(config, "DATABASE_URL") and config.DATABASE_URL:
            return config.DATABASE_URL

        # No fallback - PostgreSQL is required per project specifications
        raise RuntimeError(
            "DATABASE_URL is required but not configured. "
            "Please set DATABASE_URL in your .env file to point to PostgreSQL. "
            "This project requires PostgreSQL for all structured data storage."
        )

    def get_connection(self) -> sqlite3.Connection | psycopg2.extensions.connection:
        """Get database connection based on connection string."""
        if self.is_sqlite:
            # Extract path from sqlite:///path format
            db_path = self.connection_string.replace("sqlite:///", "")
            return sqlite3.connect(db_path)

        # PostgreSQL connection
        return psycopg2.connect(self.connection_string)

    @contextmanager
    def connection(
        self,
    ) -> Generator[sqlite3.Connection | psycopg2.extensions.connection, None, None]:
        """Context manager for database connections.

        Ensures proper connection cleanup and error handling.
        """
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with self.connection() as conn:
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

        with self.connection() as conn:
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
            # Check for stock data in fact table
            stock_result = self.execute_query("SELECT COUNT(*) as count FROM fact_stock_prices")
            stock_count = int(stock_result[0]["count"])

            # Check for currency data in fact table
            currency_result = self.execute_query("SELECT COUNT(*) as count FROM fact_currency_rates")
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
        """Get the latest date for stock data from fact table.

        Args:
            symbol: Specific symbol to check, or None for any symbol

        Returns:
            Latest date or None if no data
        """
        try:
            if symbol:
                query = """
                SELECT MAX(dd.date_value) as latest_date 
                FROM fact_stock_prices fsp
                JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
                JOIN dim_date dd ON fsp.date_id = dd.date_id
                WHERE ds.symbol = ?
                """
                params = (symbol,)
            else:
                query = """
                SELECT MAX(dd.date_value) as latest_date 
                FROM fact_stock_prices fsp
                JOIN dim_date dd ON fsp.date_id = dd.date_id
                """
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
        """Get the latest date for currency data from fact table.

        Returns:
            Latest date or None if no data
        """
        try:
            query = """
            SELECT MAX(dd.date_value) as latest_date 
            FROM fact_currency_rates fcr
            JOIN dim_date dd ON fcr.date_id = dd.date_id
            """
            result = self.execute_query(query)
            latest_date = result[0]["latest_date"] if result else None

            if isinstance(latest_date, str):
                return datetime.strptime(latest_date, "%Y-%m-%d")
            if isinstance(latest_date, datetime):
                return latest_date

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting latest currency date: %s", e)

        return None

    def ensure_date_dimension(self, date_value: str | datetime) -> None:
        """Ensure date exists in dim_date table.
        
        Args:
            date_value: Date to ensure exists in dimension table
        """
        if isinstance(date_value, str):
            date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
        elif isinstance(date_value, datetime):
            date_obj = date_value.date()
        else:
            date_obj = date_value

        insert_query = """
        INSERT INTO dim_date (
            date_value, year, quarter, month, day, day_of_week, 
            day_of_year, week_of_year, is_weekend
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (date_value) DO NOTHING
        """

        if not self.is_sqlite:
            insert_query = """
            INSERT INTO dim_date (
                date_value, year, quarter, month, day, day_of_week, 
                day_of_year, week_of_year, is_weekend
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_value) DO NOTHING
            """

        # Calculate date components
        quarter = (date_obj.month - 1) // 3 + 1
        day_of_week = date_obj.weekday() + 1  # 1=Monday, 7=Sunday
        day_of_year = date_obj.timetuple().tm_yday
        week_of_year = date_obj.isocalendar()[1]
        is_weekend = date_obj.weekday() >= 5  # Saturday=5, Sunday=6

        date_record = [
            date_obj,
            date_obj.year,
            quarter,
            date_obj.month,
            date_obj.day,
            day_of_week,
            day_of_year,
            week_of_year,
            is_weekend
        ]

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, date_record)
                conn.commit()
        except (sqlite3.Error, psycopg2.Error) as e:
            self.logger.warning("Error ensuring date dimension for %s: %s", date_obj, e)

    def insert_stock_data(self, records: list[dict[str, Any]]) -> int:
        """Insert stock data records directly into fact_stock_prices table.

        Args:
            records: List of stock data records with keys: symbol, data_date, 
                    open_price, high_price, low_price, close_price, volume

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        # Ensure all dates exist in dim_date table
        for record in records:
            self.ensure_date_dimension(record.get('data_date'))

        # Insert directly into fact_stock_prices table with dimensional lookups
        insert_query = """
        INSERT INTO fact_stock_prices 
        (stock_id, date_id, opening_price, high_price, low_price, closing_price, volume, created_at)
        SELECT 
            ds.stock_id,
            dd.date_id,
            ?,  -- opening_price
            ?,  -- high_price
            ?,  -- low_price
            ?,  -- closing_price
            ?,  -- volume
            CURRENT_TIMESTAMP
        FROM dim_stocks ds
        CROSS JOIN dim_date dd
        WHERE ds.symbol = ? AND dd.date_value = ?
        ON CONFLICT (stock_id, date_id) DO NOTHING
        """

        if not self.is_sqlite:
            # PostgreSQL syntax - need to handle bulk inserts differently
            insert_query = """
            INSERT INTO fact_stock_prices 
            (stock_id, date_id, opening_price, high_price, low_price, closing_price, volume, created_at)
            SELECT 
                ds.stock_id,
                dd.date_id,
                vals.opening_price,
                vals.high_price,
                vals.low_price,
                vals.closing_price,
                vals.volume,
                CURRENT_TIMESTAMP
            FROM (VALUES %s) AS vals(opening_price, high_price, low_price, closing_price, volume, symbol, data_date)
            JOIN dim_stocks ds ON ds.symbol = vals.symbol
            JOIN dim_date dd ON dd.date_value = vals.data_date
            ON CONFLICT (stock_id, date_id) DO NOTHING
            """

        try:
            # Prepare records for fact table insert - reorder fields for the VALUES clause
            fact_records = []
            for record in records:
                fact_record = [
                    record.get('open_price'),
                    record.get('high_price'), 
                    record.get('low_price'),
                    record.get('close_price'),
                    record.get('volume'),
                    record.get('symbol'),
                    record.get('data_date')
                ]
                fact_records.append(fact_record)

            inserted = self.execute_insert(insert_query, fact_records)
            self.logger.info("Inserted %d stock data records into fact_stock_prices", inserted)
            return inserted
        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error inserting stock data into fact_stock_prices: %s", e)
            return 0

    def insert_currency_data(self, records: list[dict[str, Any]]) -> int:
        """Insert currency data records directly into fact_currency_rates table.

        Args:
            records: List of currency data records with keys: from_currency, to_currency,
                    data_date, exchange_rate

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        # Ensure all dates exist in dim_date table
        for record in records:
            self.ensure_date_dimension(record.get('data_date'))

        # Insert directly into fact_currency_rates table with dimensional lookups
        insert_query = """
        INSERT INTO fact_currency_rates 
        (from_currency_id, to_currency_id, date_id, exchange_rate, created_at)
        SELECT 
            dc_from.currency_id,
            dc_to.currency_id,
            dd.date_id,
            ?,  -- exchange_rate
            CURRENT_TIMESTAMP
        FROM dim_currency dc_from
        CROSS JOIN dim_currency dc_to
        CROSS JOIN dim_date dd
        WHERE dc_from.currency_code = ? 
          AND dc_to.currency_code = ?
          AND dd.date_value = ?
        ON CONFLICT (from_currency_id, to_currency_id, date_id) DO NOTHING
        """

        if not self.is_sqlite:
            # PostgreSQL syntax - need to handle bulk inserts differently
            insert_query = """
            INSERT INTO fact_currency_rates 
            (from_currency_id, to_currency_id, date_id, exchange_rate, created_at)
            SELECT 
                dc_from.currency_id,
                dc_to.currency_id,
                dd.date_id,
                vals.exchange_rate,
                CURRENT_TIMESTAMP
            FROM (VALUES %s) AS vals(exchange_rate, from_currency, to_currency, data_date)
            JOIN dim_currency dc_from ON dc_from.currency_code = vals.from_currency
            JOIN dim_currency dc_to ON dc_to.currency_code = vals.to_currency
            JOIN dim_date dd ON dd.date_value = vals.data_date
            ON CONFLICT (from_currency_id, to_currency_id, date_id) DO NOTHING
            """

        try:
            # Prepare records for fact table insert - reorder fields for the VALUES clause
            fact_records = []
            for record in records:
                fact_record = [
                    record.get('exchange_rate'),
                    record.get('from_currency'),
                    record.get('to_currency'),
                    record.get('data_date')
                ]
                fact_records.append(fact_record)

            inserted = self.execute_insert(insert_query, fact_records)
            self.logger.info("Inserted %d currency data records into fact_currency_rates", inserted)
            return inserted
        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error inserting currency data into fact_currency_rates: %s", e)
            return 0

    def get_missing_dates_for_symbol(self, symbol: str, days_back: int = 10) -> list[datetime]:
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

            # Get existing dates for this symbol from fact table
            existing_query = """
            SELECT DISTINCT dd.date_value as data_date
            FROM fact_stock_prices fsp
            JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
            JOIN dim_date dd ON fsp.date_id = dd.date_id
            WHERE ds.symbol = ? AND dd.date_value >= ? AND dd.date_value <= ?
            """

            existing_results = self.execute_query(existing_query, (symbol, start_date, end_date))
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

            return [datetime.combine(date, datetime.min.time()) for date in missing_dates]

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

                # Get table counts from fact tables
                stock_count = self.execute_query("SELECT COUNT(*) as count FROM fact_stock_prices")[0]["count"]
                currency_count = self.execute_query("SELECT COUNT(*) as count FROM fact_currency_rates")[0]["count"]

                # Get date ranges
                latest_stock = self.get_latest_stock_date()
                latest_currency = self.get_latest_currency_date()

                return {
                    "status": "healthy",
                    "stock_records": stock_count,
                    "currency_records": currency_count,
                    "latest_stock_date": (latest_stock.isoformat() if latest_stock else None),
                    "latest_currency_date": (latest_currency.isoformat() if latest_currency else None),
                    "is_empty": self.is_database_empty(),
                }

        except (sqlite3.Error, psycopg2.Error, ValueError, TypeError) as e:
            return {"status": "error", "error": str(e)}
