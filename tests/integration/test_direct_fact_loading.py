"""Integration tests for direct JSON to fact table loading.

Tests the complete pipeline: JSON data → validation → fact table insertion
without using raw table intermediary layer.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ticker_converter.data_ingestion.database_manager import DatabaseManager


class TestDirectFactTableLoading:
    """Test direct loading from JSON to fact tables."""

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
                "created_at": "2025-08-30 15:39:22.465607"
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
                "created_at": "2025-08-30 15:39:35.916835"
            }
        ]

    @patch.object(DatabaseManager, 'ensure_date_dimension')
    @patch.object(DatabaseManager, 'connection')
    def test_insert_stock_data_success(self, mock_connection, mock_ensure_date, sample_stock_data):
        """Test successful stock data insertion into fact table."""
        # Mock successful date dimension insertion
        mock_ensure_date.return_value = True
        
        # Mock database connection and cursor
        mock_conn = mock_connection.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.rowcount = 1

        manager = DatabaseManager("postgresql://test")
        result = manager.insert_stock_data(sample_stock_data)

        assert result == 1
        mock_ensure_date.assert_called_once_with("2025-08-20")

    @patch.object(DatabaseManager, 'ensure_date_dimension')
    @patch.object(DatabaseManager, 'connection')
    def test_insert_currency_data_success(self, mock_connection, mock_ensure_date, sample_currency_data):
        """Test successful currency data insertion into fact table."""
        # Mock successful date dimension insertion
        mock_ensure_date.return_value = True
        
        # Mock database connection and cursor
        mock_conn = mock_connection.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.rowcount = 1

        manager = DatabaseManager("postgresql://test")
        result = manager.insert_currency_data(sample_currency_data)

        assert result == 1
        mock_ensure_date.assert_called_once_with("2025-08-20")

    @patch.object(DatabaseManager, 'ensure_date_dimension')
    def test_insert_stock_data_date_failure(self, mock_ensure_date, sample_stock_data):
        """Test stock data insertion when date dimension fails."""
        # Mock failed date dimension insertion
        mock_ensure_date.return_value = False

        manager = DatabaseManager("postgresql://test")
        result = manager.insert_stock_data(sample_stock_data)

        assert result == 0  # Should return 0 when date fails
        mock_ensure_date.assert_called_once_with("2025-08-20")

    def test_ensure_date_dimension_calculation(self):
        """Test date dimension calculation logic."""
        from datetime import datetime
        
        with patch.object(DatabaseManager, 'connection') as mock_connection:
            mock_conn = mock_connection.return_value.__enter__.return_value
            mock_cursor = mock_conn.cursor.return_value

            manager = DatabaseManager("postgresql://test")
            result = manager.ensure_date_dimension("2025-08-20")

            # Should have been called with proper date components
            mock_cursor.execute.assert_called_once()
            
            # Extract the actual call arguments
            call_args = mock_cursor.execute.call_args
            query, params = call_args[0]
            
            # Verify query targets dim_date
            assert "INSERT INTO dim_date" in query
            
            # Verify date calculations (Wednesday, Aug 20, 2025)
            date_obj, year, quarter, month, day, day_of_week, day_of_year, week_of_year, is_weekend = params
            
            assert year == 2025
            assert month == 8
            assert day == 20
            assert quarter == 3  # August is Q3
            assert day_of_week == 3  # Wednesday (1=Monday)
            assert is_weekend == False
            assert result == True

    def test_json_validation_integration(self):
        """Test validation integration with helper functions."""
        from dags.helpers.load_raw_to_db import _validate_stock_record, _validate_currency_record
        
        # Valid stock record
        valid_stock = {
            "symbol": "AAPL",
            "data_date": "2025-08-20",
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 98.0,
            "close_price": 102.5,
            "volume": 1000000
        }
        assert _validate_stock_record(valid_stock) == True
        
        # Invalid stock record (missing volume)
        invalid_stock = {
            "symbol": "AAPL",
            "data_date": "2025-08-20",
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 98.0,
            "close_price": 102.5
        }
        assert _validate_stock_record(invalid_stock) == False
        
        # Valid currency record
        valid_currency = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "data_date": "2025-08-20",
            "exchange_rate": 0.75
        }
        assert _validate_currency_record(valid_currency) == True
        
        # Invalid currency record (bad rate type)
        invalid_currency = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "data_date": "2025-08-20",
            "exchange_rate": "invalid"
        }
        assert _validate_currency_record(invalid_currency) == False

    @patch('dags.helpers.load_raw_to_db._get_database_connection')
    @patch.object(DatabaseManager, 'insert_stock_data')
    @patch.object(DatabaseManager, 'insert_currency_data')
    def test_load_raw_to_db_integration(self, mock_insert_currency, mock_insert_stock, mock_get_db_conn):
        """Test complete load_raw_to_db function integration."""
        from dags.helpers.load_raw_to_db import load_raw_to_db
        
        # Mock database connection
        mock_get_db_conn.return_value = "postgresql://test"
        
        # Mock successful insertions
        mock_insert_stock.return_value = 5
        mock_insert_currency.return_value = 2
        
        # Create temporary JSON files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create stocks directory with sample data
            stocks_dir = temp_path / "stocks"
            stocks_dir.mkdir()
            stocks_file = stocks_dir / "test_stocks.json"
            with open(stocks_file, 'w') as f:
                json.dump([{"symbol": "TEST", "data_date": "2025-08-20", "open_price": 100.0, 
                           "high_price": 105.0, "low_price": 98.0, "close_price": 102.5, "volume": 1000}], f)
            
            # Create exchange directory with sample data
            exchange_dir = temp_path / "exchange"
            exchange_dir.mkdir()
            exchange_file = exchange_dir / "test_exchange.json"
            with open(exchange_file, 'w') as f:
                json.dump([{"from_currency": "USD", "to_currency": "GBP", 
                           "data_date": "2025-08-20", "exchange_rate": 0.75}], f)
            
            # Patch the directory paths
            with patch('dags.helpers.load_raw_to_db.RAW_STOCKS_DIR', stocks_dir), \
                 patch('dags.helpers.load_raw_to_db.RAW_EXCHANGE_DIR', exchange_dir):
                
                result = load_raw_to_db()
                
                # Verify results
                assert result == {"stock_inserted": 5, "exchange_inserted": 2}
                mock_insert_stock.assert_called_once()
                mock_insert_currency.assert_called_once()
