"""Tests for storage base classes and configuration."""

import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from ticker_converter.storage.base import StorageConfig, StorageMetadata, BaseStorage


class TestStorageConfig:
    """Test StorageConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = StorageConfig()
        assert config.base_path == "data"
        assert config.create_directories is True
        assert config.timestamp_format == "%Y%m%d_%H%M%S"
        assert config.include_metadata is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = StorageConfig(
            base_path="/custom/path",
            create_directories=False,
            timestamp_format="%Y-%m-%d",
            include_metadata=False
        )
        assert str(config.base_path) == "/custom/path"
        assert config.create_directories is False
        assert config.timestamp_format == "%Y-%m-%d"
        assert config.include_metadata is False


class TestStorageMetadata:
    """Test StorageMetadata class."""

    def test_metadata_creation(self):
        """Test metadata object creation."""
        metadata = StorageMetadata(
            data_source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
            record_count=100,
            file_format="json",
            file_path="/path/to/file.json"
        )

        assert metadata.data_source == "alpha_vantage"
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == 100
        assert metadata.file_format == "json"
        assert metadata.file_path == "/path/to/file.json"
        assert isinstance(metadata.timestamp, datetime)

    def test_metadata_json_serialization(self):
        """Test metadata JSON serialization."""
        metadata = StorageMetadata(
            data_source="alpha_vantage",
            symbol="AAPL",
            data_type="daily",
            record_count=100,
            file_format="json",
            file_path="/path/to/file.json"
        )

        json_data = metadata.model_dump()
        assert "timestamp" in json_data
        assert isinstance(json_data["timestamp"], datetime)


class MockStorage(BaseStorage):
    """Mock storage implementation for testing."""

    @property
    def format_name(self) -> str:
        return "mock"

    def save(self, data, symbol, data_type, timestamp=None, **kwargs):
        return self._create_metadata(symbol, data_type, data, Path("mock.file"))

    def load(self, file_path):
        return pd.DataFrame({"test": [1, 2, 3]})


class TestBaseStorage:
    """Test BaseStorage abstract class functionality."""

    @pytest.fixture
    def storage_config(self, tmp_path):
        """Create test storage configuration."""
        return StorageConfig(base_path=str(tmp_path))

    @pytest.fixture
    def mock_storage(self, storage_config):
        """Create mock storage instance."""
        return MockStorage(storage_config)

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=5),
            "Close": [100.0, 101.5, 99.8, 102.3, 103.1],
            "Volume": [1000, 1100, 950, 1200, 1050]
        })

    def test_filename_generation(self, mock_storage):
        """Test filename generation."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        filename = mock_storage._generate_filename("AAPL", "daily", "json", timestamp)
        assert filename == "AAPL_daily_20230115_143000.json"

    def test_filename_generation_no_timestamp(self, mock_storage):
        """Test filename generation without timestamp."""
        filename = mock_storage._generate_filename("BTC", "intraday", "parquet")
        assert filename.startswith("BTC_intraday_")
        assert filename.endswith(".parquet")

    def test_file_path_generation(self, mock_storage, tmp_path):
        """Test file path generation."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        file_path = mock_storage._generate_file_path("AAPL", "daily", "json", timestamp)

        expected_path = tmp_path / "daily" / "AAPL_daily_20230115_143000.json"
        assert file_path == expected_path

    def test_data_validation_empty_dataframe(self, mock_storage):
        """Test data validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            mock_storage._validate_data(empty_df)

    def test_data_validation_no_columns(self, mock_storage):
        """Test data validation with no columns."""
        df = pd.DataFrame(index=[0, 1, 2])
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            mock_storage._validate_data(df)

    def test_data_validation_valid_data(self, mock_storage, sample_data):
        """Test data validation with valid data."""
        # Should not raise any exception
        mock_storage._validate_data(sample_data)

    def test_metadata_creation(self, mock_storage, sample_data):
        """Test metadata creation."""
        file_path = Path("/test/path.json")
        metadata = mock_storage._create_metadata("AAPL", "daily", sample_data, file_path)

        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == len(sample_data)
        assert metadata.file_format == "mock"
        assert metadata.file_path == str(file_path)
        assert metadata.data_source == "alpha_vantage"

    def test_base_directory_creation(self, tmp_path):
        """Test base directory creation."""
        test_path = tmp_path / "new_directory"
        config = StorageConfig(base_path=str(test_path))

        # Directory should not exist yet
        assert not test_path.exists()

        # Creating storage should create the directory
        MockStorage(config)
        assert test_path.exists()
        assert test_path.is_dir()

    def test_base_directory_creation_disabled(self, tmp_path):
        """Test base directory creation when disabled."""
        test_path = tmp_path / "new_directory"
        config = StorageConfig(base_path=str(test_path), create_directories=False)

        # Directory should not exist yet
        assert not test_path.exists()

        # Creating storage should not create the directory
        MockStorage(config)
        assert not test_path.exists()
