"""Common utilities for ETL operations."""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .constants import MarketDataColumns, ValidationConstants

logger = logging.getLogger(__name__)


class PriceValidator:
    """Utility class for price validation operations."""

    @staticmethod
    def validate_price_relationships(
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, int]]:
        """Validate price relationships and return cleaned DataFrame with removal counts.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (cleaned_dataframe, removal_counts_dict)
        """
        removal_counts = {
            "invalid_price_relationships": 0,
            "negative_values": 0,
            "zero_volume": 0,
        }

        # Check if required columns exist
        required_cols = [
            MarketDataColumns.HIGH,
            MarketDataColumns.LOW,
            MarketDataColumns.CLOSE,
        ]
        if not all(col in df.columns for col in required_cols):
            logger.warning("Missing required price columns for validation")
            return df, removal_counts

        # Remove rows where High < Low
        invalid_high_low = df[MarketDataColumns.HIGH] < df[MarketDataColumns.LOW]
        if invalid_high_low.any():
            removal_counts["high_low_violations"] = invalid_high_low.sum()
            df = df[~invalid_high_low]
            logger.warning(
                "Removed %s rows with High < Low", removal_counts['high_low_violations']
            )

        # Remove rows where Close is outside High/Low range
        invalid_close = (df[MarketDataColumns.CLOSE] > df[MarketDataColumns.HIGH]) | (
            df[MarketDataColumns.CLOSE] < df[MarketDataColumns.LOW]
        )
        if invalid_close.any():
            removal_counts["close_range_violations"] = invalid_close.sum()
            df = df[~invalid_close]
            logger.warning(
                "Removed %s rows with Close outside High/Low range", removal_counts['close_range_violations']
            )

        # Remove rows with non-positive prices
        for col in MarketDataColumns.PRICE_COLUMNS:
            if col in df.columns:
                negative_prices = df[col] <= 0
                if negative_prices.any():
                    count = negative_prices.sum()
                    removal_counts["negative_prices"] += count
                    df = df[~negative_prices]
                    logger.warning(
                        "Removed %s rows with non-positive %s prices", count, col
                    )

        return df, removal_counts

    @staticmethod
    def check_price_validity(
        df: pd.DataFrame, config: Optional[dict] = None
    ) -> dict[str, int]:
        """Check price validity and return violation counts.

        Args:
            df: DataFrame to check
            config: Optional configuration dict with min/max price values

        Returns:
            Dictionary with violation counts
        """
        if config is None:
            config = {
                "min_price": ValidationConstants.MIN_PRICE_VALUE,
                "max_price": ValidationConstants.MAX_PRICE_VALUE,
                "max_daily_change": ValidationConstants.MAX_DAILY_PRICE_CHANGE,
            }

        violations = {
            "negative_prices": 0,
            "below_min_price": 0,
            "above_max_price": 0,
            "extreme_changes": 0,
        }

        for col in MarketDataColumns.PRICE_COLUMNS:
            if col not in df.columns:
                continue

            # Check for negative prices
            violations["negative_prices"] += (df[col] <= 0).sum()

            # Check for extreme prices
            violations["below_min_price"] += (df[col] < config["min_price"]).sum()
            violations["above_max_price"] += (df[col] > config["max_price"]).sum()

            # Check for extreme daily changes
            if len(df) > 1:
                daily_changes = df[col].pct_change(fill_method=None).abs()
                violations["extreme_changes"] += (
                    daily_changes > config["max_daily_change"]
                ).sum()

        return violations


class DataFrameUtils:
    """Utility functions for DataFrame operations."""

    @staticmethod
    def ensure_numeric_types(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure numeric columns have correct data types.

        Args:
            df: DataFrame to process

        Returns:
            DataFrame with corrected types
        """
        df = df.copy()

        # Ensure numeric columns are proper types
        for col in MarketDataColumns.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Ensure Volume is integer
        if MarketDataColumns.VOLUME in df.columns:
            df[MarketDataColumns.VOLUME] = (
                df[MarketDataColumns.VOLUME].fillna(0).astype("int64")
            )

        # Ensure Symbol is string
        if MarketDataColumns.SYMBOL in df.columns:
            df[MarketDataColumns.SYMBOL] = df[MarketDataColumns.SYMBOL].astype(str)

        return df

    @staticmethod
    def get_missing_value_stats(df: pd.DataFrame) -> dict[str, int]:
        """Get comprehensive missing value statistics.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with missing value statistics
        """
        return {
            "total_values": df.size,
            "missing_values": df.isnull().sum().sum(),
            "complete_records": len(df.dropna()),
            "missing_by_column": df.isnull().sum().to_dict(),
        }


class OutlierDetector:
    """Utility class for outlier detection methods."""

    @staticmethod
    def detect_outliers_iqr(series: pd.Series, threshold: float = 1.5) -> pd.Series:
        """Detect outliers using IQR method.

        Args:
            series: Pandas Series to check
            threshold: IQR multiplier threshold

        Returns:
            Boolean Series indicating outliers
        """
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR

        return (series < lower_bound) | (series > upper_bound)

    @staticmethod
    def detect_outliers_zscore(series: pd.Series, threshold: float = 2.0) -> pd.Series:
        """Detect outliers using Z-score method.

        Args:
            series: Pandas Series to check
            threshold: Z-score threshold

        Returns:
            Boolean Series indicating outliers
        """
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold

    @staticmethod
    def remove_outliers_from_dataframe(
        df: pd.DataFrame,
        columns: list[str],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> tuple[pd.DataFrame, int]:
        """Remove outliers from specified columns in DataFrame.

        Args:
            df: DataFrame to process
            columns: List of column names to check for outliers
            method: Outlier detection method ('iqr' or 'zscore')
            threshold: Threshold value for outlier detection

        Returns:
            Tuple of (cleaned_dataframe, total_outliers_removed)
        """
        initial_count = len(df)
        outlier_mask = pd.Series(False, index=df.index)

        for col in columns:
            if col not in df.columns:
                continue

            if method == "iqr":
                col_outliers = OutlierDetector.detect_outliers_iqr(df[col], threshold)
            elif method == "zscore":
                col_outliers = OutlierDetector.detect_outliers_zscore(
                    df[col], threshold
                )
            else:
                logger.warning("Unknown outlier method: %s", method)
                continue

            outlier_mask |= col_outliers

        cleaned_df = df[~outlier_mask]
        outliers_removed = initial_count - len(cleaned_df)

        return cleaned_df, outliers_removed


class FeatureEngineering:
    """Common feature engineering utilities."""

    @staticmethod
    def calculate_returns(
        df: pd.DataFrame, price_col: str = MarketDataColumns.CLOSE
    ) -> pd.DataFrame:
        """Calculate various return metrics.

        Args:
            df: DataFrame with price data
            price_col: Column name for price (default: Close)

        Returns:
            DataFrame with added return columns
        """
        df = df.copy()

        # Daily returns
        df["Daily_Return"] = df[price_col].pct_change()

        # Log returns
        df["Log_Return"] = np.log(df[price_col] / df[price_col].shift(1))

        # Cumulative returns
        df["Cumulative_Return"] = (1 + df["Daily_Return"]).cumprod() - 1

        return df

    @staticmethod
    def calculate_moving_average(
        df: pd.DataFrame, column: str, period: int
    ) -> pd.Series:
        """Calculate moving average for a column.

        Args:
            df: DataFrame
            column: Column name
            period: Period for moving average

        Returns:
            Series with moving average values
        """
        return df[column].rolling(window=period, min_periods=1).mean()

    @staticmethod
    def calculate_true_range(df: pd.DataFrame) -> pd.Series:
        """Calculate True Range for ATR calculation.

        Args:
            df: DataFrame with OHLC data

        Returns:
            Series with True Range values
        """
        high_low = df[MarketDataColumns.HIGH] - df[MarketDataColumns.LOW]
        high_close_prev = np.abs(
            df[MarketDataColumns.HIGH] - df[MarketDataColumns.CLOSE].shift(1)
        )
        low_close_prev = np.abs(
            df[MarketDataColumns.LOW] - df[MarketDataColumns.CLOSE].shift(1)
        )

        return pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(
            axis=1
        )
