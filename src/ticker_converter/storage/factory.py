"""Storage factory for creating storage instances."""

from pathlib import Path
from typing import Union

from .base import BaseStorage, StorageConfig
from .json_storage import JSONStorage
from .parquet_storage import ParquetStorage


class StorageFactory:
    """Factory class for creating storage instances."""

    _STORAGE_TYPES = {
        'json': JSONStorage,
        'parquet': ParquetStorage,
    }

    @classmethod
    def create_storage(
        self,
        storage_type: str,
        base_path: Union[str, Path] = "data",
        **config_kwargs
    ) -> BaseStorage:
        """Create a storage instance.

        Args:
            storage_type: Type of storage ('json' or 'parquet')
            base_path: Base path for storage
            **config_kwargs: Additional configuration options

        Returns:
            Storage instance

        Raises:
            ValueError: If storage type is not supported
        """
        if storage_type not in self._STORAGE_TYPES:
            available_types = list(self._STORAGE_TYPES.keys())
            raise ValueError(
                f"Unsupported storage type '{storage_type}'. "
                f"Available types: {available_types}"
            )

        # Create configuration
        config = StorageConfig(base_path=base_path, **config_kwargs)

        # Create and return storage instance
        storage_class = self._STORAGE_TYPES[storage_type]
        return storage_class(config)

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported storage types.

        Returns:
            List of supported storage type names
        """
        return list(cls._STORAGE_TYPES.keys())
