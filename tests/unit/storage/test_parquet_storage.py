"""Tests for Parquet storage implementation."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ticker_converter.storage.base import StorageConfig
from ticker_converter.storage.parquet_storage import ParquetStorage


class TestParquetStorage:
    """Test ParquetStorage class."""

    @pytest.fixture
    def storage_config(self, tmp_path):
        """Create test storage configuration."""
        return StorageConfig(base_path=str(tmp_path))

    @pytest.fixture
    def parquet_storage(self, storage_config):
        """Create Parquet storage instance."""
        return ParquetStorage(storage_config)

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=3),
                "Close": [100.0, 101.5, 99.8],
                "Volume": [1000, 1100, 950],
                "Symbol": ["AAPL", "AAPL", "AAPL"],
            }
        )

    def test_format_name(self, parquet_storage):
        """Test format name property."""
        assert parquet_storage.format_name == "parquet"

    def test_save_basic(self, parquet_storage, sample_data, tmp_path):
        """Test basic save functionality."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        metadata = parquet_storage.save(sample_data, "AAPL", "daily", timestamp)

        # Check metadata
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == 3
        assert metadata.file_format == "parquet"

        # Check file was created
        expected_path = tmp_path / "daily" / "AAPL_daily_20230115_143000.parquet"
        assert Path(metadata.file_path) == expected_path
        assert expected_path.exists()

    def test_save_creates_directory(self, parquet_storage, sample_data, tmp_path):
        """Test that save creates necessary directories."""
        metadata = parquet_storage.save(sample_data, "BTC", "intraday")

        # Check that directory was created
        intraday_dir = tmp_path / "intraday"
        assert intraday_dir.exists()
        assert intraday_dir.is_dir()

        # Check file exists in the directory
        file_path = Path(metadata.file_path)
        assert file_path.parent == intraday_dir
        assert file_path.exists()

    def test_save_with_metadata(self, parquet_storage, sample_data):
        """Test save with metadata enabled."""
        metadata = parquet_storage.save(sample_data, "AAPL", "daily")

        # Load and check Parquet file
        loaded_df = pd.read_parquet(metadata.file_path)

        # Check metadata columns were added
        assert "_symbol" in loaded_df.columns
        assert "_data_type" in loaded_df.columns
        assert "_timestamp" in loaded_df.columns
        assert "_data_source" in loaded_df.columns

        # Check metadata values
        assert all(loaded_df["_symbol"] == "AAPL")
        assert all(loaded_df["_data_type"] == "daily")
        assert all(loaded_df["_data_source"] == "alpha_vantage")

    def test_save_without_metadata(self, tmp_path, sample_data):
        """Test save without metadata."""
        config = StorageConfig(base_path=str(tmp_path), include_metadata=False)
        storage = ParquetStorage(config)

        metadata = storage.save(sample_data, "AAPL", "daily")

        # Load and check Parquet file
        loaded_df = pd.read_parquet(metadata.file_path)

        # Should not have metadata columns
        metadata_columns = ["_symbol", "_data_type", "_timestamp", "_data_source"]
        for col in metadata_columns:
            assert col not in loaded_df.columns

    def test_save_validation_error(self, parquet_storage):
        """Test save with invalid data."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            parquet_storage.save(empty_df, "AAPL", "daily")

    def test_save_with_compression(self, parquet_storage, sample_data):
        """Test save with different compression options."""
        metadata = parquet_storage.save(
            sample_data, "AAPL", "daily", compression="gzip"
        )

        # File should exist and be readable
        assert Path(metadata.file_path).exists()
        loaded_df = pd.read_parquet(metadata.file_path)
        assert len(loaded_df) == 3

    def test_load_basic(self, parquet_storage, sample_data):
        """Test basic load functionality."""
        # Save data first
        metadata = parquet_storage.save(sample_data, "AAPL", "daily")

        # Load data back
        loaded_df = parquet_storage.load(metadata.file_path)

        # Check data integrity (metadata columns should be removed)
        assert len(loaded_df) == len(sample_data)

        # Original columns should be present
        for col in sample_data.columns:
            assert col in loaded_df.columns

        # Metadata columns should be removed
        metadata_columns = ["_symbol", "_data_type", "_timestamp", "_data_source"]
        for col in metadata_columns:
            assert col not in loaded_df.columns

    def test_load_file_not_found(self, parquet_storage):
        """Test load with non-existent file."""
        with pytest.raises(FileNotFoundError):
            parquet_storage.load("nonexistent.parquet")

    def test_load_invalid_parquet(self, parquet_storage, tmp_path):
        """Test load with invalid Parquet file."""
        # Create invalid Parquet file
        invalid_file = tmp_path / "invalid.parquet"
        with open(invalid_file, "w") as f:
            f.write("not a parquet file")

        with pytest.raises((OSError, ValueError)):
            parquet_storage.load(invalid_file)

    def test_data_type_optimization(self, parquet_storage):
        """Test data type optimization for Parquet storage."""
        # Create DataFrame with various data types
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "string_col": ["a", "b", "c"],
                "mixed_obj": ["text1", "text2", "text3"],
            }
        )

        optimized_df = parquet_storage._optimize_data_types(df)

        # Check that optimization was applied
        assert pd.api.types.is_integer_dtype(optimized_df["int_col"])
        assert pd.api.types.is_float_dtype(optimized_df["float_col"])
        # String columns should be converted to string dtype
        assert optimized_df["string_col"].dtype == "string"

    def test_get_file_info(self, parquet_storage, sample_data):
        """Test getting file information without loading."""
        # Save data first
        metadata = parquet_storage.save(sample_data, "AAPL", "daily")

        # Get file info
        info = parquet_storage.get_file_info(metadata.file_path)

        # Check info structure
        assert "num_rows" in info
        assert "num_columns" in info
        assert "columns" in info
        assert "file_size_bytes" in info
        assert "schema" in info

        # Check values
        assert info["num_rows"] == 3
        assert info["num_columns"] > 0  # Should include metadata columns
        assert "Close" in info["columns"]
        assert info["file_size_bytes"] > 0

    def test_get_file_info_not_found(self, parquet_storage):
        """Test get_file_info with non-existent file."""
        with pytest.raises(FileNotFoundError):
            parquet_storage.get_file_info("nonexistent.parquet")

    def test_datetime_preservation(self, parquet_storage):
        """Test that datetime columns are preserved in Parquet."""
        # Create DataFrame with datetime
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=2),
                "timestamp": pd.date_range("2023-01-01 10:00:00", periods=2, freq="1h"),
                "Close": [100.0, 101.5],
            }
        )

        # Save and load
        metadata = parquet_storage.save(df, "TEST", "daily")
        loaded_df = parquet_storage.load(metadata.file_path)

        # Check datetime preservation
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["Date"])
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["timestamp"])

        # Check values are the same
        pd.testing.assert_series_equal(
            loaded_df["Date"].sort_index(), df["Date"].sort_index()
        )

    def test_large_numbers_precision(self, parquet_storage):
        """Test precision preservation for large numbers."""
        df = pd.DataFrame(
            {
                "large_int": [999999999999, 1000000000000, 1000000000001],
                "high_precision": [
                    123.456789012345,
                    987.654321098765,
                    555.111222333444,
                ],
            }
        )

        # Save and load
        metadata = parquet_storage.save(df, "TEST", "daily")
        loaded_df = parquet_storage.load(metadata.file_path)

        # Check precision preservation
        pd.testing.assert_series_equal(
            loaded_df["large_int"].sort_index(), df["large_int"].sort_index()
        )
        # For floats, check they're close (Parquet may have slight precision differences)
        assert loaded_df["high_precision"].iloc[0] == pytest.approx(
            df["high_precision"].iloc[0], rel=1e-6
        )
