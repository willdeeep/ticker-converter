"""PostgreSQL-focused tests for DatabaseManager module."""

import os
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import psycopg2
import psycopg2.extras
import psycopg2.extensions
import pytest

from src.ticker_converter.data_ingestion.database_manager import DatabaseManager

# Mock the API key for tests
os.environ["ALPHA_VANTAGE_API_KEY"] = "test_api_key"


class TestDatabaseManagerInitialization:
    """Test database manager initialization with PostgreSQL connections."""

    def test_init_with_postgres_connection_string(self) -> None:
        """Test initialization with PostgreSQL connection string."""
        connection_string = "postgresql://user:pass@localhost:5432/testdb"
        manager = DatabaseManager(connection_string)
        assert manager.connection_string == connection_string

    def test_init_with_different_postgres_params(self) -> None:
        """Test initialization with different PostgreSQL parameters."""
        connection_string = "postgresql://admin:secret@production.db:5432/prod_db"
        manager = DatabaseManager(connection_string)
        assert manager.connection_string == connection_string


class TestDatabaseQueryOperations:
    """Test database query operations."""

    @patch.object(DatabaseManager, "connection")
    def test_execute_query_postgres_success(self, mock_connection_context: Mock) -> None:
        """Test successful PostgreSQL query execution."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        
        # Mock the RealDictCursor context manager
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.execute_query("SELECT * FROM test_table", ("param1",))

        assert result == [{"id": 1, "name": "test"}]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", ("param1",))

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

        assert result == []
        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM test_table", ())

    @patch("psycopg2.extras.execute_values")
    @patch.object(DatabaseManager, "connection")
    def test_execute_insert_postgres_success(self, mock_connection_context: Mock, mock_execute_values: Mock) -> None:
        """Test successful PostgreSQL insert execution."""
        mock_connection = MagicMock()
        mock_connection.__class__ = psycopg2.extensions.connection
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_context.return_value.__enter__.return_value = mock_connection

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        records = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}, {"id": 3, "name": "test3"}]
        result = manager.execute_insert("INSERT INTO test_table (id, name) VALUES %s", records)

        assert result == 3
        mock_execute_values.assert_called_once()


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
    def test_is_database_empty_error(self, mock_execute_query: Mock) -> None:
        """Test database empty check with query error."""
        mock_execute_query.side_effect = psycopg2.Error("Connection failed")

        manager = DatabaseManager("postgresql://user:pass@localhost/db")
        result = manager.is_database_empty()

        assert result is False  # Returns False on error as documented
