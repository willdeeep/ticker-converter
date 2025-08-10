"""Integration tests for storage with real Alpha Vantage data."""

import os
from datetime import datetime

import pandas as pd
import pytest

from ticker_converter.api_client import AlphaVantageClient
from ticker_converter.config import config
from ticker_converter.storage.factory import StorageFactory


@pytest.mark.integration
class TestStorageIntegration:
    """Integration tests for storage functionality."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create Alpha Vantage API client."""
        if not config.ALPHA_VANTAGE_API_KEY:
            pytest.skip("ALPHA_VANTAGE_API_KEY not set")
        return AlphaVantageClient(config.ALPHA_VANTAGE_API_KEY)

    @pytest.fixture(scope="class")
    def real_stock_data(self, api_client):
        """Get real stock data from Alpha Vantage."""
        try:
            return api_client.get_daily_data("AAPL")
        except Exception as e:
            pytest.skip(f"Failed to fetch real data: {e}")

    @pytest.fixture(scope="class")
    def real_forex_data(self, api_client):
        """Get real forex data from Alpha Vantage."""
        try:
            return api_client.get_forex_daily("USD", "EUR")
        except Exception as e:
            pytest.skip(f"Failed to fetch real forex data: {e}")

    @pytest.fixture(params=["json", "parquet"])
    def storage(self, request, tmp_path):
        """Create storage instance for each format."""
        return StorageFactory.create_storage(request.param, base_path=str(tmp_path))

    def test_save_and_load_real_stock_data(self, storage, real_stock_data):
        """Test saving and loading real stock data."""
        # Save the data
        metadata = storage.save(real_stock_data, "AAPL", "daily")

        # Verify metadata
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == len(real_stock_data)
        assert metadata.file_format in ["json", "parquet"]

        # Load the data back
        loaded_data = storage.load(metadata.file_path)

        # Verify data integrity
        assert len(loaded_data) == len(real_stock_data)
        assert list(loaded_data.columns) == list(real_stock_data.columns)

        # Check that key columns exist
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        for col in required_columns:
            assert col in loaded_data.columns

    def test_save_and_load_real_forex_data(self, storage, real_forex_data):
        """Test saving and loading real forex data."""
        # Save the data
        metadata = storage.save(real_forex_data, "USDEUR", "daily")

        # Verify metadata
        assert metadata.symbol == "USDEUR"
        assert metadata.data_type == "daily"
        assert metadata.record_count == len(real_forex_data)

        # Load the data back
        loaded_data = storage.load(metadata.file_path)

        # Verify data integrity
        assert len(loaded_data) == len(real_forex_data)
        assert list(loaded_data.columns) == list(real_forex_data.columns)

        # Check that key columns exist
        required_columns = ["Date", "Open", "High", "Low", "Close"]
        for col in required_columns:
            assert col in loaded_data.columns

    def test_multiple_saves_different_timestamps(self, tmp_path, real_stock_data):
        """Test saving the same data multiple times with different timestamps."""
        storage = StorageFactory.create_storage("json", base_path=str(tmp_path))

        # Save same data twice with different timestamps
        timestamp1 = datetime(2023, 1, 1, 10, 0, 0)
        timestamp2 = datetime(2023, 1, 1, 11, 0, 0)

        metadata1 = storage.save(real_stock_data, "AAPL", "daily", timestamp1)
        metadata2 = storage.save(real_stock_data, "AAPL", "daily", timestamp2)

        # Should create different files
        assert metadata1.file_path != metadata2.file_path

        # Both files should exist
        assert os.path.exists(metadata1.file_path)
        assert os.path.exists(metadata2.file_path)

        # Both should load correctly
        loaded1 = storage.load(metadata1.file_path)
        loaded2 = storage.load(metadata2.file_path)

        assert len(loaded1) == len(real_stock_data)
        assert len(loaded2) == len(real_stock_data)

    def test_large_dataset_performance(self, tmp_path, real_stock_data):
        """Test performance with larger datasets."""
        # Create a larger dataset by repeating the data
        large_data = pd.concat([real_stock_data] * 10, ignore_index=True)

        # Test both formats
        for storage_type in ["json", "parquet"]:
            storage = StorageFactory.create_storage(
                storage_type, base_path=str(tmp_path)
            )

            # Measure save time
            start_time = datetime.now()
            metadata = storage.save(large_data, "AAPL", f"large_{storage_type}")
            save_time = (datetime.now() - start_time).total_seconds()

            # Measure load time
            start_time = datetime.now()
            loaded_data = storage.load(metadata.file_path)
            load_time = (datetime.now() - start_time).total_seconds()

            # Verify data integrity
            assert len(loaded_data) == len(large_data)

            # Print performance info (for manual review)
            print(
                f"{storage_type.upper()} - Save: {save_time:.3f}s, Load: {load_time:.3f}s, "
                f"Records: {len(large_data)}"
            )

    def test_cross_format_compatibility(self, tmp_path, real_stock_data):
        """Test that data can be saved in one format and the structure preserved."""
        json_storage = StorageFactory.create_storage("json", base_path=str(tmp_path))
        parquet_storage = StorageFactory.create_storage(
            "parquet", base_path=str(tmp_path)
        )

        # Save in both formats
        json_metadata = json_storage.save(real_stock_data, "AAPL", "daily")
        parquet_metadata = parquet_storage.save(real_stock_data, "AAPL", "daily")

        # Load from both formats
        json_loaded = json_storage.load(json_metadata.file_path)
        parquet_loaded = parquet_storage.load(parquet_metadata.file_path)

        # Both should have same structure
        assert list(json_loaded.columns) == list(parquet_loaded.columns)
        assert len(json_loaded) == len(parquet_loaded)

        # Data should be equivalent (accounting for potential type differences)
        for col in json_loaded.columns:
            if pd.api.types.is_numeric_dtype(json_loaded[col]):
                pd.testing.assert_series_equal(
                    json_loaded[col].astype(float).sort_index(),
                    parquet_loaded[col].astype(float).sort_index(),
                    check_names=False,
                )

    def test_file_organization(self, tmp_path, real_stock_data):
        """Test that files are organized correctly in directories."""
        storage = StorageFactory.create_storage("json", base_path=str(tmp_path))

        # Save different data types
        metadata1 = storage.save(real_stock_data, "AAPL", "daily")
        metadata2 = storage.save(real_stock_data, "AAPL", "intraday")
        metadata3 = storage.save(real_stock_data, "MSFT", "daily")

        # Check directory structure
        base_path = tmp_path
        daily_dir = base_path / "daily"
        intraday_dir = base_path / "intraday"

        assert daily_dir.exists()
        assert intraday_dir.exists()

        # Check files are in correct directories
        assert "daily" in metadata1.file_path
        assert "intraday" in metadata2.file_path
        assert "daily" in metadata3.file_path

        # Check filenames contain symbols
        assert "AAPL" in os.path.basename(metadata1.file_path)
        assert "AAPL" in os.path.basename(metadata2.file_path)
        assert "MSFT" in os.path.basename(metadata3.file_path)
