"""Alpha Vantage API client for financial data."""

import time
from typing import Any, Optional

import pandas as pd
import requests

from .config import config
from .constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    OutputSize,
)


class AlphaVantageAPIError(Exception):
    """Custom exception for Alpha Vantage API errors."""


class AlphaVantageClient:
    """Client for Alpha Vantage financial data API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Alpha Vantage client.

        Args:
            api_key: Alpha Vantage API key. If not provided, uses config.
        """
        self.api_key = api_key or config.ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            raise AlphaVantageAPIError("Alpha Vantage API key is required")

        self.base_url = config.ALPHA_VANTAGE_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.rate_limit_delay = config.RATE_LIMIT_DELAY

        self.session = requests.Session()

    def _make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a request to the Alpha Vantage API with retry logic.

        Args:
            params: API request parameters.

        Returns:
            JSON response from the API.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params["apikey"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    self.base_url, params=params, timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()

                # Check for API errors
                if AlphaVantageResponseKey.ERROR_MESSAGE in data:
                    raise AlphaVantageAPIError(
                        f"API Error: {data[AlphaVantageResponseKey.ERROR_MESSAGE]}"
                    )

                if AlphaVantageResponseKey.NOTE in data:
                    # Rate limit hit, wait and retry
                    if attempt < self.max_retries - 1:
                        wait_time = self.rate_limit_delay * (2**attempt)
                        time.sleep(wait_time)
                        continue
                    raise AlphaVantageAPIError(
                        f"Rate limit exceeded: {data[AlphaVantageResponseKey.NOTE]}"
                    )

                # Apply rate limiting and return data
                time.sleep(self.rate_limit_delay)
                return data

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.rate_limit_delay * (2**attempt)
                    time.sleep(wait_time)
                    continue
                raise AlphaVantageAPIError(
                    f"Request failed after {self.max_retries} attempts: {e}"
                ) from e

        # This should never be reached, but needed for mypy
        raise AlphaVantageAPIError("Unexpected error: max retries exceeded")

    def _convert_time_series_to_dataframe(
        self,
        time_series: dict[str, dict[str, str]],
        datetime_key: str = "Date",
        additional_columns: Optional[dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Convert Alpha Vantage time series data to DataFrame.

        Args:
            time_series: Time series data from Alpha Vantage API
            datetime_key: Name for the datetime column ('Date' or 'DateTime')
            additional_columns: Additional columns to add to each row

        Returns:
            Sorted DataFrame with time series data
        """
        df_data = []
        additional_columns = additional_columns or {}

        for datetime_str, values in time_series.items():
            row: dict[str, Any] = {datetime_key: pd.to_datetime(datetime_str)}

            # Standard OHLCV columns
            if AlphaVantageValueKey.OPEN in values:
                row.update(
                    {
                        "Open": float(values[AlphaVantageValueKey.OPEN]),
                        "High": float(values[AlphaVantageValueKey.HIGH]),
                        "Low": float(values[AlphaVantageValueKey.LOW]),
                        "Close": float(values[AlphaVantageValueKey.CLOSE]),
                    }
                )

            # Volume handling (different keys for different endpoints)
            if AlphaVantageValueKey.VOLUME in values:
                volume_value = values[AlphaVantageValueKey.VOLUME]
                row["Volume"] = (
                    int(volume_value) if volume_value.isdigit() else float(volume_value)
                )

            # Add any additional columns
            row.update(additional_columns)
            df_data.append(row)

        df = pd.DataFrame(df_data)
        return df.sort_values(datetime_key).reset_index(drop=True)

    def get_daily_stock_data(
        self, symbol: str, outputsize: str = OutputSize.COMPACT
    ) -> pd.DataFrame:
        """Get daily stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            outputsize: 'compact' for last 100 data points, 'full' for all data.

        Returns:
            DataFrame with daily stock data (Date, Open, High, Low, Close, Volume).
        """
        params = {
            "function": AlphaVantageFunction.TIME_SERIES_DAILY,
            "symbol": symbol.upper(),
            "outputsize": outputsize,
        }

        data = self._make_request(params)

        # Extract time series data
        time_series_key = AlphaVantageResponseKey.TIME_SERIES_DAILY
        if time_series_key not in data:
            # Handle common API response variations
            available_keys = list(data.keys())
            if "Information" in available_keys:
                raise AlphaVantageAPIError(
                    f"API Information message: {data.get('Information', 'Rate limit or service issue')}"
                )
            raise AlphaVantageAPIError(f"Unexpected response format: {available_keys}")

        time_series = data[time_series_key]

        # Convert to DataFrame using helper method
        df = self._convert_time_series_to_dataframe(
            time_series,
            datetime_key="Date",
            additional_columns={"Symbol": symbol.upper()},
        )

        return df

    def get_intraday_stock_data(
        self, symbol: str, interval: str = "5min"
    ) -> pd.DataFrame:
        """Get intraday stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            interval: Time interval ('1min', '5min', '15min', '30min', '60min').

        Returns:
            DataFrame with intraday stock data.
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol.upper(),
            "interval": interval,
        }

        data = self._make_request(params)

        # Extract time series data
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            raise AlphaVantageAPIError(
                f"Unexpected response format: {list(data.keys())}"
            )

        time_series = data[time_series_key]

        # Convert to DataFrame using helper method
        df = self._convert_time_series_to_dataframe(
            time_series,
            datetime_key="DateTime",
            additional_columns={"Symbol": symbol.upper()},
        )

        return df

    def get_company_overview(self, symbol: str) -> dict[str, Any]:
        """Get company overview information for a stock symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').

        Returns:
            Dictionary containing company overview data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {"function": "OVERVIEW", "symbol": symbol}
        return self._make_request(params)

    def get_currency_exchange_rate(
        self, from_currency: str, to_currency: str
    ) -> dict[str, Any]:
        """Get real-time exchange rate for currency pair.

        Args:
            from_currency: Source currency code (e.g., 'USD', 'BTC').
            to_currency: Target currency code (e.g., 'EUR', 'USD').

        Returns:
            Dictionary containing exchange rate data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
        }
        return self._make_request(params)

    def get_forex_daily(
        self, from_symbol: str, to_symbol: str, outputsize: str = "compact"
    ) -> pd.DataFrame:
        """Get daily forex time series data.

        Args:
            from_symbol: Source currency (e.g., 'EUR').
            to_symbol: Target currency (e.g., 'USD').
            outputsize: 'compact' (100 points) or 'full' (all data).

        Returns:
            DataFrame with forex time series data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": outputsize,
        }

        data = self._make_request(params)

        # Parse forex time series data
        time_series_key = "Time Series FX (Daily)"
        if time_series_key not in data:
            # Handle common API response variations
            available_keys = list(data.keys())
            if "Information" in available_keys:
                raise AlphaVantageAPIError(
                    f"API Information message: {data.get('Information', 'Rate limit or service issue')}"
                )
            raise AlphaVantageAPIError(
                f"Unexpected forex data format: {available_keys}"
            )

        time_series = data[time_series_key]

        # Convert to DataFrame
        df_data = []
        for date_str, values in time_series.items():
            df_data.append(
                {
                    "Date": pd.to_datetime(date_str),
                    "Open": float(values["1. open"]),
                    "High": float(values["2. high"]),
                    "Low": float(values["3. low"]),
                    "Close": float(values["4. close"]),
                    "From_Symbol": from_symbol,
                    "To_Symbol": to_symbol,
                }
            )

        df = pd.DataFrame(df_data)
        df = df.sort_values("Date")
        return df.reset_index(drop=True)

    def get_digital_currency_daily(
        self, symbol: str, market: str = "USD"
    ) -> pd.DataFrame:
        """Get daily digital currency time series data.

        Args:
            symbol: Digital currency symbol (e.g., 'BTC', 'ETH').
            market: Market currency (e.g., 'USD', 'EUR').

        Returns:
            DataFrame with digital currency time series data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
        }

        data = self._make_request(params)

        # Parse digital currency time series data
        time_series_key = "Time Series (Digital Currency Daily)"
        if time_series_key not in data:
            # Handle common API response variations
            available_keys = list(data.keys())
            if "Information" in available_keys:
                raise AlphaVantageAPIError(
                    f"API Information message: {data.get('Information', 'Rate limit or service issue')}"
                )
            raise AlphaVantageAPIError(
                f"Unexpected crypto data format: {available_keys}"
            )

        time_series = data[time_series_key]

        # Convert to DataFrame
        df_data = []
        for date_str, values in time_series.items():
            # Handle both old and new API response formats
            try:
                # Try new format first (current Alpha Vantage format)
                df_data.append(
                    {
                        "Date": pd.to_datetime(date_str),
                        "Open_Market": float(values["1. open"]),
                        "High_Market": float(values["2. high"]),
                        "Low_Market": float(values["3. low"]),
                        "Close_Market": float(values["4. close"]),
                        "Open_USD": float(values["1. open"]),  # For compatibility
                        "High_USD": float(values["2. high"]),
                        "Low_USD": float(values["3. low"]),
                        "Close_USD": float(values["4. close"]),
                        "Volume": float(values["5. volume"]),
                        "Symbol": symbol,
                        "Market": market,
                    }
                )
            except KeyError:
                # Fall back to old format if new format fails
                df_data.append(
                    {
                        "Date": pd.to_datetime(date_str),
                        "Open_Market": float(values[f"1a. open ({market})"]),
                        "High_Market": float(values[f"2a. high ({market})"]),
                        "Low_Market": float(values[f"3a. low ({market})"]),
                        "Close_Market": float(values[f"4a. close ({market})"]),
                        "Open_USD": float(values["1b. open (USD)"]),
                        "High_USD": float(values["2b. high (USD)"]),
                        "Low_USD": float(values["3b. low (USD)"]),
                        "Close_USD": float(values["4b. close (USD)"]),
                        "Volume": float(values["5. volume"]),
                        "Market_Cap_USD": float(values["6. market cap (USD)"]),
                        "Symbol": symbol,
                        "Market": market,
                    }
                )

        df = pd.DataFrame(df_data)
        df = df.sort_values("Date")
        return df.reset_index(drop=True)
