"""Comprehensive tests for DatabaseManager module.

This module provides comprehensive testing for database management functionality,
covering connection management, CRUD operations, transaction handling, and error scenarios.
"""

import sqlite3
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import psycopg2
import pytest

from src.ticker_converter.data_ingestion.database_manager import DatabaseManager


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization and configuration."""

    def test_init_with_sqlite_connection_string(self) -> None:
        """Test initialization with SQLite connection string."""
        manager = DatabaseManager("sqlite:///test.db")
        assert manager.connection_string == "sqlite:///test.db"
        assert manager.is_sqlite is True

    def test_init_with_postgres_connection_string(self) -> None:
        """Test initialization with PostgreSQL connection string."""
        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        assert manager.connection_string == "postgresql://user:pass@localhost/db"
        assert manager.is_sqlite is False

    @patch("src.ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_with_config_url(self, mock_config: Mock) -> None:
        """Test default connection when config has DATABASE_URL."""
        mock_config.DATABASE_URL = "postgresql://configured:url@localhost/db"

        manager = DatabaseManager()
        assert manager.connection_string == "postgresql://configured:url@localhost/db"
        assert manager.is_sqlite is False

    @patch("src.ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_no_database_url(self, mock_config: Mock) -> None:
        """Test error when no config DATABASE_URL is provided."""
        # Mock config without DATABASE_URL
        mock_config.DATABASE_URL = None

        # Should raise RuntimeError when no DATABASE_URL is configured
        with pytest.raises(RuntimeError, match="DATABASE_URL is required but not configured"):
            DatabaseManager()

    def test_init_with_none_connection_uses_default(self) -> None:
        """Test initialization with None connection string uses default."""
        with patch.object(
            DatabaseManager,
            "_get_default_connection",
            return_value="sqlite:///default.db",
        ):
            manager = DatabaseManager(None)
            assert manager.connection_string == "sqlite:///default.db"


class TestDatabaseConnection:
    """Test database connection management."""

    @patch("src.ticker_converter.data_ingestion.database_manager.sqlite3")
    def test_get_connection_sqlite(self, mock_sqlite3: Mock) -> None:
        """Test getting SQLite connection."""
        mock_connection = MagicMock()
        mock_sqlite3.connect.return_value = mock_connection

        manager = DatabaseManager("sqlite:///test.db")
        connection = manager.get_connection()

        mock_sqlite3.connect.assert_called_once_with("test.db")
        assert connection == mock_connection

    @patch("src.ticker_converter.data_ingestion.database_manager.psycopg2")
    def test_get_connection_postgresql(self, mock_psycopg2: Mock) -> None:
        """Test getting PostgreSQL connection."""
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        connection = manager.get_connection()

        mock_psycopg2.connect.assert_called_once_with("postgresql://user:pass@localhost/db")
        assert connection == mock_connection

    @patch("src.ticker_converter.data_ingestion.database_manager.sqlite3")
    def test_connection_context_manager_success(self, mock_sqlite3: Mock) -> None:
        """Test connection context manager success case."""
        mock_connection = MagicMock()
        mock_sqlite3.connect.return_value = mock_connection

        manager = DatabaseManager("sqlite:///test.db")

        with manager.connection() as conn:
            assert conn == mock_connection

        mock_connection.close.assert_called_once()

    @patch("src.ticker_converter.data_ingestion.database_manager.sqlite3")
    def test_connection_context_manager_error_handling(self, mock_sqlite3: Mock) -> None:
        """Test connection context manager error handling."""
        mock_connection = MagicMock()
        mock_sqlite3.connect.return_value = mock_connection

        manager = DatabaseManager("sqlite:///test.db")

        with pytest.raises(ValueError):
            with manager.connection() as conn:
                assert conn == mock_connection
                raise ValueError("Test error")

        mock_connection.rollback.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("src.ticker_converter.data_ingestion.database_manager.sqlite3")
    def test_connection_context_manager_no_connection_error(self, mock_sqlite3: Mock) -> None:
        """Test connection context manager when connection fails."""
        mock_sqlite3.connect.side_effect = sqlite3.Error("Connection failed")

        manager = DatabaseManager("sqlite:///test.db")

        with pytest.raises(sqlite3.Error):
            with manager.connection():
                pass


class TestDatabaseQueryOperations:
    """Test database query execution operations."""

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_sqlite_success(self, mock_connection_context: Mock) -> None:
        """Test successful query execution with SQLite."""
        # Mock SQLite connection and cursor
        mock_connection = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        # Mock query results
        mock_row1 = {"id": 1, "symbol": "AAPL"}
        mock_row2 = {"id": 2, "symbol": "GOOGL"}
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]

        manager = DatabaseManager("sqlite:///test.db")
        results = manager.execute_query("SELECT * FROM stocks", ("param1",))

        # Verify query execution
        mock_cursor.execute.assert_called_once_with("SELECT * FROM stocks", ("param1",))
        assert results == [mock_row1, mock_row2]

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_postgresql_success(self, mock_connection_context: Mock) -> None:
        """Test successful query execution with PostgreSQL."""
        # Mock PostgreSQL connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        # Mock query results
        mock_row1 = {"id": 1, "symbol": "AAPL"}
        mock_row2 = {"id": 2, "symbol": "GOOGL"}
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")

        # Mock the psycopg2 isinstance check to return True
        with patch("src.ticker_converter.data_ingestion.database_manager.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True
            results = manager.execute_query("SELECT * FROM stocks", ("param1",))

        # Verify query execution
        mock_cursor.execute.assert_called_once_with("SELECT * FROM stocks", ("param1",))
        assert results == [mock_row1, mock_row2]

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_with_no_parameters(self, mock_connection_context: Mock) -> None:
        """Test query execution without parameters."""
        mock_connection = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        mock_cursor.fetchall.return_value = []

        manager = DatabaseManager("sqlite:///test.db")
        results = manager.execute_query("SELECT COUNT(*) FROM stocks")

        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM stocks", ())
        assert results == []

    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_sqlite_success(self, mock_connection_context: Mock) -> None:
        """Test successful insert operation with SQLite."""
        mock_connection = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [
            {"symbol": "AAPL", "price": 150.0},
            {"symbol": "GOOGL", "price": 2500.0},
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.execute_insert("INSERT INTO stocks VALUES (?, ?)", records)

        mock_cursor.executemany.assert_called_once_with("INSERT INTO stocks VALUES (?, ?)", records)
        mock_connection.commit.assert_called_once()
        assert result == 2

    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_postgresql_success(self, mock_connection_context: Mock) -> None:
        """Test successful insert operation with PostgreSQL."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [
            {"symbol": "AAPL", "price": 150.0},
            {"symbol": "GOOGL", "price": 2500.0},
        ]

        # Mock the execute_values import that happens inside the method
        with patch("psycopg2.extras.execute_values") as mock_execute_values:
            manager = DatabaseManager("postgresql://user:pass@localhost/db")
            result = manager.execute_insert("INSERT INTO stocks VALUES %s", records)

            # Verify execute_values called with correct parameters
            expected_values = [["AAPL", 150.0], ["GOOGL", 2500.0]]
            mock_execute_values.assert_called_once_with(mock_cursor, "INSERT INTO stocks VALUES %s", expected_values)
            mock_connection.commit.assert_called_once()
            assert result == 2

    def test_execute_insert_empty_records(self) -> None:
        """Test insert operation with empty records list."""
        manager = DatabaseManager("sqlite:///test.db")
        result = manager.execute_insert("INSERT INTO stocks VALUES (?, ?)", [])
        assert result == 0


class TestDatabaseStatusChecking:
    """Test database status and validation operations."""

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_true(self, mock_execute_query: Mock) -> None:
        """Test database empty check when database is empty."""
        # Mock empty stock and currency data
        mock_execute_query.side_effect = [
            [{"count": 0}],  # stock count
            [{"count": 0}],  # currency count
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.is_database_empty()

        assert result is True
        assert mock_execute_query.call_count == 2

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_false_with_stock_data(self, mock_execute_query: Mock) -> None:
        """Test database empty check when stock data exists."""
        mock_execute_query.side_effect = [
            [{"count": 5}],  # stock count
            [{"count": 0}],  # currency count
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.is_database_empty()

        assert result is False

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_false_with_currency_data(self, mock_execute_query: Mock) -> None:
        """Test database empty check when currency data exists."""
        mock_execute_query.side_effect = [
            [{"count": 0}],  # stock count
            [{"count": 3}],  # currency count
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.is_database_empty()

        assert result is False

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_error_handling(self, mock_execute_query: Mock) -> None:
        """Test database empty check error handling."""
        mock_execute_query.side_effect = sqlite3.Error("Database connection failed")

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.is_database_empty()

        # Should return True when error occurs
        assert result is True

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_with_symbol(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date for specific symbol."""
        test_date = "2023-08-15"
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_stock_date("AAPL")

        expected_query = """
                SELECT MAX(dd.date_value) as latest_date 
                FROM fact_stock_prices fsp
                JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
                JOIN dim_date dd ON fsp.date_id = dd.date_id
                WHERE ds.symbol = ?
                """
        mock_execute_query.assert_called_once_with(expected_query, ("AAPL",))
        assert result == datetime.strptime(test_date, "%Y-%m-%d")

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_all_symbols(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date for all symbols."""
        test_date = datetime(2023, 8, 15)
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_stock_date()

        expected_query = """
                SELECT MAX(dd.date_value) as latest_date 
                FROM fact_stock_prices fsp
                JOIN dim_date dd ON fsp.date_id = dd.date_id
                """
        mock_execute_query.assert_called_once_with(expected_query, None)
        assert result == test_date

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_no_data(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date when no data exists."""
        mock_execute_query.return_value = [{"latest_date": None}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_stock_date("AAPL")

        assert result is None

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_error_handling(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date error handling."""
        mock_execute_query.side_effect = sqlite3.Error("Database error")

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_stock_date("AAPL")

        assert result is None

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_currency_date_success(self, mock_execute_query: Mock) -> None:
        """Test getting latest currency date successfully."""
        test_date = "2023-08-15"
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_currency_date()

        expected_query = """
            SELECT MAX(dd.date_value) as latest_date 
            FROM fact_currency_rates fcr
            JOIN dim_date dd ON fcr.date_id = dd.date_id
            """
        mock_execute_query.assert_called_once_with(expected_query)
        assert result == datetime.strptime(test_date, "%Y-%m-%d")

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_currency_date_error(self, mock_execute_query: Mock) -> None:
        """Test getting latest currency date with error."""
        mock_execute_query.side_effect = psycopg2.Error("Connection error")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_latest_currency_date()

        assert result is None


class TestDatabaseDataOperations:
    """Test database data insertion and management operations."""

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_stock_data_success(self, mock_execute_insert: Mock) -> None:
        """Test successful stock data insertion."""
        mock_execute_insert.return_value = 2

        records = [
            {
                "symbol": "AAPL",
                "data_date": "2023-08-15",
                "open_price": 175.0,
                "high_price": 177.0,
                "low_price": 174.0,
                "close_price": 176.0,
                "volume": 1000000,
                "source": "alpha_vantage",
                "created_at": datetime.now(),
            }
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.insert_stock_data(records)

        assert result == 2
        mock_execute_insert.assert_called_once()

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_stock_data_postgresql_query(self, mock_execute_insert: Mock) -> None:
        """Test stock data insertion uses correct PostgreSQL query."""
        mock_execute_insert.return_value = 1

        records = [{"symbol": "AAPL", "data_date": "2023-08-15"}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        manager.insert_stock_data(records)

        # Verify PostgreSQL-specific query was used
        call_args = mock_execute_insert.call_args
        query = call_args[0][0]
        assert "VALUES %s" in query
        assert "ON CONFLICT" in query

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_stock_data_empty_records(self, mock_execute_insert: Mock) -> None:
        """Test stock data insertion with empty records."""
        manager = DatabaseManager("sqlite:///test.db")
        result = manager.insert_stock_data([])

        assert result == 0
        mock_execute_insert.assert_not_called()

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_stock_data_error_handling(self, mock_execute_insert: Mock) -> None:
        """Test stock data insertion error handling."""
        mock_execute_insert.side_effect = sqlite3.Error("Insert failed")

        records = [{"symbol": "AAPL", "data_date": "2023-08-15"}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.insert_stock_data(records)

        assert result == 0

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_currency_data_success(self, mock_execute_insert: Mock) -> None:
        """Test successful currency data insertion."""
        mock_execute_insert.return_value = 1

        records = [
            {
                "from_currency": "USD",
                "to_currency": "EUR",
                "data_date": "2023-08-15",
                "exchange_rate": 0.85,
                "source": "alpha_vantage",
                "created_at": datetime.now(),
            }
        ]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.insert_currency_data(records)

        assert result == 1
        mock_execute_insert.assert_called_once()

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_currency_data_postgresql_query(self, mock_execute_insert: Mock) -> None:
        """Test currency data insertion uses correct PostgreSQL query."""
        mock_execute_insert.return_value = 1

        records = [{"from_currency": "USD", "to_currency": "EUR"}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        manager.insert_currency_data(records)

        # Verify PostgreSQL-specific query was used
        call_args = mock_execute_insert.call_args
        query = call_args[0][0]
        assert "VALUES %s" in query
        assert "ON CONFLICT" in query

    @patch.object(DatabaseManager, "execute_insert")
    def test_insert_currency_data_error_handling(self, mock_execute_insert: Mock) -> None:
        """Test currency data insertion error handling."""
        mock_execute_insert.side_effect = psycopg2.Error("Insert failed")

        records = [{"from_currency": "USD", "to_currency": "EUR"}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.insert_currency_data(records)

        assert result == 0


class TestDatabaseMissingDataAnalysis:
    """Test missing data analysis and date calculations."""

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_success(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates for symbol successfully."""
        # Mock existing dates (missing one day in between)
        existing_dates = [
            {"data_date": "2023-08-14"},
            {"data_date": "2023-08-16"},  # Missing 2023-08-15
        ]
        mock_execute_query.return_value = existing_dates

        manager = DatabaseManager("sqlite:///test.db")

        # Test with a 3-day range to ensure we get the missing date
        missing_dates = manager.get_missing_dates_for_symbol("AAPL", days_back=3)

        # Should return missing weekdays
        assert len(missing_dates) > 0
        assert all(isinstance(date, datetime) for date in missing_dates)

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_all_present(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates when all dates are present."""
        # Mock all dates present for last 5 business days
        today = datetime.now().date()
        existing_dates = []

        for i in range(5):
            date = today - timedelta(days=i)
            if date.weekday() < 5:  # Weekdays only
                existing_dates.append({"data_date": date.strftime("%Y-%m-%d")})

        mock_execute_query.return_value = existing_dates

        manager = DatabaseManager("sqlite:///test.db")
        missing_dates = manager.get_missing_dates_for_symbol("AAPL", days_back=5)

        # Should return fewer missing dates since many are present
        assert isinstance(missing_dates, list)

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_error_handling(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates error handling."""
        mock_execute_query.side_effect = sqlite3.Error("Query failed")

        manager = DatabaseManager("sqlite:///test.db")
        missing_dates = manager.get_missing_dates_for_symbol("AAPL", days_back=5)

        assert missing_dates == []

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_handles_datetime_objects(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates handles datetime objects correctly."""
        # Mock existing dates as datetime objects
        existing_dates = [
            {"data_date": datetime(2023, 8, 14).date()},
            {"data_date": datetime(2023, 8, 16).date()},
        ]
        mock_execute_query.return_value = existing_dates

        manager = DatabaseManager("sqlite:///test.db")
        missing_dates = manager.get_missing_dates_for_symbol("AAPL", days_back=3)

        assert isinstance(missing_dates, list)
        assert all(isinstance(date, datetime) for date in missing_dates)


class TestDatabaseHealthCheck:
    """Test database health check functionality."""

    @patch.object(DatabaseManager, "execute_query")
    @patch.object(DatabaseManager, "get_latest_stock_date")
    @patch.object(DatabaseManager, "get_latest_currency_date")
    @patch.object(DatabaseManager, "is_database_empty")
    def test_health_check_success(
        self,
        mock_is_empty: Mock,
        mock_latest_currency: Mock,
        mock_latest_stock: Mock,
        mock_execute_query: Mock,
    ) -> None:
        """Test successful health check."""
        # Mock query results
        mock_execute_query.side_effect = [
            [{"count": 100}],  # stock count
            [{"count": 50}],  # currency count
        ]

        # Mock date results
        mock_stock_date = datetime(2023, 8, 15)
        mock_currency_date = datetime(2023, 8, 14)
        mock_latest_stock.return_value = mock_stock_date
        mock_latest_currency.return_value = mock_currency_date
        mock_is_empty.return_value = False

        # Mock the connection context manager to test the "SELECT 1" query
        with patch.object(DatabaseManager, "get_connection") as mock_get_connection:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            mock_get_connection.return_value.__enter__.return_value = mock_connection
            mock_get_connection.return_value.__exit__.return_value = None

            manager = DatabaseManager("sqlite:///test.db")
            result = manager.health_check()

            # Verify the connection test was performed
            mock_cursor.execute.assert_called_once_with("SELECT 1")

        expected_result = {
            "status": "healthy",
            "stock_records": 100,
            "currency_records": 50,
            "latest_stock_date": mock_stock_date.isoformat(),
            "latest_currency_date": mock_currency_date.isoformat(),
            "is_empty": False,
        }

        assert result == expected_result

    @patch.object(DatabaseManager, "get_connection")
    @patch.object(DatabaseManager, "execute_query")
    @patch.object(DatabaseManager, "get_latest_stock_date")
    @patch.object(DatabaseManager, "get_latest_currency_date")
    @patch.object(DatabaseManager, "is_database_empty")
    def test_health_check_with_none_dates(
        self,
        mock_is_empty: Mock,
        mock_latest_currency: Mock,
        mock_latest_stock: Mock,
        mock_execute_query: Mock,
        mock_get_connection: Mock,
    ) -> None:
        """Test health check when latest dates are None."""
        # Mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        # Mock query results
        mock_execute_query.side_effect = [
            [{"count": 0}],  # stock count
            [{"count": 0}],  # currency count
        ]

        # Mock None date results
        mock_latest_stock.return_value = None
        mock_latest_currency.return_value = None
        mock_is_empty.return_value = True

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.health_check()

        expected_result = {
            "status": "healthy",
            "stock_records": 0,
            "currency_records": 0,
            "latest_stock_date": None,
            "latest_currency_date": None,
            "is_empty": True,
        }

        assert result == expected_result

    @patch.object(DatabaseManager, "get_connection")
    def test_health_check_connection_error(self, mock_get_connection: Mock) -> None:
        """Test health check with connection error."""
        mock_get_connection.side_effect = sqlite3.Error("Connection failed")

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.health_check()

        expected_result = {"status": "error", "error": "Connection failed"}

        assert result == expected_result

    @patch.object(DatabaseManager, "get_connection")
    def test_health_check_postgresql_error(self, mock_get_connection: Mock) -> None:
        """Test health check with PostgreSQL error."""
        mock_get_connection.side_effect = psycopg2.Error("PostgreSQL connection failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.health_check()

        expected_result = {"status": "error", "error": "PostgreSQL connection failed"}

        assert result == expected_result


class TestDatabaseManagerErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_manager_with_invalid_connection_string(self) -> None:
        """Test manager initialization with invalid connection string."""
        manager = DatabaseManager("invalid://connection/string")
        assert manager.connection_string == "invalid://connection/string"
        assert manager.is_sqlite is False

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_with_invalid_query(self, mock_connection_context: Mock) -> None:
        """Test query execution with invalid SQL."""
        mock_connection = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("Invalid SQL syntax")
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("sqlite:///test.db")

        with pytest.raises(sqlite3.Error):
            manager.execute_query("INVALID SQL SYNTAX")

    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_with_constraint_violation(self, mock_connection_context: Mock) -> None:
        """Test insert operation with constraint violation."""
        mock_connection = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_cursor.executemany.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [{"symbol": "AAPL", "price": 150.0}]

        manager = DatabaseManager("sqlite:///test.db")

        with pytest.raises(sqlite3.IntegrityError):
            manager.execute_insert("INSERT INTO stocks VALUES (?, ?)", records)

    @patch("src.ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_config_attribute_error(self, mock_config: Mock) -> None:
        """Test default connection when config doesn't have DATABASE_URL attribute."""
        # Mock config without DATABASE_URL attribute
        delattr(mock_config, "DATABASE_URL")

        # Should raise RuntimeError when no DATABASE_URL is configured
        with pytest.raises(RuntimeError, match="DATABASE_URL is required but not configured"):
            DatabaseManager()

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_value_error(self, mock_execute_query: Mock) -> None:
        """Test get_latest_stock_date with invalid date format."""
        mock_execute_query.return_value = [{"latest_date": "invalid-date-format"}]

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_stock_date("AAPL")

        assert result is None

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_currency_date_type_error(self, mock_execute_query: Mock) -> None:
        """Test get_latest_currency_date with invalid data type."""
        mock_execute_query.return_value = [{"latest_date": 12345}]  # Invalid type

        manager = DatabaseManager("sqlite:///test.db")
        result = manager.get_latest_currency_date()

        assert result is None
