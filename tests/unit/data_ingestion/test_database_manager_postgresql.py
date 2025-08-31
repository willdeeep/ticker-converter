"""PostgreSQL-focused tests for DatabaseManager module.

This module provides comprehensive testing for PostgreSQL database management functionality,
covering connection management, CRUD operations, transaction handling, and error scenarios.
Updated to match the new PostgreSQL-only implementation.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import psycopg2
import pytest

from src.ticker_converter.data_ingestion.database_manager import DatabaseManager


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization and configuration."""

    def test_init_with_postgres_connection_string(self) -> None:
        """Test initialization with PostgreSQL connection string."""
        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        assert manager.connection_string == "postgresql://user:pass@localhost/db"

    @patch("src.ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_with_config_url(self, mock_config: Mock) -> None:
        """Test default connection when config has DATABASE_URL."""
        mock_config.DATABASE_URL = "postgresql://configured:url@localhost/db"

        manager = DatabaseManager()
        assert manager.connection_string == "postgresql://configured:url@localhost/db"

    @patch("src.ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_no_database_url(self, mock_config: Mock) -> None:
        """Test error when no config DATABASE_URL is provided."""
        # Mock config without DATABASE_URL
        mock_config.DATABASE_URL = None

        # Should raise RuntimeError when no DATABASE_URL is configured
        with pytest.raises(RuntimeError, match="DATABASE_URL is required but not configured"):
            DatabaseManager()

    def test_init_with_none_connection_uses_default(self) -> None:
        """Test initialization with None uses default connection."""
        with patch("src.ticker_converter.data_ingestion.database_manager.config") as mock_config:
            mock_config.DATABASE_URL = "postgresql://default:url@localhost/db"
            manager = DatabaseManager(None)
            assert manager.connection_string == "postgresql://default:url@localhost/db"


class TestDatabaseConnection:
    """Test database connection management."""

    @patch("src.ticker_converter.data_ingestion.database_manager.psycopg2")
    def test_get_connection_postgres(self, mock_psycopg2: Mock) -> None:
        """Test getting PostgreSQL connection."""
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_connection()

        mock_psycopg2.connect.assert_called_once_with("postgresql://user:pass@localhost/db")
        assert result == mock_connection

    @patch("src.ticker_converter.data_ingestion.database_manager.psycopg2")
    def test_connection_context_manager_success(self, mock_psycopg2: Mock) -> None:
        """Test successful connection context manager."""
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")

        with manager.connection() as conn:
            assert conn == mock_connection

        mock_connection.close.assert_called_once()

    @patch("src.ticker_converter.data_ingestion.database_manager.psycopg2")
    def test_connection_context_manager_error_handling(self, mock_psycopg2: Mock) -> None:
        """Test connection context manager error handling."""
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")

        with pytest.raises(ValueError):
            with manager.connection():
                raise ValueError("Test error")

        mock_connection.rollback.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("src.ticker_converter.data_ingestion.database_manager.psycopg2")
    def test_connection_context_manager_no_connection_error(self, mock_psycopg2: Mock) -> None:
        """Test connection context manager when connection fails."""
        mock_psycopg2.connect.side_effect = psycopg2.Error("Connection failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")

        with pytest.raises(psycopg2.Error):
            with manager.connection():
                pass


class TestDatabaseQueryOperations:
    """Test database query operations."""

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_postgres_success(self, mock_connection_context: Mock) -> None:
        """Test successful PostgreSQL query execution."""
        # Mock the connection with proper psycopg2 type
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection

        # Mock the RealDictCursor context manager
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.execute_query("SELECT * FROM test_table", ("param1",))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", ("param1",))
        assert result == [{"id": 1, "name": "test"}]

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_with_no_parameters(self, mock_connection_context: Mock) -> None:
        """Test query execution without parameters."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection

        # Mock the RealDictCursor context manager
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.execute_query("SELECT COUNT(*) FROM test_table")

        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM test_table", ())
        assert result == []

    @patch("psycopg2.extras.execute_values")
    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_postgres_success(self, mock_connection_context: Mock, mock_execute_values: Mock) -> None:
        """Test successful PostgreSQL insert operation."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [{"symbol": "AAPL", "price": 150.0}, {"symbol": "MSFT", "price": 200.0}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.execute_insert("INSERT INTO stocks VALUES %s", records)

        assert result == 2
        mock_execute_values.assert_called_once()
        mock_connection.commit.assert_called_once()


class TestDatabaseStatusChecking:
    """Test database status and health checking operations."""

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_with_data(self, mock_execute_query: Mock) -> None:
        """Test database empty check when data exists."""
        mock_execute_query.side_effect = [
            [{"count": 5}],  # stock count
            [{"count": 3}],  # currency count
        ]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.is_database_empty()

        assert result is False

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_no_data(self, mock_execute_query: Mock) -> None:
        """Test database empty check when no data exists."""
        mock_execute_query.side_effect = [
            [{"count": 0}],  # stock count
            [{"count": 0}],  # currency count
        ]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.is_database_empty()

        assert result is True

    @patch.object(DatabaseManager, "execute_query")
    def test_is_database_empty_error_handling(self, mock_execute_query: Mock) -> None:
        """Test database empty check error handling."""
        mock_execute_query.side_effect = psycopg2.Error("Database connection failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.is_database_empty()

        assert result is False  # Implementation returns False on error, not True

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_with_symbol(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date for specific symbol."""
        test_date = datetime(2023, 8, 15)
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_latest_stock_date("AAPL")

        # Verify the PostgreSQL query structure (note: using %s instead of ?)
        call_args = mock_execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "MAX(d.date_value)" in query
        assert "fact_stock_prices" in query
        assert "dim_date" in query
        assert "%s" in query  # PostgreSQL parameter style
        assert params == ("AAPL",)
        assert result == test_date

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_all_symbols(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date for all symbols."""
        test_date = datetime(2023, 8, 15)
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_latest_stock_date()

        call_args = mock_execute_query.call_args
        query = call_args[0][0]

        assert "MAX(d.date_value)" in query
        assert "fact_stock_prices" in query
        assert "dim_date" in query
        assert result == test_date

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_stock_date_error_handling(self, mock_execute_query: Mock) -> None:
        """Test getting latest stock date error handling."""
        mock_execute_query.side_effect = psycopg2.Error("Database error")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_latest_stock_date("AAPL")

        assert result is None

    @patch.object(DatabaseManager, "execute_query")
    def test_get_latest_currency_date_success(self, mock_execute_query: Mock) -> None:
        """Test getting latest currency date successfully."""
        test_date = datetime(2023, 8, 15)
        mock_execute_query.return_value = [{"latest_date": test_date}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_latest_currency_date()

        call_args = mock_execute_query.call_args
        query = call_args[0][0]

        assert "MAX(d.date_value)" in query
        assert "fact_currency_rates" in query
        assert "dim_date" in query
        assert result == test_date


class TestDatabaseDataOperations:
    """Test database data insertion and manipulation operations."""

    @patch.object(DatabaseManager, "connection")
    @patch.object(DatabaseManager, "ensure_date_dimension")
    def test_insert_stock_data_success(self, mock_ensure_date: Mock, mock_connection_context: Mock) -> None:
        """Test successful stock data insertion."""
        # Mock ensure_date_dimension
        mock_ensure_date.return_value = True

        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1  # Each execute returns 1 row
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

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
            },
            {
                "symbol": "GOOGL",
                "data_date": "2023-08-15",
                "open_price": 2800.0,
                "high_price": 2850.0,
                "low_price": 2790.0,
                "close_price": 2820.0,
                "volume": 500000,
                "source": "alpha_vantage",
                "created_at": datetime.now(),
            },
        ]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.insert_stock_data(records)

        assert result == 2  # Should insert 2 records
        mock_ensure_date.assert_any_call("2023-08-15")
        assert mock_cursor.execute.call_count == 2  # One call per record
        mock_connection.commit.assert_called_once()

    @patch.object(DatabaseManager, "connection")
    @patch.object(DatabaseManager, "ensure_date_dimension")
    def test_insert_stock_data_postgresql_query(self, mock_ensure_date: Mock, mock_connection_context: Mock) -> None:
        """Test stock data insertion uses correct PostgreSQL query."""
        mock_ensure_date.return_value = True

        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [
            {
                "symbol": "AAPL",
                "data_date": "2023-08-15",
                "open_price": 150.0,
                "high_price": 155.0,
                "low_price": 149.0,
                "close_price": 153.0,
                "volume": 1000,
            }
        ]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.insert_stock_data(records)

        # Verify PostgreSQL-specific query was used
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]

        assert "INSERT INTO fact_stock_prices" in query
        assert "ON CONFLICT" in query  # PostgreSQL upsert
        assert "DO UPDATE SET" in query
        assert result == 1

    @patch.object(DatabaseManager, "connection")
    @patch.object(DatabaseManager, "ensure_date_dimension")
    def test_insert_currency_data_success(self, mock_ensure_date: Mock, mock_connection_context: Mock) -> None:
        """Test successful currency data insertion."""
        mock_ensure_date.return_value = True

        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

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

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.insert_currency_data(records)

        assert result == 1
        mock_ensure_date.assert_called_once_with("2023-08-15")
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

    @patch.object(DatabaseManager, "connection")
    @patch.object(DatabaseManager, "ensure_date_dimension")
    def test_insert_currency_data_postgresql_query(self, mock_ensure_date: Mock, mock_connection_context: Mock) -> None:
        """Test currency data insertion uses correct PostgreSQL query."""
        mock_ensure_date.return_value = True

        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        records = [{"from_currency": "USD", "to_currency": "EUR", "data_date": "2023-08-15", "exchange_rate": 0.85}]

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        manager.insert_currency_data(records)

        # Verify cursor.execute was called with the correct query
        mock_cursor.execute.assert_called_once()
        called_query = mock_cursor.execute.call_args[0][0]

        assert "INSERT INTO fact_currency_rates" in called_query
        assert "ON CONFLICT" in called_query  # PostgreSQL upsert
        assert "DO UPDATE SET" in called_query


class TestDatabaseMissingDataAnalysis:
    """Test missing data analysis operations."""

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_success(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates for symbol successfully."""
        # Mock missing dates query result
        missing_dates = [
            {"date_value": datetime(2023, 8, 15).date()},
            {"date_value": datetime(2023, 8, 16).date()},
        ]
        mock_execute_query.return_value = missing_dates

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_missing_dates_for_symbol("AAPL", days_back=3)

        assert len(result) == 2
        assert result[0] == datetime(2023, 8, 15).date()
        assert result[1] == datetime(2023, 8, 16).date()

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_all_present(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates when all dates are present."""
        # No missing dates
        mock_execute_query.return_value = []

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_missing_dates_for_symbol("AAPL", days_back=5)

        assert result == []

    @patch.object(DatabaseManager, "execute_query")
    def test_get_missing_dates_for_symbol_error_handling(self, mock_execute_query: Mock) -> None:
        """Test getting missing dates error handling."""
        mock_execute_query.side_effect = psycopg2.Error("Query failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.get_missing_dates_for_symbol("AAPL", days_back=5)

        assert result == []


class TestDatabaseHealthCheck:
    """Test database health checking operations."""

    @patch.object(DatabaseManager, "execute_query")
    @patch.object(DatabaseManager, "connection")
    def test_health_check_success(self, mock_connection_context: Mock, mock_execute_query: Mock) -> None:
        """Test successful health check."""
        # Mock connection context manager
        mock_connection = MagicMock()
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        # Mock tables query result
        mock_execute_query.return_value = [
            {"table_name": "fact_stock_prices"},
            {"table_name": "fact_currency_rates"},
            {"table_name": "dim_date"},
        ]

        # Mock the is_database_empty method
        with patch.object(DatabaseManager, "is_database_empty", return_value=False):
            manager = DatabaseManager("postgresql://user:pass@localhost/db")
            result = manager.health_check()

        assert result["database_connected"] is True
        assert result["tables_exist"] is True
        assert result["has_data"] is True
        assert result["error"] is None

    @patch.object(DatabaseManager, "connection")
    def test_health_check_connection_error(self, mock_connection_context: Mock) -> None:
        """Test health check with connection error."""
        mock_connection_context.side_effect = psycopg2.Error("Connection failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.health_check()

        assert result["database_connected"] is False
        assert result["tables_exist"] is False
        assert result["has_data"] is False
        assert "Connection failed" in result["error"]


class TestDatabaseManagerErrorScenarios:
    """Test error scenarios and edge cases."""

    def test_manager_with_invalid_connection_string(self) -> None:
        """Test manager initialization with invalid connection string."""
        manager = DatabaseManager("invalid://connection/string")
        assert manager.connection_string == "invalid://connection/string"

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_with_invalid_query(self, mock_connection_context: Mock) -> None:
        """Test query execution with invalid SQL."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Invalid SQL syntax")

        # Mock the cursor context manager properly
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")

        with pytest.raises(psycopg2.Error):
            manager.execute_query("INVALID SQL SYNTAX")

    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_with_constraint_violation(self, mock_connection_context: Mock) -> None:
        """Test insert operation with constraint violation."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        # Mock execute_values to raise constraint violation
        with patch("psycopg2.extras.execute_values") as mock_execute_values:
            mock_execute_values.side_effect = psycopg2.IntegrityError("UNIQUE constraint failed")

            records = [{"symbol": "AAPL", "price": 150.0}]
            manager = DatabaseManager("postgresql://user:pass@localhost/db")

            with pytest.raises(psycopg2.IntegrityError):
                manager.execute_insert("INSERT INTO stocks VALUES %s", records)
