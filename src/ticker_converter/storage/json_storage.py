"""JSON storage implementation for market data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from .base import BaseStorage, StorageMetadata


class JSONStorage(BaseStorage):
    """JSON file storage implementation for market data."""

    @property
    def format_name(self) -> str:
        """Return the format name for this storage implementation."""
        return "json"

    def save(
        self,
        data: pd.DataFrame,
        symbol: str,
        data_type: str,
        timestamp: Optional[datetime] = None,
        **kwargs: Any,
    ) -> StorageMetadata:
        """Save DataFrame to JSON file.

        Args:
            data: DataFrame to save
            symbol: Financial symbol (e.g., 'AAPL', 'BTC')
            data_type: Type of data (e.g., 'daily', 'intraday')
            timestamp: Optional timestamp for filename
            **kwargs: Additional JSON options (e.g., orient, date_format)

        Returns:
            StorageMetadata object with save details

        Raises:
            ValueError: If data validation fails
            OSError: If file operations fail
        """
        # Validate input data
        self._validate_data(data)

        # Generate file path
        file_path = self._generate_file_path(symbol, data_type, "json", timestamp)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data for JSON serialization
        json_data = self._prepare_json_data(data, symbol, data_type, **kwargs)

        # Save to JSON file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        except OSError as e:
            raise OSError(f"Failed to save JSON file {file_path}: {e}") from e

        # Create and return metadata
        return self._create_metadata(symbol, data_type, data, file_path)

    def load(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Load DataFrame from JSON file.

        Args:
            file_path: Path to JSON file to load

        Returns:
            Loaded DataFrame

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If JSON parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                json_data = json.load(f)
        except OSError as e:
            raise OSError(f"Failed to read JSON file {file_path}: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {file_path}: {e}") from e

        # Extract DataFrame from JSON structure
        if "data" in json_data:
            df = pd.DataFrame(json_data["data"])
        else:
            # Fallback: treat entire JSON as DataFrame data
            df = pd.DataFrame(json_data)

        # Convert date columns back to datetime if they exist
        self._restore_datetime_columns(df)

        return df

    def _prepare_json_data(
        self, data: pd.DataFrame, symbol: str, data_type: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Prepare DataFrame for JSON serialization.

        Args:
            data: DataFrame to prepare
            symbol: Financial symbol
            data_type: Type of data
            **kwargs: Additional options

        Returns:
            Dictionary ready for JSON serialization
        """
        # Convert DataFrame to dictionary
        orient = kwargs.get("orient", "records")

        df_dict = data.to_dict(orient=orient)

        # Create structured JSON with metadata if enabled
        if self.config.include_metadata:
            json_data = {
                "metadata": {
                    "symbol": symbol,
                    "data_type": data_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "record_count": len(data),
                    "columns": list(data.columns),
                    "data_source": "alpha_vantage",
                },
                "data": df_dict,
            }
        else:
            json_data = df_dict

        return json_data

    def _restore_datetime_columns(self, df: pd.DataFrame) -> None:
        """Restore datetime columns from string format.

        Args:
            df: DataFrame to process (modified in-place)
        """
        # Common date column names to check
        date_columns = ["Date", "date", "timestamp", "Timestamp"]

        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    # If conversion fails, leave as is
                    continue
