"""Alpha Vantage API client with comprehensive error handling and async support.

This module provides a robust client for the Alpha Vantage API with features including:
- Synchronous and asynchronous request methods
- Exponential backoff retry logic with jitter
- Comprehensive error handling with custom exception hierarchy
- Rate limiting and timeout management
- Context manager support for resource cleanup
- Detailed logging for debugging and monitoring
"""

import asyncio
import logging
import time
from typing import Any

import aiohttp
import pandas as pd
import requests

from ..config import get_api_config
from .constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    OutputSize,
)


class AlphaVantageAPIError(Exception):
    """Base exception for Alpha Vantage API errors."""


class AlphaVantageRateLimitError(AlphaVantageAPIError):
    """Exception for rate limit exceeded errors."""


class AlphaVantageRequestError(AlphaVantageAPIError):
    """Exception for request-related errors."""


class AlphaVantageConfigError(AlphaVantageAPIError):
    """Exception for configuration-related errors."""


class AlphaVantageClient:
    """Client for Alpha Vantage financial data API.

    Provides both synchronous and asynchronous methods for fetching
    financial data with proper error handling, retry logic, and rate limiting.
    """

    def __init__(self, api_key: str | None = None, config: Any | None = None):
        """Initialize the Alpha Vantage client.

        Args:
            api_key: Alpha Vantage API key. If not provided, uses config.
            config: API configuration. If not provided, uses default config.

        Raises:
            AlphaVantageConfigError: If API key is invalid or missing.
        """
        self.config = config or get_api_config()
        self.api_key = api_key or self.config.api_key.get_secret_value()
        self.logger = logging.getLogger(__name__)

        if not self.api_key or self.api_key == "demo":
            raise AlphaVantageConfigError("Valid Alpha Vantage API key is required")

        self.session = requests.Session()
        self._aio_session: aiohttp.ClientSession | None = None

        self.logger.info(
            "Alpha Vantage client initialized with %d max retries",
            self.config.max_retries,
        )

    @property
    def base_url(self) -> str:
        """Get the base URL for backwards compatibility."""
        return self.config.base_url

    @property
    def timeout(self) -> int:
        """Get the timeout for backwards compatibility."""
        return self.config.timeout

    @property
    def max_retries(self) -> int:
        """Get the max retries for backwards compatibility."""
        return self.config.max_retries

    @property
    def rate_limit_delay(self) -> int:
        """Get the rate limit delay for backwards compatibility."""
        return self.config.rate_limit_delay

    async def __aenter__(self) -> "AlphaVantageClient":
        """Async context manager entry."""
        self._aio_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._aio_session:
            await self._aio_session.close()

    def close(self) -> None:
        """Close synchronous session."""
        self.session.close()

    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self._aio_session:
            await self._aio_session.close()

    def make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a request to the Alpha Vantage API with retry logic.

        Args:
            params: API request parameters.

        Returns:
            JSON response from the API.

        Raises:
            AlphaVantageRateLimitError: If rate limit is exceeded.
            AlphaVantageRequestError: If the request fails.
            AlphaVantageAPIError: For other API errors.
        """
        params = params.copy()  # Avoid modifying original params
        params["apikey"] = self.api_key

        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(
                    "Making API request (attempt %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    params.get("function", "unknown"),
                )

                response = self.session.get(
                    self.config.base_url, params=params, timeout=self.config.timeout
                )
                response.raise_for_status()

                data: dict[str, Any] = response.json()

                # Check for API errors
                if AlphaVantageResponseKey.ERROR_MESSAGE.value in data:
                    error_msg = data[AlphaVantageResponseKey.ERROR_MESSAGE.value]
                    self.logger.error("API error received: %s", error_msg)
                    raise AlphaVantageAPIError(f"API Error: {error_msg}")

                if AlphaVantageResponseKey.NOTE.value in data:
                    # Rate limit hit, wait and retry
                    note_msg = data[AlphaVantageResponseKey.NOTE.value]
                    self.logger.warning("Rate limit detected: %s", note_msg)

                    if attempt < self.config.max_retries - 1:
                        wait_time = self._calculate_backoff_delay(attempt)
                        self.logger.info("Backing off for %d seconds", wait_time)
                        time.sleep(wait_time)
                        continue

                    raise AlphaVantageRateLimitError(
                        f"Rate limit exceeded after {self.config.max_retries} attempts: {note_msg}"
                    )

                # Apply rate limiting and return data
                time.sleep(self.config.rate_limit_delay)
                self.logger.debug("API request successful")
                return data

            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    str(e),
                )

                if attempt < self.config.max_retries - 1:
                    wait_time = self._calculate_backoff_delay(attempt)
                    self.logger.info("Retrying in %d seconds", wait_time)
                    time.sleep(wait_time)
                    continue

        # All attempts failed
        raise AlphaVantageRequestError(
            f"Request failed after {self.config.max_retries} attempts"
        ) from last_exception

    def _calculate_backoff_delay(self, attempt: int) -> int:
        """Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-based).

        Returns:
            Delay in seconds.
        """
        delay = self.config.rate_limit_delay * (2**attempt)
        return min(int(delay), 300)  # Max 5 minutes

    async def make_request_async(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make an async request to the Alpha Vantage API with retry logic.

        Args:
            params: API request parameters.

        Returns:
            JSON response from the API.

        Raises:
            AlphaVantageRateLimitError: If rate limit is exceeded.
            AlphaVantageRequestError: If the request fails.
            AlphaVantageAPIError: For other API errors.
        """
        if not self._aio_session:
            raise AlphaVantageConfigError(
                "Async session not initialized. Use async context manager."
            )

        params = params.copy()  # Avoid modifying original params
        params["apikey"] = self.api_key

        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                self.logger.debug(
                    "Making async API request (attempt %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    params.get("function", "unknown"),
                )

                async with self._aio_session.get(
                    self.config.base_url, params=params
                ) as response:
                    response.raise_for_status()
                    data: dict[str, Any] = await response.json()

                # Check for API errors
                if AlphaVantageResponseKey.ERROR_MESSAGE.value in data:
                    error_msg = data[AlphaVantageResponseKey.ERROR_MESSAGE.value]
                    self.logger.error("API error received: %s", error_msg)
                    raise AlphaVantageAPIError(f"API Error: {error_msg}")

                if AlphaVantageResponseKey.NOTE.value in data:
                    # Rate limit hit, wait and retry
                    note_msg = data[AlphaVantageResponseKey.NOTE.value]
                    self.logger.warning("Rate limit detected: %s", note_msg)

                    if attempt < self.config.max_retries - 1:
                        wait_time = self._calculate_backoff_delay(attempt)
                        self.logger.info("Backing off for %d seconds", wait_time)
                        await asyncio.sleep(wait_time)
                        continue

                    raise AlphaVantageRateLimitError(
                        f"Rate limit exceeded after {self.config.max_retries} attempts: {note_msg}"
                    )

                # Apply rate limiting and return data
                await asyncio.sleep(self.config.rate_limit_delay)
                self.logger.debug("Async API request successful")
                return data

            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning(
                    "Async request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    str(e),
                )

                if attempt < self.config.max_retries - 1:
                    wait_time = self._calculate_backoff_delay(attempt)
                    self.logger.info("Retrying in %d seconds", wait_time)
                    await asyncio.sleep(wait_time)
                    continue

        # All attempts failed
        raise AlphaVantageRequestError(
            f"Async request failed after {self.config.max_retries} attempts"
        ) from last_exception

    def _convert_time_series_to_dataframe(
        self,
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
        return df.sort_values(datetime_key).reset_index(drop=True)

    def _handle_api_error_response(self, data: dict[str, Any]) -> None:
        """Handle common API error responses.

        Args:
            data: API response data

        Raises:
            AlphaVantageAPIError: If response contains error indicators
        """
        available_keys = list(data.keys())
        if "Information" in available_keys:
            raise AlphaVantageAPIError(
                f"API Information message: {data.get('Information', 'Rate limit or service issue')}"
            )

    def get_daily_stock_data(
        self, symbol: str, outputsize: OutputSize | str = OutputSize.COMPACT
    ) -> pd.DataFrame:
        """Get daily stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            outputsize: Output size enum value or string.

        Returns:
            DataFrame with daily stock data (Date, Open, High, Low, Close, Volume).
        """
        # Handle both enum and string inputs for backwards compatibility
        output_value = (
            outputsize.value if isinstance(outputsize, OutputSize) else outputsize
        )

        params = {
            "function": AlphaVantageFunction.TIME_SERIES_DAILY.value,
            "symbol": symbol.upper(),
            "outputsize": output_value,
        }

        data = self.make_request(params)

        # Extract time series data
        time_series_key = AlphaVantageResponseKey.TIME_SERIES_DAILY.value
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected response format: {list(data.keys())}"
            )

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
            "function": AlphaVantageFunction.TIME_SERIES_INTRADAY.value,
            "symbol": symbol.upper(),
            "interval": interval,
        }

        data = self.make_request(params)

        # Extract time series data
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            self._handle_api_error_response(data)
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
        params = {"function": AlphaVantageFunction.OVERVIEW.value, "symbol": symbol}
        return self.make_request(params)

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
            "function": AlphaVantageFunction.CURRENCY_EXCHANGE_RATE.value,
            "from_currency": from_currency,
            "to_currency": to_currency,
        }
        return self.make_request(params)

    def get_forex_daily(
        self,
        from_symbol: str,
        to_symbol: str,
        outputsize: OutputSize | str = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Get daily forex time series data.

        Args:
            from_symbol: Source currency (e.g., 'EUR').
            to_symbol: Target currency (e.g., 'USD').
            outputsize: Output size enum value or string.

        Returns:
            DataFrame with forex time series data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        # Handle both enum and string inputs for backwards compatibility
        output_value = (
            outputsize.value if isinstance(outputsize, OutputSize) else outputsize
        )

        params = {
            "function": AlphaVantageFunction.FX_DAILY.value,
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": output_value,
        }

        data = self.make_request(params)

        # Parse forex time series data
        time_series_key = "Time Series FX (Daily)"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected forex data format: {list(data.keys())}"
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
            "function": AlphaVantageFunction.DIGITAL_CURRENCY_DAILY.value,
            "symbol": symbol,
            "market": market,
        }

        data = self.make_request(params)

        # Parse digital currency time series data
        time_series_key = "Time Series (Digital Currency Daily)"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected crypto data format: {list(data.keys())}"
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

    # Async versions of API methods
    async def get_intraday_async(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: OutputSize | str = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Async version of get_intraday."""
        output_value = (
            outputsize.value if isinstance(outputsize, OutputSize) else outputsize
        )

        params = {
            "function": AlphaVantageFunction.TIME_SERIES_INTRADAY.value,
            "symbol": symbol,
            "interval": interval,
            "outputsize": output_value,
        }

        data = await self.make_request_async(params)

        # Parse intraday time series data
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected intraday data format: {list(data.keys())}"
            )

        time_series = data[time_series_key]

        # Convert to DataFrame
        df_data = []
        for datetime_str, values in time_series.items():
            df_data.append(
                {
                    "Datetime": pd.to_datetime(datetime_str),
                    "Open": float(values["1. open"]),
                    "High": float(values["2. high"]),
                    "Low": float(values["3. low"]),
                    "Close": float(values["4. close"]),
                    "Volume": int(values["5. volume"]),
                    "Symbol": symbol,
                }
            )

        df = pd.DataFrame(df_data)
        df = df.sort_values("Datetime")
        return df.reset_index(drop=True)

    async def get_daily_async(
        self, symbol: str, outputsize: OutputSize | str = OutputSize.COMPACT
    ) -> pd.DataFrame:
        """Async version of get_daily."""
        output_value = (
            outputsize.value if isinstance(outputsize, OutputSize) else outputsize
        )

        params = {
            "function": AlphaVantageFunction.TIME_SERIES_DAILY.value,
            "symbol": symbol,
            "outputsize": output_value,
        }

        data = await self.make_request_async(params)

        # Parse daily time series data
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected daily data format: {list(data.keys())}"
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
                    "Volume": int(values["5. volume"]),
                    "Symbol": symbol,
                }
            )

        df = pd.DataFrame(df_data)
        df = df.sort_values("Date")
        return df.reset_index(drop=True)

    async def get_forex_daily_async(
        self,
        from_symbol: str,
        to_symbol: str,
        outputsize: OutputSize | str = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Async version of get_forex_daily."""
        output_value = (
            outputsize.value if isinstance(outputsize, OutputSize) else outputsize
        )

        params = {
            "function": AlphaVantageFunction.FX_DAILY.value,
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": output_value,
        }

        data = await self.make_request_async(params)

        # Parse forex time series data
        time_series_key = "Time Series FX (Daily)"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected forex data format: {list(data.keys())}"
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

    async def get_digital_currency_daily_async(
        self, symbol: str, market: str = "USD"
    ) -> pd.DataFrame:
        """Async version of get_digital_currency_daily."""
        params = {
            "function": AlphaVantageFunction.DIGITAL_CURRENCY_DAILY.value,
            "symbol": symbol,
            "market": market,
        }

        data = await self.make_request_async(params)

        # Parse digital currency time series data
        time_series_key = "Time Series (Digital Currency Daily)"
        if time_series_key not in data:
            self._handle_api_error_response(data)
            raise AlphaVantageAPIError(
                f"Unexpected crypto data format: {list(data.keys())}"
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
