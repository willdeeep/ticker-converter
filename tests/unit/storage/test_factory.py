"""Tests for storage factory."""

import pytest

from ticker_converter.storage.factory import StorageFactory
from ticker_converter.storage.json_storage import JSONStorage
from ticker_converter.storage.parquet_storage import ParquetStorage


class TestStorageFactory:
    """Test StorageFactory class."""

    def test_create_json_storage(self, tmp_path):
        """Test creating JSON storage."""
        storage = StorageFactory.create_storage("json", base_path=str(tmp_path))

        assert isinstance(storage, JSONStorage)
        assert str(storage.config.base_path) == str(tmp_path)

    def test_create_parquet_storage(self, tmp_path):
        """Test creating Parquet storage."""
        storage = StorageFactory.create_storage("parquet", base_path=str(tmp_path))

        assert isinstance(storage, ParquetStorage)
        assert str(storage.config.base_path) == str(tmp_path)

    def test_create_storage_with_config_kwargs(self, tmp_path):
        """Test creating storage with additional config options."""
        storage = StorageFactory.create_storage(
            "json",
            base_path=str(tmp_path),
            include_metadata=False,
            timestamp_format="%Y-%m-%d",
        )

        assert isinstance(storage, JSONStorage)
        assert storage.config.include_metadata is False
        assert storage.config.timestamp_format == "%Y-%m-%d"

    def test_unsupported_storage_type(self):
        """Test error for unsupported storage type."""
        with pytest.raises(ValueError, match="Unsupported storage type 'invalid'"):
            StorageFactory.create_storage("invalid")

    def test_get_supported_types(self):
        """Test getting supported storage types."""
        types = StorageFactory.get_supported_types()

        assert isinstance(types, list)
        assert "json" in types
        assert "parquet" in types
        assert len(types) == 2

    def test_default_base_path(self):
        """Test default base path when not specified."""
        storage = StorageFactory.create_storage("json")

        assert str(storage.config.base_path) == "data"
