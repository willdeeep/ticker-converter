"""Database manager for data ingestion operations.

This module handles PostgreSQL database connectivity and operations for the data ingestion
pipeline, including checking if the database needs initial setup.
"""

import logging
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extensions
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseManager:
    """Manages PostgreSQL database connections and operations for data ingestion."""

    def __init__(self, connection_string: str | None = None) -> None:
        """Initialize the DatabaseManager with PostgreSQL connection.

        Args:
            connection_string: PostgreSQL connection string. If None, will use DATABASE_URL from environment.
        """
        self.connection_string = connection_string or self._get_connection_string()
        self.logger = logging.getLogger(__name__)

    def _get_connection_string(self) -> str:
        """Get PostgreSQL connection string from environment variables."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required for PostgreSQL connection"
            )

        if not database_url.startswith("postgresql://"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL connection string (postgresql://...)"
            )

        return database_url

    def get_connection(self) -> psycopg2.extensions.connection:
        """Establish a PostgreSQL database connection."""
        return psycopg2.connect(self.connection_string)

    def execute_query(
        self, query: str, params: Any = None, fetch_results: bool = False
    ) -> list[dict[str, Any]] | None:
        """Execute a query against the PostgreSQL database.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            fetch_results: Whether to fetch and return results

        Returns:
            Query results if fetch_results is True, None otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cursor:
                    cursor.execute(query, params)

                    if fetch_results:
                        results = cursor.fetchall()
                        return [dict(row) for row in results]

                    conn.commit()
                    return None

        except psycopg2.Error as e:
            self.logger.error("Database query failed: %s", e)
            raise

    def bulk_insert(
        self, table_name: str, data: list[dict[str, Any]], on_conflict: str = "NOTHING"
    ) -> None:
        """Perform bulk insert into PostgreSQL table.

        Args:
            table_name: Name of the table to insert into
            data: List of dictionaries containing the data to insert
            on_conflict: Conflict resolution strategy (NOTHING, UPDATE, etc.)
        """
        if not data:
            return

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # PostgreSQL bulk insert using execute_values
                    columns = list(data[0].keys())
                    values = [[row[col] for col in columns] for row in data]

                    query = f"""
                        INSERT INTO {table_name} ({", ".join(columns)})
                        VALUES %s
                        ON CONFLICT DO {on_conflict}
                    """

                    psycopg2.extras.execute_values(
                        cursor, query, values, template=None, page_size=1000
                    )
                    conn.commit()

        except psycopg2.Error as e:
            self.logger.error("Bulk insert failed for table %s: %s", table_name, e)
            raise

    def check_stocks_table_empty(self) -> bool:
        """Check if stocks table exists and is empty."""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM dim_stocks LIMIT 1", fetch_results=True
            )
            return result[0]["count"] == 0 if result else True

        except psycopg2.Error as e:
            self.logger.info("Stocks table check failed (table may not exist): %s", e)
            return True

    def check_exchange_rates_table_empty(self) -> bool:
        """Check if exchange rates table exists and is empty."""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM fact_exchange_rates LIMIT 1",
                fetch_results=True,
            )
            return result[0]["count"] == 0 if result else True

        except psycopg2.Error as e:
            self.logger.info(
                "Exchange rates table check failed (table may not exist): %s", e
            )
            return True

    def get_latest_stock_date(self, symbol: str) -> datetime | None:
        """Get the latest date for which we have stock data for a given symbol."""
        try:
            query = """
                SELECT MAX(sp.date) as latest_date
                FROM fact_stock_prices sp
                JOIN dim_stocks s ON sp.stock_id = s.id
                WHERE s.symbol = %s
            """

            result = self.execute_query(query, (symbol,), fetch_results=True)

            if result and result[0]["latest_date"]:
                return result[0]["latest_date"]
            return None

        except psycopg2.Error as e:
            self.logger.error("Failed to get latest stock date for %s: %s", symbol, e)
            return None

    def get_latest_exchange_rate_date(
        self, from_currency: str, to_currency: str
    ) -> datetime | None:
        """Get the latest date for exchange rate data."""
        try:
            query = """
                SELECT MAX(date) as latest_date
                FROM fact_exchange_rates
                WHERE from_currency = %s AND to_currency = %s
            """

            result = self.execute_query(
                query, (from_currency, to_currency), fetch_results=True
            )

            if result and result[0]["latest_date"]:
                return result[0]["latest_date"]
            return None

        except psycopg2.Error as e:
            self.logger.error(
                "Failed to get latest exchange rate date for %s/%s: %s",
                from_currency,
                to_currency,
                e,
            )
            return None

    def needs_initial_setup(self) -> bool:
        """Check if database needs initial setup (both stocks and exchange rates are empty)."""
        return (
            self.check_stocks_table_empty() and self.check_exchange_rates_table_empty()
        )

    def get_stock_count(self) -> int:
        """Get the total number of stocks in the database."""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM dim_stocks", fetch_results=True
            )
            return result[0]["count"] if result else 0

        except psycopg2.Error as e:
            self.logger.error("Failed to get stock count: %s", e)
            return 0

    def get_price_record_count(self) -> int:
        """Get the total number of price records in the database."""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM fact_stock_prices", fetch_results=True
            )
            return result[0]["count"] if result else 0

        except psycopg2.Error as e:
            self.logger.error("Failed to get price record count: %s", e)
            return 0

    def get_exchange_rate_count(self) -> int:
        """Get the total number of exchange rate records in the database."""
        try:
            result = self.execute_query(
                "SELECT COUNT(*) as count FROM fact_exchange_rates", fetch_results=True
            )
            return result[0]["count"] if result else 0

        except psycopg2.Error as e:
            self.logger.error("Failed to get exchange rate count: %s", e)
            return 0

    def create_database_schema(self) -> dict[str, Any]:
        """Create database schema by executing DDL files in order.

        Returns:
            Dictionary with execution results and any errors
        """
        results = {"success": False, "ddl_files_executed": [], "errors": []}

        try:
            # Get DDL directory
            current_dir = Path(__file__).parent.parent.parent.parent
            ddl_dir = current_dir / "sql" / "ddl"

            if not ddl_dir.exists():
                results["errors"].append(f"DDL directory not found: {ddl_dir}")
                return results

            # Get all DDL files and sort them by name (ensures 001_, 002_, etc. order)
            ddl_files = sorted([f for f in ddl_dir.glob("*.sql") if f.is_file()])

            if not ddl_files:
                results["errors"].append(f"No DDL files found in {ddl_dir}")
                return results

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for ddl_file in ddl_files:
                        ddl_path = ddl_dir / ddl_file

                        with open(ddl_path, "r", encoding="utf-8") as f:
                            ddl_content = f.read()

                        # Split DDL content into individual statements
                        # Remove comments and empty lines, then split by semicolon
                        statements = []
                        for stmt in ddl_content.split(";"):
                            # Clean up statement - remove comments and whitespace
                            cleaned_stmt = []
                            for line in stmt.split("\n"):
                                line = line.strip()
                                if line and not line.startswith("--"):
                                    cleaned_stmt.append(line)

                            cleaned = " ".join(cleaned_stmt).strip()
                            if cleaned:  # Only add non-empty statements
                                statements.append(cleaned)

                        # Execute each statement separately
                        try:
                            for i, statement in enumerate(statements):
                                self.logger.debug(
                                    "Executing statement %d from %s: %s",
                                    i + 1,
                                    ddl_file,
                                    statement[:100] + "...",
                                )
                                cursor.execute(statement)
                                conn.commit()

                            results["ddl_files_executed"].append(ddl_file.name)
                            self.logger.info(
                                "Successfully executed: %s (%d statements)",
                                ddl_file.name,
                                len(statements),
                            )

                        except psycopg2.Error as e:
                            error_msg = f"Failed to execute {ddl_file.name}: {e}"
                            results["errors"].append(error_msg)
                            self.logger.error(error_msg)
                            # Continue with next file instead of failing completely
                            continue

            results["success"] = len(results["ddl_files_executed"]) > 0

        except (psycopg2.Error, FileNotFoundError, IOError) as e:
            error_msg = f"Schema creation failed: {e}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def teardown_database_schema(self) -> dict[str, Any]:
        """Drop all tables, views, and database objects.

        Returns:
            Dictionary with teardown results and any errors
        """
        results = {"success": False, "objects_dropped": [], "errors": []}

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get all tables in the public schema
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """)
                    tables = [row[0] for row in cursor.fetchall()]

                    # Get all views in the public schema
                    cursor.execute("""
                        SELECT viewname FROM pg_views 
                        WHERE schemaname = 'public'
                        ORDER BY viewname
                    """)
                    views = [row[0] for row in cursor.fetchall()]

                    # Drop views first (they may depend on tables)
                    for view in views:
                        try:
                            cursor.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
                            conn.commit()
                            results["objects_dropped"].append(f"view:{view}")
                            self.logger.info("Dropped view: %s", view)
                        except psycopg2.Error as e:
                            error_msg = f"Failed to drop view {view}: {e}"
                            results["errors"].append(error_msg)
                            self.logger.warning(error_msg)

                    # Drop tables
                    for table in tables:
                        try:
                            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                            conn.commit()
                            results["objects_dropped"].append(f"table:{table}")
                            self.logger.info("Dropped table: %s", table)
                        except psycopg2.Error as e:
                            error_msg = f"Failed to drop table {table}: {e}"
                            results["errors"].append(error_msg)
                            self.logger.warning(error_msg)

                    # Drop any remaining sequences, functions, etc.
                    try:
                        cursor.execute("""
                            SELECT sequence_name FROM information_schema.sequences 
                            WHERE sequence_schema = 'public'
                        """)
                        sequences = [row[0] for row in cursor.fetchall()]

                        for sequence in sequences:
                            cursor.execute(
                                f"DROP SEQUENCE IF EXISTS {sequence} CASCADE"
                            )
                            conn.commit()
                            results["objects_dropped"].append(f"sequence:{sequence}")
                            self.logger.info("Dropped sequence: %s", sequence)

                    except psycopg2.Error as e:
                        error_msg = f"Failed to drop sequences: {e}"
                        results["errors"].append(error_msg)
                        self.logger.warning(error_msg)

                    results["success"] = True
                    self.logger.info("Database schema teardown completed")

        except psycopg2.Error as e:
            error_msg = f"Schema teardown failed: {e}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def is_database_empty(self) -> bool:
        """Check if database is empty (alias for needs_initial_setup for backward compatibility).

        Returns:
            True if database needs initial setup
        """
        return self.needs_initial_setup()

    def health_check(self) -> dict[str, Any]:
        """Perform database health check.

        Returns:
            Dictionary with health check results
        """
        try:
            # Parse database URL for display
            parsed = urllib.parse.urlparse(self.connection_string)
            db_display_url = f"postgresql://{parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}"

            # Test connection
            if not self.test_connection():
                return {
                    "status": "offline",
                    "error": "Connection failed",
                    "database_url": db_display_url,
                }

            # Get record counts
            stock_count = self.get_stock_count()
            price_count = self.get_price_record_count()
            currency_count = self.get_exchange_rate_count()

            # Get latest dates
            latest_stock = None
            latest_currency = None

            try:
                # Get latest stock date for any symbol
                result = self.execute_query(
                    "SELECT MAX(sp.date) as latest_date FROM fact_stock_prices sp",
                    fetch_results=True,
                )
                if result and result[0]["latest_date"]:
                    latest_stock = result[0]["latest_date"]
            except psycopg2.Error:
                pass

            try:
                # Get latest currency date
                result = self.execute_query(
                    "SELECT MAX(date) as latest_date FROM fact_exchange_rates",
                    fetch_results=True,
                )
                if result and result[0]["latest_date"]:
                    latest_currency = result[0]["latest_date"]
            except psycopg2.Error:
                pass

            return {
                "status": "online",
                "database_url": db_display_url,
                "stock_records": stock_count,
                "price_records": price_count,
                "currency_records": currency_count,
                "latest_stock_date": latest_stock.isoformat() if latest_stock else None,
                "latest_currency_date": latest_currency.isoformat()
                if latest_currency
                else None,
                "is_empty": self.is_database_empty(),
            }

        except Exception as e:
            # Parse database URL for display in error case too
            parsed = urllib.parse.urlparse(self.connection_string)
            db_display_url = f"postgresql://{parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}"

            return {"status": "error", "error": str(e), "database_url": db_display_url}

    def insert_stock_data(self, records: list[dict[str, Any]]) -> int:
        """Insert stock data records into raw_stock_data table.

        Args:
            records: List of stock data records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        try:
            # Insert into raw_stock_data table
            self.bulk_insert("raw_stock_data", records, on_conflict="NOTHING")
            self.logger.info("Inserted %d stock data records", len(records))
            return len(records)
        except Exception as e:
            self.logger.error("Failed to insert stock data: %s", e)
            return 0

    def insert_currency_data(self, records: list[dict[str, Any]]) -> int:
        """Insert currency data records into raw_currency_data table.

        Args:
            records: List of currency data records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        try:
            # Insert into raw_currency_data table
            self.bulk_insert("raw_currency_data", records, on_conflict="NOTHING")
            self.logger.info("Inserted %d currency data records", len(records))
            return len(records)
        except Exception as e:
            self.logger.error("Failed to insert currency data: %s", e)
            return 0

    def get_missing_dates_for_symbol(
        self, symbol: str, days_back: int = 10
    ) -> list[datetime]:
        """Get list of missing dates for a symbol within the last N days.

        Args:
            symbol: Stock symbol to check
            days_back: Number of days to check back

        Returns:
            List of missing dates (simplified - just returns empty list for now)
        """
        # Simplified implementation - in a full implementation, this would check
        # for missing business days in the date range
        self.logger.info(
            "Checking missing dates for %s (last %d days)", symbol, days_back
        )
        return []

    def test_connection(self) -> bool:
        """Test the PostgreSQL database connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except psycopg2.Error as e:
            self.logger.error("Database connection test failed: %s", e)
            return False
