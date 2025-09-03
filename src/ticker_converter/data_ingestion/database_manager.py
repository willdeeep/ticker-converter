"""Database manager for data ingestion operations.

This module handles database connectivity and operations for the data ingestion
pipeline, including checking if the database needs initial setup.
"""

import logging
import os
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

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get PostgreSQL database connection."""
        return psycopg2.connect(self.connection_string)

    @contextmanager
    def connection(
        self,
    ) -> Generator[psycopg2.extensions.connection, None, None]:
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
            # PostgreSQL connection
            # nosec B101: Type checking assert for PostgreSQL connection
            assert isinstance(conn, psycopg2.extensions.connection)  # nosec
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

            # PostgreSQL bulk insert
            from psycopg2.extras import execute_values  # pylint: disable=import-outside-toplevel

            # Convert dict records to tuple values
            columns = list(records[0].keys())
            values = [[record[col] for col in columns] for record in records]

            execute_values(cursor, query, values)
            inserted_count = cursor.rowcount or 0  # Handle None case

            conn.commit()
            return int(inserted_count)

    def is_database_empty(self) -> bool:
        """Check if the database has any stock or currency data.

        Returns:
            True if database is empty (needs initial setup)
        """
        try:
            # Check for stock data in fact table
            stock_result = self.execute_query("SELECT COUNT(*) as count FROM fact_stock_prices")
            stock_count = stock_result[0]["count"] if stock_result else 0

            # Check for currency data in fact table
            currency_result = self.execute_query("SELECT COUNT(*) as count FROM fact_currency_rates")
            currency_count = currency_result[0]["count"] if currency_result else 0

            return stock_count == 0 and currency_count == 0

        except (psycopg2.Error, OSError) as e:
            self.logger.error("Database error during empty check: %s", e)
            # Assume not empty on error to prevent unnecessary initialization
            return False

    def get_latest_stock_date(self, symbol: str | None = None) -> datetime | None:
        """Get the most recent stock data date.

        Args:
            symbol: Optional specific symbol to check. If None, checks across all symbols.

        Returns:
            Latest date as datetime object, or None if no data exists
        """
        try:
            if symbol:
                query = """
                    SELECT MAX(d.date_value) as latest_date
                    FROM fact_stock_prices fsp
                    JOIN dim_date d ON fsp.date_id = d.date_id
                    WHERE fsp.symbol = %s
                """
                result = self.execute_query(query, (symbol,))
            else:
                query = """
                    SELECT MAX(d.date_value) as latest_date
                    FROM fact_stock_prices fsp
                    JOIN dim_date d ON fsp.date_id = d.date_id
                """
                result = self.execute_query(query)

            if result and result[0]["latest_date"]:
                latest_date = result[0]["latest_date"]
                # Ensure we return a datetime object
                if isinstance(latest_date, datetime):
                    return latest_date
                # Handle string dates by parsing them
                elif isinstance(latest_date, str):
                    return datetime.fromisoformat(latest_date.replace("Z", "+00:00"))
                else:
                    # Return None for unexpected types to avoid Any return
                    return None
            return None

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting latest stock date: %s", e)
            return None

    def get_latest_currency_date(self) -> datetime | None:
        """Get the most recent currency data date.

        Returns:
            Latest date as datetime object, or None if no data exists
        """
        try:
            query = """
                SELECT MAX(d.date_value) as latest_date
                FROM fact_currency_rates fcr
                JOIN dim_date d ON fcr.date_id = d.date_id
            """
            result = self.execute_query(query)

            if result and result[0]["latest_date"]:
                latest_date = result[0]["latest_date"]
                # Ensure we return a datetime object
                if isinstance(latest_date, datetime):
                    return latest_date
                # Handle string dates by parsing them
                elif isinstance(latest_date, str):
                    return datetime.fromisoformat(latest_date.replace("Z", "+00:00"))
                else:
                    # Return None for unexpected types to avoid Any return
                    return None
            return None

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting latest currency date: %s", e)
            return None

    def ensure_date_dimension(self, date_value: str | datetime) -> bool:
        """Ensure the given date exists in the dim_date table.

        Args:
            date_value: Date as string (YYYY-MM-DD) or datetime object

        Returns:
            True if date dimension record was ensured, False on error
        """
        try:
            # Convert to datetime if string
            if isinstance(date_value, str):
                dt = datetime.strptime(date_value, "%Y-%m-%d")
            else:
                dt = date_value

            # Check if date already exists
            existing = self.execute_query(
                "SELECT date_id FROM dim_date WHERE date_value = %s", (dt.strftime("%Y-%m-%d"),)
            )

            if existing:
                return True

            # PostgreSQL-specific insert with correct field names matching schema
            date_record = {
                "date_value": dt.strftime("%Y-%m-%d"),
                "year": dt.year,
                "quarter": (dt.month - 1) // 3 + 1,
                "month": dt.month,
                "day": dt.day,
                "day_of_week": dt.weekday() + 1,  # Monday = 1, Sunday = 7
                "day_of_year": dt.timetuple().tm_yday,
                "week_of_year": dt.isocalendar()[1],
                "is_weekend": dt.weekday() >= 5,
                "is_holiday": False,  # Default to false, can be updated later
            }

            query = """
                INSERT INTO dim_date (date_value, year, quarter, month, day, day_of_week,
                                    day_of_year, week_of_year, is_weekend, is_holiday)
                VALUES (%(date_value)s, %(year)s, %(quarter)s, %(month)s, %(day)s,
                        %(day_of_week)s, %(day_of_year)s, %(week_of_year)s, %(is_weekend)s, %(is_holiday)s)
                ON CONFLICT (date_value) DO NOTHING
            """

            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, date_record)
                conn.commit()

            return True

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error ensuring date dimension for %s: %s", date_value, e)
            return False

    def insert_stock_data(self, records: list[dict[str, Any]]) -> int:
        """Insert stock data into fact_stock_prices table.

        Args:
            records: List of stock data records with JSON field names

        Returns:
            Number of records successfully inserted
        """
        if not records:
            return 0

        inserted_count = 0

        try:
            # First, ensure all required dates exist in dim_date
            for record in records:
                date_str = record.get("data_date")  # JSON uses 'data_date'
                if date_str and not self.ensure_date_dimension(date_str):
                    self.logger.warning("Failed to ensure date dimension for %s", date_str)

            # PostgreSQL-specific bulk insert with conflict resolution
            # Map JSON field names to database field names
            query = """
                INSERT INTO fact_stock_prices (stock_id, date_id, opening_price, high_price, low_price,
                                             closing_price, volume, adjusted_close)
                SELECT ds.stock_id, d.date_id, %(open_price)s, %(high_price)s, %(low_price)s,
                       %(close_price)s, %(volume)s, %(close_price)s
                FROM dim_date d
                CROSS JOIN dim_stocks ds
                WHERE d.date_value = %(data_date)s AND ds.symbol = %(symbol)s
                ON CONFLICT (stock_id, date_id) DO UPDATE SET
                    opening_price = EXCLUDED.opening_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    closing_price = EXCLUDED.closing_price,
                    volume = EXCLUDED.volume,
                    adjusted_close = EXCLUDED.adjusted_close,
                    updated_at = CURRENT_TIMESTAMP
            """

            with self.connection() as conn:
                cursor = conn.cursor()
                for record in records:
                    try:
                        # Map JSON field names to what the query expects
                        mapped_record = {
                            "symbol": record["symbol"],
                            "data_date": record["data_date"],
                            "open_price": record["open_price"],
                            "high_price": record["high_price"],
                            "low_price": record["low_price"],
                            "close_price": record["close_price"],
                            "volume": record["volume"],
                        }
                        cursor.execute(query, mapped_record)
                        if cursor.rowcount > 0:
                            inserted_count += cursor.rowcount
                    except (psycopg2.Error, KeyError) as e:
                        self.logger.warning("Failed to insert stock record %s: %s", record, e)
                        continue

                conn.commit()

            self.logger.info("Successfully inserted %d stock records", inserted_count)
            return inserted_count

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error during stock data insertion: %s", e)
            return 0

    def insert_currency_data(self, records: list[dict[str, Any]]) -> int:
        """Insert currency data into fact_currency_rates table.

        Args:
            records: List of currency data records with JSON field names

        Returns:
            Number of records successfully inserted
        """
        if not records:
            return 0

        inserted_count = 0

        try:
            # First, ensure all required dates exist in dim_date
            for record in records:
                date_str = record.get("data_date")  # JSON uses 'data_date'
                if date_str and not self.ensure_date_dimension(date_str):
                    self.logger.warning("Failed to ensure date dimension for %s", date_str)

            # PostgreSQL-specific bulk insert with conflict resolution
            # Map JSON field names to database field names using dimension lookups
            query = """
                INSERT INTO fact_currency_rates (from_currency_id, to_currency_id, date_id, exchange_rate)
                SELECT
                    dc_from.currency_id,
                    dc_to.currency_id,
                    d.date_id,
                    %(exchange_rate)s
                FROM dim_date d
                CROSS JOIN dim_currency dc_from
                CROSS JOIN dim_currency dc_to
                WHERE d.date_value = %(data_date)s
                  AND dc_from.currency_code = %(from_currency)s
                  AND dc_to.currency_code = %(to_currency)s
                ON CONFLICT (from_currency_id, to_currency_id, date_id) DO UPDATE SET
                    exchange_rate = EXCLUDED.exchange_rate,
                    updated_at = CURRENT_TIMESTAMP
            """

            with self.connection() as conn:
                cursor = conn.cursor()
                for record in records:
                    try:
                        # Map JSON field names to what the query expects
                        mapped_record = {
                            "from_currency": record["from_currency"],
                            "to_currency": record["to_currency"],
                            "data_date": record["data_date"],
                            "exchange_rate": record["exchange_rate"],
                        }
                        cursor.execute(query, mapped_record)
                        if cursor.rowcount > 0:
                            inserted_count += cursor.rowcount
                    except (psycopg2.Error, KeyError) as e:
                        self.logger.warning("Failed to insert currency record %s: %s", record, e)
                        continue

                conn.commit()

            self.logger.info("Successfully inserted %d currency records", inserted_count)
            return inserted_count

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error during currency data insertion: %s", e)
            return 0

    def get_missing_dates_for_symbol(self, symbol: str, days_back: int = 10) -> list[datetime]:
        """Get dates that are missing for a specific symbol within the last N days.

        Args:
            symbol: Stock symbol to check
            days_back: Number of days back from today to check

        Returns:
            List of missing datetime objects
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            # PostgreSQL query to find missing dates for the symbol
            query = """
                SELECT d.date_value
                FROM dim_date d
                WHERE d.date_value BETWEEN %s AND %s
                  AND d.is_weekend = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM fact_stock_prices fsp
                      WHERE fsp.date_id = d.date_id AND fsp.symbol = %s
                  )
                ORDER BY d.date_value
            """

            result = self.execute_query(query, (start_date, end_date, symbol))
            return [row["date_value"] for row in result]

        except (psycopg2.Error, ValueError, TypeError) as e:
            self.logger.error("Error getting missing dates for symbol %s: %s", symbol, e)
            return []

    def health_check(self) -> dict[str, Any]:
        """Perform a health check on the database.

        Returns:
            Dictionary with health check results
        """
        health_status: dict[str, Any] = {
            "database_connected": False,
            "tables_exist": False,
            "has_data": False,
            "error": None,
        }

        try:
            # Test basic connection
            with self.connection():
                health_status["database_connected"] = True

                # Check if required tables exist
                table_check_query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('fact_stock_prices', 'fact_currency_rates', 'dim_date')
                """

                tables = self.execute_query(table_check_query)
                table_names = {row["table_name"] for row in tables}
                required_tables = {"fact_stock_prices", "fact_currency_rates", "dim_date"}

                health_status["tables_exist"] = required_tables.issubset(table_names)

                if health_status["tables_exist"]:
                    # Check if there's any data
                    health_status["has_data"] = not self.is_database_empty()

        except (psycopg2.Error, ValueError, TypeError) as e:
            health_status["error"] = str(e)
            self.logger.error("Database health check failed: %s", e)

        return health_status
