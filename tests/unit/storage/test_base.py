"""Tests for storage base classes and configuration."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from ticker_converter.storage.base import BaseStorage, StorageConfig, StorageMetadata


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
            include_metadata=False,
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
            file_path="/path/to/file.json",
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
            file_path="/path/to/file.json",
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
        """Save data and return metadata with proper file path generation."""
        # Validate data first (this will raise ValueError if invalid)
        self._validate_data(data)

        # Generate file path using the protected method
        file_path = self._generate_file_path(
            symbol, data_type, self.format_name, timestamp
        )
        return self._create_metadata(symbol, data_type, data, file_path)

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
        return pd.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=5),
                "Close": [100.0, 101.5, 99.8, 102.3, 103.1],
                "Volume": [1000, 1100, 950, 1200, 1050],
            }
        )

    def test_filename_generation_through_save(self, mock_storage, sample_data):
        """Test filename generation through save method."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        metadata = mock_storage.save(sample_data, "AAPL", "daily", timestamp)

        # Verify the filename pattern in the returned metadata
        expected_filename = "AAPL_daily_20230115_143000.mock"
        assert expected_filename in str(metadata.file_path)

    def test_filename_generation_no_timestamp_through_save(
        self, mock_storage, sample_data
    ):
        """Test filename generation without timestamp through save method."""
        metadata = mock_storage.save(sample_data, "BTC", "intraday")

        # Verify the filename pattern
        filename = Path(metadata.file_path).name
        assert filename.startswith("BTC_intraday_")
        assert filename.endswith(".mock")

    def test_file_path_structure_through_save(
        self, mock_storage, sample_data, tmp_path
    ):
        """Test file path structure through save method."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        metadata = mock_storage.save(sample_data, "AAPL", "daily", timestamp)

        file_path = Path(metadata.file_path)
        assert file_path.parent.name == "daily"
        assert file_path.name == "AAPL_daily_20230115_143000.mock"
        assert str(tmp_path) in str(file_path)

    def test_data_validation_empty_dataframe_through_save(self, mock_storage):
        """Test data validation with empty DataFrame through save method."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            mock_storage.save(empty_df, "AAPL", "daily")

    def test_data_validation_no_columns_through_save(self, mock_storage):
        """Test data validation with no columns through save method."""
        df = pd.DataFrame(index=[0, 1, 2])
        with pytest.raises(ValueError, match="DataFrame must have at least one column"):
            mock_storage.save(df, "AAPL", "daily")

    def test_data_validation_valid_data_through_save(self, mock_storage, sample_data):
        """Test data validation with valid data through save method."""
        # Should not raise any exception
        try:
            metadata = mock_storage.save(sample_data, "AAPL", "daily")
            # Verify that metadata was created successfully
            assert metadata.symbol == "AAPL"
            assert metadata.record_count == len(sample_data)
        except ValueError:
            pytest.fail("save() raised ValueError unexpectedly!")

    def test_metadata_creation_through_save(self, mock_storage, sample_data):
        """Test metadata creation through save method."""
        timestamp = datetime(2023, 1, 15, 14, 30, 0)
        metadata = mock_storage.save(sample_data, "AAPL", "daily", timestamp)

        # Verify all metadata fields are correctly set
        assert metadata.symbol == "AAPL"
        assert metadata.data_type == "daily"
        assert metadata.record_count == len(sample_data)
        assert metadata.file_format == "mock"
        assert metadata.data_source == "alpha_vantage"
        assert isinstance(metadata.timestamp, datetime)

        # Verify file path structure
        file_path = Path(metadata.file_path)
        assert file_path.name == "AAPL_daily_20230115_143000.mock"

    def test_different_data_types_through_save(self, mock_storage, sample_data):
        """Test that different data types create appropriate subdirectories."""
        # Test daily data
        daily_metadata = mock_storage.save(sample_data, "AAPL", "daily")
        daily_path = Path(daily_metadata.file_path)
        assert daily_path.parent.name == "daily"

        # Test intraday data
        intraday_metadata = mock_storage.save(sample_data, "AAPL", "intraday")
        intraday_path = Path(intraday_metadata.file_path)
        assert intraday_path.parent.name == "intraday"

    def test_symbol_preservation_through_save(self, mock_storage, sample_data):
        """Test that symbol information is preserved in metadata."""
        symbols = ["AAPL", "GOOGL", "MSFT", "BTC-USD"]

        for symbol in symbols:
            metadata = mock_storage.save(sample_data, symbol, "daily")
            assert metadata.symbol == symbol
            assert symbol in str(metadata.file_path)

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
