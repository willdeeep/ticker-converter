"""Data storage module for financial market data.

This module provides functionality to store raw market data in various formats
including JSON and Parquet, with support for local and cloud storage.
"""

from .base import BaseStorage, StorageConfig, StorageMetadata
from .factory import StorageFactory
from .json_storage import JSONStorage
from .parquet_storage import ParquetStorage

__all__ = [
    "BaseStorage",
    "StorageConfig",
    "StorageMetadata",
    "StorageFactory",
    "JSONStorage",
    "ParquetStorage",
]
