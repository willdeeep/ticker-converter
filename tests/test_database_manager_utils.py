"""Tests for database manager utilities."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ticker_converter.data_ingestion.database_manager import DatabaseManager


class TestDatabaseManagerInit:
    """Test DatabaseManager initialization and utility methods."""

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

    @patch("ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_with_config_url(self, mock_config: Any) -> None:
        """Test default connection when config has DATABASE_URL."""
        mock_config.DATABASE_URL = "postgresql://configured:url@localhost/db"

        manager = DatabaseManager()
        assert manager.connection_string == "postgresql://configured:url@localhost/db"

    @patch("ticker_converter.data_ingestion.database_manager.config")
    def test_get_default_connection_no_database_url(self, mock_config: Any) -> None:
        """Test error when no config DATABASE_URL is provided."""
        # Mock config without DATABASE_URL
        mock_config.DATABASE_URL = None

        # Should raise RuntimeError when no DATABASE_URL is configured
        with pytest.raises(RuntimeError, match="DATABASE_URL is required but not configured"):
            DatabaseManager()
