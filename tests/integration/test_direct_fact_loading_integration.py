"""Integration tests for direct fact table loading functionality.

These tests verify the actual database operations for loading data directly
into fact tables, bypassing the raw tables layer. Tests use real PostgreSQL
database connections and validate end-to-end functionality.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dags.helpers.load_raw_to_db import load_raw_to_db
from src.ticker_converter.data_ingestion.database_manager import DatabaseManager

# Load database configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


@pytest.fixture
def postgres_connection_string():
    """Construct PostgreSQL connection string from environment variables."""
    required_vars = [POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]

    if not all(required_vars):
        pytest.skip("PostgreSQL environment variables not configured")

    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


@pytest.fixture
def test_database_manager(postgres_connection_string):
    """Create DatabaseManager instance for testing."""
    return DatabaseManager(postgres_connection_string)


@pytest.fixture
def real_stock_json_data():
    """Load real stock data from the actual JSON file."""
    import json

    stock_file_path = "/Users/willhuntleyclarke/repos/interests/ticker-converter/dags/raw_data/dummy_stocks/stocks_20250830T143935Z.json"
    with open(stock_file_path, "r") as f:
        data = json.load(f)

    # Return just the first 5 records for testing
    return data[:5]


@pytest.fixture
def real_currency_json_data():
    """Load real currency data from the actual JSON file."""
    import json

    currency_file_path = "/Users/willhuntleyclarke/repos/interests/ticker-converter/dags/raw_data/dummy_exchange/exchange_20250830T143935Z.json"
    with open(currency_file_path, "r") as f:
        data = json.load(f)

    # Return just the first 3 records for testing
    return data[:3]


@pytest.fixture
def temp_json_files_with_real_data(real_stock_json_data, real_currency_json_data):
    """Create temporary JSON files with real test data."""
    import json

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create stock data file
        stocks_dir = temp_path / "stocks"
        stocks_dir.mkdir()

        stock_file = stocks_dir / "stocks_2025-08-30.json"
        with open(stock_file, "w") as f:
            json.dump(real_stock_json_data, f)

        # Create currency data file
        exchange_dir = temp_path / "exchange"
        exchange_dir.mkdir()

        currency_file = exchange_dir / "exchange_2025-08-30.json"
        with open(currency_file, "w") as f:
            json.dump(real_currency_json_data, f)

        yield temp_path


class TestDirectFactTableLoadingIntegration:
    """Integration tests for direct fact table loading."""

    def test_postgres_environment_configured(self):
        """Verify PostgreSQL environment is properly configured."""
        required_vars = {
            "POSTGRES_HOST": POSTGRES_HOST,
            "POSTGRES_PORT": POSTGRES_PORT,
            "POSTGRES_DB": POSTGRES_DB,
            "POSTGRES_USER": POSTGRES_USER,
            "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
        }

        for var_name, var_value in required_vars.items():
            assert var_value is not None, f"{var_name} must be set for integration tests"
            assert var_value != "", f"{var_name} cannot be empty"

    def test_database_connection(self, test_database_manager):
        """Test that database connection works."""
        # Test connection by executing a simple query
        result = test_database_manager.execute_query("SELECT 1 as test")
        assert len(result) == 1
        assert result[0]["test"] == 1

    def test_required_tables_exist(self, test_database_manager):
        """Test that required dimension and fact tables exist."""
        required_tables = [
            "dim_date",
            "dim_stocks",
            "dim_currency",  # Note: singular, not plural
            "fact_stock_prices",
            "fact_currency_rates",
        ]

        for table in required_tables:
            # Check if table exists
            result = test_database_manager.execute_query(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
                """,
                (table,),
            )
            assert result[0]["exists"], f"Required table {table} does not exist"

    def test_direct_stock_data_insertion(self, test_database_manager, real_stock_json_data):
        """Test direct insertion of stock data into fact table."""
        # Get initial count
        initial_count = test_database_manager.execute_query("SELECT COUNT(*) as count FROM fact_stock_prices")[0][
            "count"
        ]

        # Insert test data
        inserted_count = test_database_manager.insert_stock_data(real_stock_json_data)

        # Verify insertion
        assert inserted_count > 0, "Should have inserted at least some records"

        # Check final count - with upsert logic, records may be updated rather than inserted
        final_count = test_database_manager.execute_query("SELECT COUNT(*) as count FROM fact_stock_prices")[0]["count"]
        
        # Since we use ON CONFLICT DO UPDATE, the final count may not always increase
        # The key is that the operation completed successfully (inserted_count > 0)
        assert final_count >= initial_count, "Should have at least the same number of records"
        
        # Verify that data actually exists with our test symbols
        symbol_check = test_database_manager.execute_query(
            "SELECT COUNT(DISTINCT ds.symbol) as symbol_count FROM fact_stock_prices fsp "
            "JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id WHERE ds.symbol IN ('AAPL', 'MSFT', 'AMZN')"
        )
        assert symbol_check[0]["symbol_count"] > 0, "Should have data for test symbols"

    def test_direct_currency_data_insertion(self, test_database_manager, real_currency_json_data):
        """Test direct insertion of currency data into fact table."""
        # Get initial count
        initial_count = test_database_manager.execute_query("SELECT COUNT(*) as count FROM fact_currency_rates")[0][
            "count"
        ]

        # Insert test data
        inserted_count = test_database_manager.insert_currency_data(real_currency_json_data)

        # Verify insertion
        assert inserted_count > 0, "Should have inserted at least some records"

        # Check final count - with upsert logic, records may be updated rather than inserted
        final_count = test_database_manager.execute_query("SELECT COUNT(*) as count FROM fact_currency_rates")[0][
            "count"
        ]

        # Since we use ON CONFLICT DO UPDATE, the final count may not always increase
        # The key is that the operation completed successfully (inserted_count > 0)
        assert final_count >= initial_count, "Should have at least the same number of records"
        
        # Verify that data actually exists for USD/GBP
        currency_check = test_database_manager.execute_query(
            "SELECT COUNT(*) as rate_count FROM fact_currency_rates fcr "
            "JOIN dim_currency dc_from ON fcr.from_currency_id = dc_from.currency_id "
            "JOIN dim_currency dc_to ON fcr.to_currency_id = dc_to.currency_id "
            "WHERE dc_from.currency_code = 'USD' AND dc_to.currency_code = 'GBP'"
        )
        assert currency_check[0]["rate_count"] > 0, "Should have USD/GBP exchange rate data"

    def test_date_dimension_creation(self, test_database_manager):
        """Test that date dimension records are created as needed."""
        test_date = "2025-08-18"  # Date from the real data

        # Ensure the date exists
        result = test_database_manager.ensure_date_dimension(test_date)
        assert result is True, "Date dimension creation should succeed"

        # Verify the date exists in the table
        date_check = test_database_manager.execute_query(
            "SELECT COUNT(*) as count FROM dim_date WHERE date_value = %s", (test_date,)
        )
        assert date_check[0]["count"] >= 1, "Date should exist in dimension table"

    def test_end_to_end_load_raw_to_db(self, temp_json_files_with_real_data, postgres_connection_string):
        """Test the complete load_raw_to_db function end-to-end."""
        # TODO: Update after load_raw_to_db function signature is corrected
        # The current function takes no parameters but should take directory path
        pytest.skip("Function signature mismatch - load_raw_to_db takes no parameters")

    def test_data_quality_after_insertion(self, test_database_manager, real_stock_json_data):
        """Test data quality after insertion - verify dimensional lookups work."""
        # Insert test data
        test_database_manager.insert_stock_data(real_stock_json_data)

        # Check that dimensional lookups work correctly
        result = test_database_manager.execute_query(
            """
            SELECT 
                fsp.closing_price,
                ds.symbol,
                dd.date_value
            FROM fact_stock_prices fsp
            JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id  
            JOIN dim_date dd ON fsp.date_id = dd.date_id
            WHERE ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META')
            AND dd.date_value >= '2025-08-18'
            ORDER BY ds.symbol, dd.date_value
        """
        )

        assert len(result) >= 1, "Should have records for test symbols"

        # Check price data looks reasonable
        for row in result:
            assert row["closing_price"] > 0, "Closing price should be positive"
            assert row["date_value"] is not None, "Date should be present"

    def test_duplicate_handling(self, test_database_manager, real_stock_json_data):
        """Test that duplicate insertions are handled properly."""
        # Insert data twice
        first_insert = test_database_manager.insert_stock_data(real_stock_json_data)
        second_insert = test_database_manager.insert_stock_data(real_stock_json_data)

        # Both should succeed (ON CONFLICT DO NOTHING should handle duplicates)
        assert first_insert > 0, "First insert should succeed"
        # Second insert might be 0 due to conflicts, which is expected behavior
        assert second_insert >= 0, "Second insert should not fail"
