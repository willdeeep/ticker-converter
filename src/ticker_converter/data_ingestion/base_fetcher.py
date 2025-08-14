"""Base fetcher class for data ingestion operations.

This module provides a common base class for all data fetchers to ensure
consistent patterns, error handling, and logging across the data ingestion pipeline.
"""

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, ClassVar

import pandas as pd

from ..api_clients.client import AlphaVantageClient
from ..api_clients.exceptions import AlphaVantageAPIError


class BaseDataFetcher(ABC):
    """Abstract base class for all data fetchers.

    Provides common functionality and enforces consistent patterns
    across NYSE and currency data fetchers.
    """

    # Source identifier for all records
    SOURCE: ClassVar[str] = "alpha_vantage"

    def __init__(self, api_client: AlphaVantageClient | None = None) -> None:
        """Initialize the base data fetcher.

        Args:
            api_client: Alpha Vantage API client. If None, creates a new instance.
        """
        self.api_client = api_client or AlphaVantageClient()
        self.logger = logging.getLogger(self.__class__.__module__)
        self._log_initialization()

    def _log_initialization(self) -> None:
        """Log fetcher initialization."""
        self.logger.info("Initialized %s", self.__class__.__name__)

    @abstractmethod
    def prepare_for_sql_insert(
        self, df: pd.DataFrame, *args: Any
    ) -> list[dict[str, Any]]:
        """Prepare DataFrame data for SQL insertion.

        Args:
            df: DataFrame with fetched data
            *args: Additional arguments specific to fetcher type

        Returns:
            List of dictionaries ready for SQL insertion
        """

    def _handle_api_error(self, error: AlphaVantageAPIError, operation: str) -> None:
        """Handle API errors consistently.

        Args:
            error: The API error that occurred
            operation: Description of the operation that failed
        """
        self.logger.error("API error during %s: %s", operation, error)

    def _handle_data_error(self, error: Exception, operation: str) -> None:
        """Handle data processing errors consistently.

        Args:
            error: The error that occurred
            operation: Description of the operation that failed
        """
        self.logger.error("Data processing error during %s: %s", operation, error)

    def _create_base_record(self) -> dict[str, Any]:
        """Create base record with common fields.

        Returns:
            Dictionary with source and created_at fields
        """
        return {
            "source": self.SOURCE,
            "created_at": datetime.now(),
        }

    def _validate_dataframe(
        self, df: pd.DataFrame, required_columns: list[str]
    ) -> bool:
        """Validate DataFrame has required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names

        Returns:
            True if DataFrame is valid, False otherwise
        """
        if df is None or df.empty:
            self.logger.warning("DataFrame is None or empty")
            return False

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.warning("Missing required columns: %s", missing_columns)
            return False

        return True

    def _safe_float_conversion(self, value: Any, field_name: str) -> float:
        """Safely convert value to float with error handling.

        Args:
            value: Value to convert
            field_name: Name of the field for error logging

        Returns:
            Float value or 0.0 if conversion fails
        """
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            self.logger.warning(
                "Failed to convert %s to float for field %s: %s. Using 0.0",
                value,
                field_name,
                e,
            )
            return 0.0

    def _safe_int_conversion(self, value: Any, field_name: str) -> int:
        """Safely convert value to int with error handling.

        Args:
            value: Value to convert
            field_name: Name of the field for error logging

        Returns:
            Integer value or 0 if conversion fails
        """
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            self.logger.warning(
                "Failed to convert %s to int for field %s: %s. Using 0",
                value,
                field_name,
                e,
            )
            return 0

    def _safe_date_conversion(self, value: Any) -> date:
        """Safely convert value to date with error handling.

        Args:
            value: Value to convert (datetime, date, or string)

        Returns:
            Date object or current date if conversion fails
        """
        try:
            # Handle datetime objects
            if hasattr(value, "date") and callable(getattr(value, "date")):
                return value.date()  # type: ignore[no-any-return]
            # Handle date objects
            if isinstance(value, date):
                return value
            # Handle string dates
            if isinstance(value, str):
                return datetime.strptime(value, "%Y-%m-%d").date()
            # Default fallback
            self.logger.warning("Unexpected date type %s: %s", type(value), value)
            return datetime.now().date()
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(
                "Failed to convert %s to date: %s. Using current date", value, e
            )
            return datetime.now().date()
