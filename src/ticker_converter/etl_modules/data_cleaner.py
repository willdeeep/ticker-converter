"""Data cleaning module for market data."""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ..data_models.market_data import CleanedMarketData, RawMarketData
from .constants import CleaningConstants, MarketDataColumns
from .utils import DataFrameUtils, OutlierDetector, PriceValidator

logger = logging.getLogger(__name__)


class CleaningConfig(BaseModel):
    """Configuration for data cleaning operations."""

    remove_duplicates: bool = Field(
        default=True, description="Remove duplicate records"
    )
    fill_missing_values: bool = Field(default=True, description="Fill missing values")
    missing_value_method: str = Field(
        default=CleaningConstants.FORWARD_FILL,
        description="Method for filling missing values",
    )
    remove_outliers: bool = Field(
        default=True, description="Remove statistical outliers"
    )
    outlier_method: str = Field(
        default=CleaningConstants.IQR_METHOD, description="Outlier detection method"
    )
    outlier_threshold: float = Field(
        default=CleaningConstants.IQR_DEFAULT_MULTIPLIER,
        description="Outlier threshold multiplier",
    )
    validate_price_relationships: bool = Field(
        default=True, description="Validate price relationships"
    )
    ensure_consistent_types: bool = Field(
        default=True, description="Ensure consistent data types"
    )
    sort_by_date: bool = Field(default=True, description="Sort data by date")


class DataCleaner:
    """Cleans and validates market data for analysis."""

    def __init__(self, config: Optional[CleaningConfig] = None):
        """Initialize the data cleaner.

        Args:
            config: Cleaning configuration options
        """
        self.config = config or CleaningConfig()
        self.cleaning_operations: list[str] = []
        self.outliers_removed = 0
        self.missing_values_filled = 0

    def clean(self, raw_data: RawMarketData) -> CleanedMarketData:
        """Clean raw market data.

        Args:
            raw_data: Raw market data to clean

        Returns:
            CleanedMarketData with cleaned DataFrame
        """
        logger.info("Starting data cleaning for %s", raw_data.symbol)

        # Reset counters
        self.cleaning_operations = []
        self.outliers_removed = 0
        self.missing_values_filled = 0

        # Convert to DataFrame
        df = raw_data.to_dataframe()
        original_count = len(df)

        logger.info("Original data shape: %s", df.shape)

        # Apply cleaning operations
        df = self._ensure_consistent_types(df)
        df = self._sort_by_date(df)
        df = self._remove_duplicates(df)
        df = self._validate_price_relationships(df)
        df = self._fill_missing_values(df)
        df = self._remove_outliers(df)

        logger.info("Cleaned data shape: %s", df.shape)
        logger.info("Records removed: %s", original_count - len(df))
        logger.info("Cleaning operations applied: %s", self.cleaning_operations)

        # Create cleaned data object
        cleaned_data = CleanedMarketData(
            raw_data=raw_data,
            cleaning_applied=self.cleaning_operations.copy(),
            outliers_removed=self.outliers_removed,
            missing_values_filled=self.missing_values_filled,
        )

        return cleaned_data

    def _ensure_consistent_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent data types across columns."""
        if not self.config.ensure_consistent_types:
            return df

        try:
            df = DataFrameUtils.ensure_numeric_types(df)
            self.cleaning_operations.append("ensure_consistent_types")
            logger.debug("Data types standardized")

        except Exception as e:
            logger.warning("Error ensuring consistent types: %s", e)

        return df

    def _sort_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sort DataFrame by date index."""
        if not self.config.sort_by_date:
            return df

        try:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.sort_index()
                self.cleaning_operations.append("sort_by_date")
                logger.debug("Data sorted by date")
        except Exception as e:
            logger.warning("Error sorting by date: %s", e)

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records based on date and symbol."""
        if not self.config.remove_duplicates:
            return df

        initial_count = len(df)

        try:
            # Remove duplicates based on index (date) and Symbol
            df = (
                df.reset_index()
                .drop_duplicates(
                    subset=[MarketDataColumns.DATE, MarketDataColumns.SYMBOL],
                    keep="first",
                )
                .set_index(MarketDataColumns.DATE)
            )

            duplicates_removed = initial_count - len(df)
            if duplicates_removed > 0:
                self.cleaning_operations.append(
                    f"remove_duplicates_{duplicates_removed}"
                )
                logger.info("Removed %s duplicate records", duplicates_removed)

        except Exception as e:
            logger.warning("Error removing duplicates: %s", e)

        return df

    def _validate_price_relationships(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate price relationships (High >= Low, Close within range)."""
        if not self.config.validate_price_relationships:
            return df

        try:
            initial_count = len(df)
            df, removal_counts = PriceValidator.validate_price_relationships(df)

            total_removed = initial_count - len(df)
            if total_removed > 0:
                self.cleaning_operations.append(
                    f"validate_price_relationships_{total_removed}"
                )

        except Exception as e:
            logger.warning("Error validating price relationships: %s", e)

        return df

    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values in the DataFrame."""
        if not self.config.fill_missing_values:
            return df

        try:
            missing_before = df.isnull().sum().sum()

            if missing_before == 0:
                return df

            if self.config.missing_value_method == CleaningConstants.FORWARD_FILL:
                df = df.fillna(method="ffill")
            elif self.config.missing_value_method == CleaningConstants.BACKWARD_FILL:
                df = df.fillna(method="bfill")
            elif self.config.missing_value_method == CleaningConstants.INTERPOLATE:
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                df[numeric_columns] = df[numeric_columns].interpolate(method="linear")
            elif self.config.missing_value_method == CleaningConstants.MEAN_FILL:
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                df[numeric_columns] = df[numeric_columns].fillna(
                    df[numeric_columns].mean()
                )

            missing_after = df.isnull().sum().sum()
            filled_count = missing_before - missing_after

            if filled_count > 0:
                self.missing_values_filled = filled_count
                self.cleaning_operations.append(
                    f"fill_missing_values_{self.config.missing_value_method}_{filled_count}"
                )
                logger.info(
                    "Filled %s missing values using %s", filled_count, self.config.missing_value_method
                )

        except Exception as e:
            logger.warning("Error filling missing values: %s", e)

        return df

    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove statistical outliers from price data."""
        if not self.config.remove_outliers:
            return df

        try:
            df, total_removed = OutlierDetector.remove_outliers_from_dataframe(
                df=df,
                columns=MarketDataColumns.PRICE_COLUMNS,
                method=self.config.outlier_method,
                threshold=self.config.outlier_threshold,
            )

            if total_removed > 0:
                self.outliers_removed = total_removed
                self.cleaning_operations.append(
                    f"remove_outliers_{self.config.outlier_method}_{total_removed}"
                )
                logger.info(
                    "Removed %s outliers using %s", total_removed, self.config.outlier_method
                )

        except Exception as e:
            logger.warning("Error removing outliers: %s", e)

        return df
