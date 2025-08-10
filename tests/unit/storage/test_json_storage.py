"""Tests for JSON storage implementation."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ticker_converter.storage.base import StorageConfig
from ticker_converter.storage.json_storage import JSONStorage


class TestJSONStorage:
    """Test JSONStorage class."""

    @pytest.fixture
    def storage_config(self, tmp_path):
        """Create test storage configuration."""
        return StorageConfig(base_path=str(tmp_path))

    @pytest.fixture
    def json_storage(self, storage_config):
        """Create JSON storage instance."""
        return JSONStorage(storage_config)

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=3),
                "Close": [100.0, 101.5, 99.8],
                "Volume": [1000, 1100, 950],
            }
        )

    def test_format_name(self, json_storage):
        """Test format name property."""
        assert json_storage.format_name == "json"

    def test_save_basic(self, json_storage, sample_data, tmp_path):
        """Test basic save functionality."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        metadata = json_storage.save(sample_data, "AAPL", "daily", timestamp)

        # Check metadata
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == 3
        assert metadata.file_format == "json"

        # Check file was created
        expected_path = tmp_path / "daily" / "AAPL_daily_20230115_143000.json"
        assert Path(metadata.file_path) == expected_path
        assert expected_path.exists()

    def test_save_creates_directory(self, json_storage, sample_data, tmp_path):
        """Test that save creates necessary directories."""
        metadata = json_storage.save(sample_data, "BTC", "intraday")

        # Check that directory was created
        intraday_dir = tmp_path / "intraday"
        assert intraday_dir.exists()
        assert intraday_dir.is_dir()

        # Check file exists in the directory
        file_path = Path(metadata.file_path)
        assert file_path.parent == intraday_dir
        assert file_path.exists()

    def test_save_with_metadata(self, json_storage, sample_data):
        """Test save with metadata enabled."""
        metadata = json_storage.save(sample_data, "AAPL", "daily")

        # Load and check JSON structure
        with open(metadata.file_path) as f:
            json_data = json.load(f)

        assert "metadata" in json_data
        assert "data" in json_data

        # Check metadata fields
        meta = json_data["metadata"]
        assert meta["symbol"] == "AAPL"
        assert meta["data_type"] == "daily"
        assert meta["record_count"] == 3
        assert meta["data_source"] == "alpha_vantage"
        assert "timestamp" in meta
        assert "columns" in meta

        # Check data
        assert len(json_data["data"]) == 3

    def test_save_without_metadata(self, tmp_path, sample_data):
        """Test save without metadata."""
        config = StorageConfig(base_path=str(tmp_path), include_metadata=False)
        storage = JSONStorage(config)

        metadata = storage.save(sample_data, "AAPL", "daily")

        # Load and check JSON structure
        with open(metadata.file_path) as f:
            json_data = json.load(f)

        # Should be just the data, no metadata wrapper
        assert "metadata" not in json_data
        assert isinstance(json_data, list)  # records format
        assert len(json_data) == 3

    def test_save_validation_error(self, json_storage):
        """Test save with invalid data."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            json_storage.save(empty_df, "AAPL", "daily")

    def test_load_basic(self, json_storage, sample_data):
        """Test basic load functionality."""
        # Save data first
        metadata = json_storage.save(sample_data, "AAPL", "daily")

        # Load data back
        loaded_df = json_storage.load(metadata.file_path)

        # Check data integrity
        assert len(loaded_df) == len(sample_data)
        assert list(loaded_df.columns) == list(sample_data.columns)

        # Check that Date column is converted back to datetime
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["Date"])

    def test_load_file_not_found(self, json_storage):
        """Test load with non-existent file."""
        with pytest.raises(FileNotFoundError):
            json_storage.load("nonexistent.json")

    def test_load_invalid_json(self, json_storage, tmp_path):
        """Test load with invalid JSON file."""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("{ invalid json content")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            json_storage.load(invalid_file)

    def test_load_without_metadata_wrapper(self, json_storage, tmp_path):
        """Test load with JSON that doesn't have metadata wrapper."""
        # Create JSON without metadata wrapper
        data = [
            {"Date": "2023-01-01", "Close": 100.0},
            {"Date": "2023-01-02", "Close": 101.5},
        ]

        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump(data, f)

        # Load data
        loaded_df = json_storage.load(json_file)

        assert len(loaded_df) == 2
        assert "Date" in loaded_df.columns
        assert "Close" in loaded_df.columns

    def test_datetime_restoration(self, json_storage, tmp_path):
        """Test that datetime columns are properly restored."""
        # Create DataFrame with datetime
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=2),
                "timestamp": pd.date_range("2023-01-01 10:00:00", periods=2, freq="1h"),
                "Close": [100.0, 101.5],
            }
        )

        # Save and load
        metadata = json_storage.save(df, "TEST", "daily")
        loaded_df = json_storage.load(metadata.file_path)

        # Check datetime restoration
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["Date"])
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["timestamp"])

    def test_custom_json_options(self, json_storage, sample_data):
        """Test save with custom JSON options."""
        # Save with custom orient
        metadata = json_storage.save(sample_data, "AAPL", "daily", orient="index")

        # Load and verify structure
        with open(metadata.file_path) as f:
            json_data = json.load(f)

        # With orient="index", data should be dict with numeric keys
        data = json_data["data"]
        assert isinstance(data, dict)
        assert "0" in data  # First row index as string key

    def test_file_path_generation(self, json_storage):
        """Test that file paths are generated correctly."""
        timestamp = datetime(2023, 5, 15, 9, 30, 0)
        file_path = json_storage._generate_file_path(
            "MSFT", "intraday", "json", timestamp
        )

        assert file_path.suffix == ".json"
        assert "MSFT_intraday_20230515_093000.json" in str(file_path)
        assert "intraday" in str(file_path.parent)
