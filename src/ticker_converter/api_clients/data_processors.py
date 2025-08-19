"""Data processing utilities for Alpha Vantage API responses.

This module contains functions for converting API responses to pandas DataFrames
and other data transformation utilities.
"""

from typing import Any

import pandas as pd

from .constants import AlphaVantageValueKey


def convert_time_series_to_dataframe(
    time_series: dict[str, dict[str, str]],
    datetime_key: str = "Date",
    additional_columns: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Convert Alpha Vantage time series data to DataFrame.

    Args:
        time_series: Time series data from Alpha Vantage API
        datetime_key: Name for the datetime column ('Date' or 'DateTime')
        additional_columns: Additional columns to add to each row

    Returns:
        Sorted DataFrame with time series data
    """
    # Handle None input
    if time_series is None:
        return pd.DataFrame()

    # Handle empty dictionary
    if not time_series:
        return pd.DataFrame()

    df_data = []
    additional_columns = additional_columns or {}

    for datetime_str, values in time_series.items():
        row: dict[str, Any] = {datetime_key: pd.to_datetime(datetime_str)}

        # Standard OHLCV columns
        if AlphaVantageValueKey.OPEN.value in values:
            row.update(
                {
                    "Open": float(values[AlphaVantageValueKey.OPEN.value]),
                    "High": float(values[AlphaVantageValueKey.HIGH.value]),
                    "Low": float(values[AlphaVantageValueKey.LOW.value]),
                    "Close": float(values[AlphaVantageValueKey.CLOSE.value]),
                }
            )

        # Volume handling (different keys for different endpoints)
        if AlphaVantageValueKey.VOLUME.value in values:
            volume_value = values[AlphaVantageValueKey.VOLUME.value]
            row["Volume"] = (
                int(volume_value) if volume_value.isdigit() else float(volume_value)
            )

        # Add any additional columns
        row.update(additional_columns)
        df_data.append(row)

    df = pd.DataFrame(df_data)

    # Only sort if the DataFrame has the datetime column
    if not df.empty and datetime_key in df.columns:
        return df.sort_values(datetime_key).reset_index(drop=True)

    return df


def process_forex_time_series(
    time_series: dict[str, dict[str, str]],
    from_currency: str,
    to_currency: str,
) -> pd.DataFrame:
    """Process forex time series data into DataFrame.

    Args:
        time_series: Time series data from Alpha Vantage API
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        DataFrame with forex time series data
    """
    df_data = []

    for datetime_str, values in time_series.items():
        row = {
            "DateTime": pd.to_datetime(datetime_str),
            "Open": float(values[AlphaVantageValueKey.OPEN.value]),
            "High": float(values[AlphaVantageValueKey.HIGH.value]),
            "Low": float(values[AlphaVantageValueKey.LOW.value]),
            "Close": float(values[AlphaVantageValueKey.CLOSE.value]),
            "FromCurrency": from_currency,
            "ToCurrency": to_currency,
        }
        df_data.append(row)

    df = pd.DataFrame(df_data)
    return df.sort_values("DateTime").reset_index(drop=True)


def process_digital_currency_time_series(
    time_series: dict[str, dict[str, str]],
    currency_code: str,
    market_code: str,
) -> pd.DataFrame:
    """Process digital currency time series data into DataFrame.

    Args:
        time_series: Time series data from Alpha Vantage API
        currency_code: Digital currency code (e.g., BTC)
        market_code: Market currency code (e.g., USD)

    Returns:
        DataFrame with digital currency time series data
    """
    df_data = []

    for datetime_str, values in time_series.items():
        # Extract values in market currency
        open_key = f"1a. open ({market_code})"
        high_key = f"2a. high ({market_code})"
        low_key = f"3a. low ({market_code})"
        close_key = f"4a. close ({market_code})"
        volume_key = "5. volume"
        market_cap_key = f"6. market cap ({market_code})"

        row = {
            "DateTime": pd.to_datetime(datetime_str),
            "Open": float(values.get(open_key, 0)),
            "High": float(values.get(high_key, 0)),
            "Low": float(values.get(low_key, 0)),
            "Close": float(values.get(close_key, 0)),
            "Volume": float(values.get(volume_key, 0)),
            "MarketCap": float(values.get(market_cap_key, 0)),
            "CurrencyCode": currency_code,
            "MarketCode": market_code,
        }
        df_data.append(row)

    df = pd.DataFrame(df_data)
    return df.sort_values("DateTime").reset_index(drop=True)


def validate_time_series_data(time_series: dict[str, dict[str, str]]) -> None:
    """Validate time series data structure.

    Args:
        time_series: Time series data to validate

    Raises:
        ValueError: If data structure is invalid
    """
    if not isinstance(time_series, dict):
        raise ValueError("Time series data must be a dictionary")

    if not time_series:
        raise ValueError("Time series data is empty")

    # Check that each entry has the expected structure
    for date_key, values in time_series.items():
        if not isinstance(values, dict):
            raise ValueError(f"Values for {date_key} must be a dictionary")

        if not values:
            raise ValueError(f"Values for {date_key} are empty")


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize DataFrame column names.

    Args:
        df: DataFrame to standardize

    Returns:
        DataFrame with standardized column names
    """
    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Standard column name mappings
    column_mappings = {
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume",
        "datetime": "DateTime",
        "date": "Date",
    }

    # Apply mappings
    df_copy.columns = [column_mappings.get(col.lower(), col) for col in df_copy.columns]

    return df_copy
