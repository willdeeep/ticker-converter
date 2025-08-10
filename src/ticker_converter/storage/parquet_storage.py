"""Parquet storage implementation for market data."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .base import BaseStorage, StorageMetadata


class ParquetStorage(BaseStorage):
    """Parquet file storage implementation for market data."""

    @property
    def format_name(self) -> str:
        """Return the format name for this storage implementation."""
        return "parquet"

    def save(
        self,
        data: pd.DataFrame,
        symbol: str,
        data_type: str,
        timestamp: Optional[datetime] = None,
        **kwargs: Any,
    ) -> StorageMetadata:
        """Save DataFrame to Parquet file.

        Args:
            data: DataFrame to save
            symbol: Financial symbol (e.g., 'AAPL', 'BTC')
            data_type: Type of data (e.g., 'daily', 'intraday')
            timestamp: Optional timestamp for filename
            **kwargs: Additional Parquet options (e.g., compression, index)

        Returns:
            StorageMetadata object with save details

        Raises:
            ValueError: If data validation fails
            OSError: If file operations fail
        """
        # Validate input data
        self._validate_data(data)

        # Generate file path
        file_path = self._generate_file_path(symbol, data_type, "parquet", timestamp)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data for Parquet storage
        df_to_save = self._prepare_parquet_data(data, symbol, data_type)

        # Set default Parquet options
        compression = kwargs.get("compression", "snappy")
        index = kwargs.get("index", False)

        # Save to Parquet file
        try:
            df_to_save.to_parquet(
                file_path, compression=compression, index=index, engine="pyarrow"
            )
        except (OSError, pa.ArrowException) as e:
            raise OSError(f"Failed to save Parquet file {file_path}: {e}") from e

        # Create and return metadata
        return self._create_metadata(symbol, data_type, data, file_path)

    def load(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Load DataFrame from Parquet file.

        Args:
            file_path: Path to Parquet file to load

        Returns:
            Loaded DataFrame with metadata columns removed

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If Parquet parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {file_path}")

        try:
            df = pd.read_parquet(file_path, engine="pyarrow")
        except (OSError, pa.ArrowException) as e:
            raise OSError(f"Failed to read Parquet file {file_path}: {e}") from e
        except Exception as e:
            raise ValueError(f"Invalid Parquet format in {file_path}: {e}") from e

        # Remove metadata columns if they exist
        metadata_columns = ["_symbol", "_data_type", "_timestamp", "_data_source"]
        df = df.drop(columns=[col for col in metadata_columns if col in df.columns])

        return df

    def _prepare_parquet_data(
        self, data: pd.DataFrame, symbol: str, data_type: str
    ) -> pd.DataFrame:
        """Prepare DataFrame for Parquet storage.

        Args:
            data: DataFrame to prepare
            symbol: Financial symbol
            data_type: Type of data

        Returns:
            DataFrame with metadata columns added if enabled
        """
        # Create a copy to avoid modifying original data
        df = data.copy()

        # Add metadata columns if enabled
        if self.config.include_metadata:
            df["_symbol"] = symbol
            df["_data_type"] = data_type
            df["_timestamp"] = datetime.utcnow()
            df["_data_source"] = "alpha_vantage"

        # Optimize data types for Parquet storage
        df = self._optimize_data_types(df)

        return df

    def _optimize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame data types for efficient Parquet storage.

        Args:
            df: DataFrame to optimize

        Returns:
            DataFrame with optimized data types
        """
        # Create a copy to avoid modifying original
        optimized_df = df.copy()

        for column in optimized_df.columns:
            # Skip metadata columns
            if column.startswith("_"):
                continue

            dtype = optimized_df[column].dtype

            # Optimize numeric columns
            if pd.api.types.is_numeric_dtype(dtype):
                # For integer columns, try to downcast
                if pd.api.types.is_integer_dtype(dtype):
                    optimized_df[column] = pd.to_numeric(
                        optimized_df[column], downcast="integer"
                    )
                # For float columns, try to downcast
                elif pd.api.types.is_float_dtype(dtype):
                    optimized_df[column] = pd.to_numeric(
                        optimized_df[column], downcast="float"
                    )

            # Convert object columns to string if they contain text
            elif dtype == "object":
                # Check if it's likely a string column
                if optimized_df[column].notna().any():
                    sample_value = (
                        optimized_df[column].dropna().iloc[0]
                        if len(optimized_df[column].dropna()) > 0
                        else None
                    )
                    if isinstance(sample_value, str):
                        optimized_df[column] = optimized_df[column].astype("string")

        return optimized_df

    def get_file_info(self, file_path: Union[str, Path]) -> dict[str, Any]:
        """Get information about a Parquet file without loading it.

        Args:
            file_path: Path to Parquet file

        Returns:
            Dictionary with file information

        Raises:
            FileNotFoundError: If file does not exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {file_path}")

        try:
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema
            metadata = parquet_file.metadata

            return {
                "num_rows": metadata.num_rows,
                "num_columns": len(schema),
                "columns": [field.name for field in schema],
                "file_size_bytes": file_path.stat().st_size,
                "schema": str(schema),
                "created_by": (
                    metadata.created_by if hasattr(metadata, "created_by") else None
                ),
            }
        except Exception as e:
            raise ValueError(
                f"Failed to read Parquet file info from {file_path}: {e}"
            ) from e
