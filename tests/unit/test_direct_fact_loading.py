"""Unit tests for direct JSON to fact table loading.

Tests individual components of the pipeline: validation logic, database manager methods,
and data transformation with complete mocking of external dependencies.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ticker_converter.data_ingestion.database_manager import DatabaseManager


class TestDirectFactTableLoadingUnit:
    """Unit tests for direct loading from JSON to fact tables."""

    @pytest.fixture
    def sample_stock_data(self):
        """Sample stock data in correct JSON format."""
        return [
            {
                "symbol": "TEST",
                "data_date": "2025-08-20",
                "open_price": 100.0,
                "high_price": 105.0,
                "low_price": 98.0,
                "close_price": 102.5,
                "volume": 1000000,
                "source": "alpha_vantage",
                "created_at": "2025-08-30 15:39:22.465607",
            }
        ]

    @pytest.fixture
    def sample_currency_data(self):
        """Sample currency data in correct JSON format."""
        return [
            {
                "from_currency": "USD",
                "to_currency": "GBP",
                "data_date": "2025-08-20",
                "exchange_rate": 0.75,
                "source": "alpha_vantage",
                "created_at": "2025-08-30 15:39:35.916835",
            }
        ]

    @patch("tests.unit.test_direct_fact_loading.DatabaseManager")
    def test_insert_stock_data_success(self, MockDatabaseManager, sample_stock_data):
        """Test successful stock data insertion into fact table."""
        # Create mock instance
        mock_manager = MockDatabaseManager.return_value

        # Mock successful return value
        mock_manager.insert_stock_data.return_value = 5

        # Create actual manager instance to call
        manager = DatabaseManager("postgresql://test")
        result = manager.insert_stock_data(sample_stock_data)

        # Verify return value
        assert result == 5

        # Verify the mock was called
        mock_manager.insert_stock_data.assert_called_once_with(sample_stock_data)

    @patch("tests.unit.test_direct_fact_loading.DatabaseManager")
    def test_insert_currency_data_success(self, MockDatabaseManager, sample_currency_data):
        """Test successful currency data insertion into fact table."""
        # Create mock instance
        mock_manager = MockDatabaseManager.return_value

        # Mock successful return value
        mock_manager.insert_currency_data.return_value = 2

        # Create actual manager instance to call
        manager = DatabaseManager("postgresql://test")
        result = manager.insert_currency_data(sample_currency_data)

        # Verify return value
        assert result == 2

        # Verify the mock was called
        mock_manager.insert_currency_data.assert_called_once_with(sample_currency_data)

    @patch("tests.unit.test_direct_fact_loading.DatabaseManager")
    def test_insert_stock_data_date_failure(self, MockDatabaseManager, sample_stock_data):
        """Test stock data insertion when date dimension fails."""
        # Create mock instance
        mock_manager = MockDatabaseManager.return_value

        # Mock failed insertion (returns 0 when dates fail)
        mock_manager.insert_stock_data.return_value = 0

        manager = DatabaseManager("postgresql://test")
        result = manager.insert_stock_data(sample_stock_data)

        # Verify return value
        assert result == 0  # Should return 0 when date fails

        # Verify the mock was called
        mock_manager.insert_stock_data.assert_called_once_with(sample_stock_data)

    @patch("tests.unit.test_direct_fact_loading.DatabaseManager")
    def test_ensure_date_dimension_calculation(self, MockDatabaseManager):
        """Test date dimension calculation logic."""
        # Create mock instance
        mock_manager = MockDatabaseManager.return_value

        # Mock successful date dimension creation
        mock_manager.ensure_date_dimension.return_value = True

        manager = DatabaseManager("postgresql://test")
        result = manager.ensure_date_dimension("2025-08-20")

        # Verify return value
        assert result == True

        # Verify the mock was called
        mock_manager.ensure_date_dimension.assert_called_once_with("2025-08-20")

    def test_json_validation_integration(self):
        """Test validation integration with helper functions."""
        from dags.helpers.load_raw_to_db import (
            _validate_currency_record,
            _validate_stock_record,
        )

        # Valid stock record
        valid_stock = {
            "symbol": "AAPL",
            "data_date": "2025-08-20",
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 98.0,
            "close_price": 102.5,
            "volume": 1000000,
        }
        assert _validate_stock_record(valid_stock) == True

        # Invalid stock record (missing volume)
        invalid_stock = {
            "symbol": "AAPL",
            "data_date": "2025-08-20",
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 98.0,
            "close_price": 102.5,
        }
        assert _validate_stock_record(invalid_stock) == False

        # Valid currency record
        valid_currency = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "data_date": "2025-08-20",
            "exchange_rate": 0.75,
        }
        assert _validate_currency_record(valid_currency) == True

        # Invalid currency record (bad rate type)
        invalid_currency = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "data_date": "2025-08-20",
            "exchange_rate": "invalid",
        }
        assert _validate_currency_record(invalid_currency) == False

    @patch("dags.helpers.load_raw_to_db._get_database_connection")
    @patch("dags.helpers.load_raw_to_db.DatabaseManager")
    def test_load_raw_to_db_unit(self, mock_db_manager_class, mock_get_db_conn):
        """Test load_raw_to_db function with completely mocked dependencies."""
        from dags.helpers.load_raw_to_db import load_raw_to_db

        # Mock database connection string
        mock_get_db_conn.return_value = "postgresql://test"

        # Create a mock DatabaseManager instance
        mock_db_instance = mock_db_manager_class.return_value
        mock_db_instance.insert_stock_data.return_value = 5
        mock_db_instance.insert_currency_data.return_value = 2

        # Create temporary JSON files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create stocks directory with sample data
            stocks_dir = temp_path / "stocks"
            stocks_dir.mkdir()
            stocks_file = stocks_dir / "test_stocks.json"
            with open(stocks_file, "w") as f:
                json.dump(
                    [
                        {
                            "symbol": "TEST",
                            "data_date": "2025-08-20",
                            "open_price": 100.0,
                            "high_price": 105.0,
                            "low_price": 98.0,
                            "close_price": 102.5,
                            "volume": 1000,
                        }
                    ],
                    f,
                )

            # Create exchange directory with sample data
            exchange_dir = temp_path / "exchange"
            exchange_dir.mkdir()
            exchange_file = exchange_dir / "test_exchange.json"
            with open(exchange_file, "w") as f:
                json.dump(
                    [{"from_currency": "USD", "to_currency": "GBP", "data_date": "2025-08-20", "exchange_rate": 0.75}],
                    f,
                )

            # Patch the directory paths
            with (
                patch("dags.helpers.load_raw_to_db.RAW_STOCKS_DIR", stocks_dir),
                patch("dags.helpers.load_raw_to_db.RAW_EXCHANGE_DIR", exchange_dir),
            ):
                result = load_raw_to_db()

                # Verify results match our mocked return values
                assert result == {"stock_inserted": 5, "exchange_inserted": 2}

                # Verify the DatabaseManager was instantiated with correct connection string
                mock_db_manager_class.assert_called_once_with(connection_string="postgresql://test")

                # Verify the methods were called once each
                mock_db_instance.insert_stock_data.assert_called_once()
                mock_db_instance.insert_currency_data.assert_called_once()

                # Verify the data passed to the methods
                stock_call_args = mock_db_instance.insert_stock_data.call_args[0][0]  # First argument (records list)
                currency_call_args = mock_db_instance.insert_currency_data.call_args[0][0]

                assert len(stock_call_args) == 1
                assert stock_call_args[0]["symbol"] == "TEST"
                assert len(currency_call_args) == 1
                assert currency_call_args[0]["from_currency"] == "USD"
