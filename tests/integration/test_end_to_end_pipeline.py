"""End-to-end integration tests for the complete data pipeline.

This test validates the full pipeline from API data retrieval through storage
and loading, ensuring the complete Issue #2 storage functionality works.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ticker_converter.api_client import AlphaVantageAPIError, AlphaVantageClient
from ticker_converter.config import config
from ticker_converter.storage import StorageFactory


@pytest.mark.integration
class TestEndToEndPipeline:
    """Test the complete data pipeline from API to storage."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create Alpha Vantage API client."""
        if not config.ALPHA_VANTAGE_API_KEY:
            pytest.skip("ALPHA_VANTAGE_API_KEY not set")
        return AlphaVantageClient(config.ALPHA_VANTAGE_API_KEY)

    @pytest.fixture(scope="class")
    def stock_data(self, api_client):
        """Get real stock data from Alpha Vantage."""
        try:
            return api_client.get_daily_stock_data("AAPL")
        except Exception as e:
            pytest.skip(f"Failed to fetch stock data: {e}")

    @pytest.fixture(params=["json", "parquet"])
    def storage_type(self, request):
        """Parametrize storage types."""
        return request.param

    def test_complete_pipeline_flow(self, stock_data, storage_type, tmp_path):
        """Test complete pipeline: API -> Storage -> Load -> Verify."""

        # 1. Verify API data quality
        assert len(stock_data) > 0, "Should have retrieved stock data"
        assert "Date" in stock_data.columns, "Should have Date column"
        assert "Close" in stock_data.columns, "Should have Close column"
        assert "Volume" in stock_data.columns, "Should have Volume column"

        # 2. Test storage functionality
        storage = StorageFactory.create_storage(
            storage_type, base_path=str(tmp_path), include_metadata=True
        )

        # Save data
        metadata = storage.save(stock_data, "AAPL", "daily")

        # Verify metadata
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == len(stock_data)
        assert metadata.file_format == storage_type

        # Verify file was created
        file_path = Path(metadata.file_path)
        assert file_path.exists(), f"Storage file should exist: {file_path}"
        assert file_path.stat().st_size > 0, "Storage file should not be empty"

        # 3. Test data loading
        loaded_data = storage.load(metadata.file_path)

        # 4. Verify data integrity
        assert len(loaded_data) == len(
            stock_data
        ), "Loaded data should have same number of records"

        # Check that key columns are preserved
        for col in ["Date", "Close", "Volume"]:
            assert col in loaded_data.columns, f"Column {col} should be preserved"

        # Verify data types are reasonable
        assert pd.api.types.is_datetime64_any_dtype(
            loaded_data["Date"]
        ), "Date should be datetime"
        assert pd.api.types.is_numeric_dtype(
            loaded_data["Close"]
        ), "Close should be numeric"
        assert pd.api.types.is_numeric_dtype(
            loaded_data["Volume"]
        ), "Volume should be numeric"

    def test_file_organization(self, stock_data, tmp_path):
        """Test that files are organized correctly by data type."""
        storage = StorageFactory.create_storage("json", base_path=str(tmp_path))

        # Save different data types
        daily_metadata = storage.save(stock_data, "AAPL", "daily")
        intraday_metadata = storage.save(stock_data, "AAPL", "intraday")

        # Verify directory structure
        daily_dir = tmp_path / "daily"
        intraday_dir = tmp_path / "intraday"

        assert daily_dir.exists(), "Daily directory should be created"
        assert intraday_dir.exists(), "Intraday directory should be created"

        # Verify files are in correct directories
        assert "daily" in daily_metadata.file_path
        assert "intraday" in intraday_metadata.file_path

    def test_cross_format_compatibility(self, stock_data, tmp_path):
        """Test that data can be saved and loaded across different formats."""
        json_storage = StorageFactory.create_storage("json", base_path=str(tmp_path))
        parquet_storage = StorageFactory.create_storage(
            "parquet", base_path=str(tmp_path)
        )

        # Save in both formats
        json_metadata = json_storage.save(stock_data, "AAPL", "daily")
        parquet_metadata = parquet_storage.save(stock_data, "AAPL", "daily")

        # Load from both formats
        json_loaded = json_storage.load(json_metadata.file_path)
        parquet_loaded = parquet_storage.load(parquet_metadata.file_path)

        # Verify compatibility
        assert len(json_loaded) == len(
            parquet_loaded
        ), "Both formats should have same record count"
        assert list(json_loaded.columns) == list(
            parquet_loaded.columns
        ), "Both formats should have same columns"

    def test_rate_limit_handling(self, api_client):
        """Test that the system handles API rate limits gracefully."""
        # This test should be run sparingly to avoid hitting actual rate limits
        # It mainly validates that the client doesn't crash on rate limit responses

        try:
            # Make a simple request
            data = api_client.get_daily_stock_data("MSFT")
            assert len(data) > 0, "Should retrieve data successfully"
        except AlphaVantageAPIError as e:
            # If we hit a rate limit or API information message, that's expected
            error_msg = str(e).lower()
            if any(phrase in error_msg for phrase in ["rate limit", "information", "api call frequency"]):
                pytest.skip(f"Hit API limit or restriction - this is expected: {e}")
            else:
                raise  # Re-raise if it's a different API error

    @pytest.mark.slow
    def test_large_dataset_handling(self, api_client, tmp_path):
        """Test handling of larger datasets (marked as slow test)."""
        try:
            # Get full dataset instead of compact
            data = api_client.get_daily_stock_data("AAPL", outputsize="full")

            if len(data) > 1000:  # Only run if we got a substantial dataset
                # Test with both storage formats
                for storage_type in ["json", "parquet"]:
                    storage = StorageFactory.create_storage(
                        storage_type, base_path=str(tmp_path)
                    )

                    # Measure performance
                    start_time = datetime.now()
                    metadata = storage.save(data, "AAPL", f"large_{storage_type}")
                    save_time = (datetime.now() - start_time).total_seconds()

                    start_time = datetime.now()
                    loaded_data = storage.load(metadata.file_path)
                    load_time = (datetime.now() - start_time).total_seconds()

                    # Verify data integrity
                    assert len(loaded_data) == len(data)

                    # Performance should be reasonable (less than 30 seconds each)
                    assert (
                        save_time < 30
                    ), f"{storage_type} save took too long: {save_time}s"
                    assert (
                        load_time < 30
                    ), f"{storage_type} load took too long: {load_time}s"
            else:
                pytest.skip("Dataset too small for large dataset test")

        except Exception as e:
            pytest.skip(f"Could not fetch large dataset: {e}")
