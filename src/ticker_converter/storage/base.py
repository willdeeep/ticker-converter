"""Base storage interface for market data."""

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Union

import pandas as pd
from pydantic import BaseModel
from pydantic import Field

from ..constants import FILENAME_TIMESTAMP_FORMAT


class StorageConfig(BaseModel):
    """Configuration for data storage operations."""

    base_path: Union[str, Path] = Field(default="data", description="Base storage path")
    create_directories: bool = Field(
        default=True, description="Auto-create directories"
    )
    timestamp_format: str = Field(
        default="%Y%m%d_%H%M%S", description="Timestamp format for files"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in stored files"
    )

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class StorageMetadata(BaseModel):
    """Metadata for stored market data."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = Field(
        ..., description="Source of the data (e.g., 'alpha_vantage')"
    )
    symbol: str = Field(..., description="Financial symbol (e.g., 'AAPL', 'BTC')")
    data_type: str = Field(
        ..., description="Type of data (e.g., 'daily', 'intraday', 'forex')"
    )
    record_count: int = Field(..., description="Number of records stored")
    file_format: str = Field(
        ..., description="Storage format (e.g., 'json', 'parquet')"
    )
    file_path: str = Field(..., description="Full path to stored file")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class BaseStorage(ABC):
    """Abstract base class for market data storage implementations."""

    def __init__(self, config: StorageConfig):
        """Initialize storage with configuration.

        Args:
            config: Storage configuration object
        """
        self.config = config
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """Ensure the base storage directory exists."""
        if self.config.create_directories:
            Path(self.config.base_path).mkdir(parents=True, exist_ok=True)

    def _generate_filename(
        self,
        symbol: str,
        data_type: str,
        extension: str,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Generate filename for storage.

        Args:
            symbol: Financial symbol
            data_type: Type of data
            extension: File extension
            timestamp: Optional timestamp

        Returns:
            Generated filename
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Use modern f-string with format specification
        timestamp_str = timestamp.strftime(FILENAME_TIMESTAMP_FORMAT)
        return f"{symbol}_{data_type}_{timestamp_str}.{extension}"

    def _generate_file_path(
        self,
        symbol: str,
        data_type: str,
        file_extension: str,
        timestamp: Optional[datetime] = None,
    ) -> Path:
        """Generate full file path for data storage.

        Args:
            symbol: Financial symbol
            data_type: Type of data
            file_extension: File extension
            timestamp: Optional timestamp

        Returns:
            Full Path object for the file
        """
        filename = self._generate_filename(symbol, data_type, file_extension, timestamp)
        return Path(self.config.base_path) / data_type / filename

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate data before storage.

        Args:
            data: DataFrame to validate

        Raises:
            ValueError: If data validation fails
        """
        if len(data.columns) == 0:
            raise ValueError("DataFrame must have at least one column")

        if data.empty:
            raise ValueError("Cannot store empty DataFrame")

    def _create_metadata(
        self,
        symbol: str,
        data_type: str,
        data: pd.DataFrame,
        file_path: Path,
        data_source: str = "alpha_vantage",
    ) -> StorageMetadata:
        """Create metadata for stored data.

        Args:
            symbol: Financial symbol
            data_type: Type of data
            data: Stored DataFrame
            file_path: Path where data was stored
            data_source: Source of the data

        Returns:
            StorageMetadata object
        """
        return StorageMetadata(
            data_source=data_source,
            symbol=symbol,
            data_type=data_type,
            record_count=len(data),
            file_format=self.format_name,
            file_path=str(file_path),
        )

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name for this storage implementation."""
        ...

    @abstractmethod
    def save(
        self,
        data: pd.DataFrame,
        symbol: str,
        data_type: str,
        timestamp: Optional[datetime] = None,
        **kwargs: Any,
    ) -> StorageMetadata:
        """Save DataFrame to storage.

        Args:
            data: DataFrame to save
            symbol: Financial symbol
            data_type: Type of data
            timestamp: Optional timestamp for filename
            **kwargs: Additional format-specific options

        Returns:
            StorageMetadata object with save details
        """
        ...

    @abstractmethod
    def load(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Load DataFrame from storage.

        Args:
            file_path: Path to file to load

        Returns:
            Loaded DataFrame
        """
        ...
