"""Alpha Vantage API client with comprehensive error handling and async support.

This module provides a robust client for the Alpha Vantage API with features including:
- Synchronous and asynchronous request methods
- Exponential backoff retry logic with jitter
- Comprehensive error handling with custom exception hierarchy
- Rate limiting and timeout management
- Context manager support for resource cleanup
- Detailed logging for debugging and monitoring
- Modern Python 3.11 type hints and patterns
- Enhanced security and connection pooling
"""

import asyncio
import logging
import random
import sys
import time
from typing import Any

import aiohttp
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_api_config
from .constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    OutputSize,
)


class AlphaVantageAPIError(Exception):
    """Base exception for Alpha Vantage API errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize with message and optional error code.

        Args:
            message: Error message
            error_code: Optional error code from API
        """
        super().__init__(message)
        self.error_code = error_code


class AlphaVantageRateLimitError(AlphaVantageAPIError):
    """Exception for rate limit exceeded errors."""


class AlphaVantageRequestError(AlphaVantageAPIError):
    """Exception for request-related errors."""


class AlphaVantageConfigError(AlphaVantageAPIError):
    """Exception for configuration-related errors."""


class AlphaVantageAuthenticationError(AlphaVantageAPIError):
    """Exception for authentication/authorization errors."""


class AlphaVantageTimeoutError(AlphaVantageAPIError):
    """Exception for request timeout errors."""


class AlphaVantageDataError(AlphaVantageAPIError):
    """Exception for data validation/format errors."""


class AlphaVantageClient:
    """Client for Alpha Vantage financial data API.

    Provides both synchronous and asynchronous methods for fetching
    financial data with proper error handling, retry logic, and rate limiting.

    Features:
    - Connection pooling for improved performance
    - Exponential backoff with jitter
    - Comprehensive error handling
    - Request/response logging
    - Modern async patterns
    """

    def __init__(self, api_key: str | None = None, config: Any | None = None) -> None:
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

        # Setup session with connection pooling and retry strategy
        self.session = self._create_session()
        self._aio_session: aiohttp.ClientSession | None = None

        self.logger.info(
            "Alpha Vantage client initialized with %d max retries and %ds rate limit",
            self.config.max_retries,
            self.config.rate_limit_delay,
        )

    def _create_session(self) -> requests.Session:
        """Create HTTP session with connection pooling and retry strategy.

        Returns:
            Configured requests session
        """
        self.logger.debug("Creating HTTP session with connection pooling")
        session = requests.Session()

        # Configure retry strategy at the urllib3 level
        retry_strategy = Retry(
            total=0,  # We handle retries at application level
            connect=2,  # Only retry connection errors
            read=2,
            status_forcelist=[500, 502, 503, 504],  # Server errors
            backoff_factor=1,
        )

        # Setup HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=20,  # Maximum number of connections to save in pool
            max_retries=retry_strategy,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set common headers
        session.headers.update(
            {
                "User-Agent": f"ticker-converter/{self.config.__class__.__name__}",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        self.logger.debug(
            "HTTP session created with pool size 20 and 10 connections per pool"
        )
        return session

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
        """Async context manager entry with connection pooling."""
        self.logger.debug("Initializing async HTTP session with connection pooling")

        connector = aiohttp.TCPConnector(
            limit=20,  # Total connection limit
            limit_per_host=10,  # Connection limit per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=30,  # Connection timeout
            sock_read=self.config.timeout,  # Socket read timeout
        )

        self._aio_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": f"TickerConverter/1.0 (Python/{sys.version.split()[0]})"
            },
        )

        self.logger.debug(
            "Async HTTP session created with connector limits: %d total, %d per host",
            20,
            10,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._aio_session:
            self.logger.debug("Closing async HTTP session")
            await self._aio_session.close()
            self.logger.debug("Async HTTP session closed")

    def close(self) -> None:
        """Close synchronous session."""
        self.logger.debug("Closing synchronous HTTP session")
        self.session.close()
        self.logger.debug("Synchronous HTTP session closed")

    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self._aio_session:
            self.logger.debug("Closing async HTTP session via aclose")
            await self._aio_session.close()
            self.logger.debug("Async HTTP session closed via aclose")

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
                    self.config.base_url,
                    params=params,
                    timeout=self.config.timeout,
                    stream=False,  # Ensure connection is closed after response
                )

                # Enhanced status code handling
                if response.status_code == 401:
                    raise AlphaVantageAuthenticationError("Invalid API key")
                elif response.status_code == 403:
                    raise AlphaVantageAuthenticationError("API access forbidden")
                elif response.status_code == 429:
                    raise AlphaVantageRateLimitError("Rate limit exceeded (HTTP 429)")

                response.raise_for_status()

                try:
                    data: dict[str, Any] = response.json()
                except ValueError as e:
                    raise AlphaVantageDataError(f"Invalid JSON response: {e}") from e

                # Log response size for monitoring
                response_size = len(response.content)
                self.logger.debug("Response received: %d bytes", response_size)

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
                        wait_time = self._calculate_backoff_delay_with_jitter(attempt)
                        self.logger.info(
                            "Rate limit detected, backing off for %.1f seconds",
                            wait_time,
                        )
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
                    wait_time = self._calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Retrying in %.1f seconds", wait_time)
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

    def _calculate_backoff_delay_with_jitter(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter.

        Jitter helps prevent thundering herd problems when multiple
        clients retry simultaneously.

        Args:
            attempt: Current attempt number (0-based).

        Returns:
            Delay in seconds with jitter.
        """
        base_delay = self.config.rate_limit_delay * (2**attempt)
        max_delay = min(base_delay, 300)  # Max 5 minutes

        # Add jitter: random factor between 0.5 and 1.5
        jitter = 0.5 + random.random()
        delay_with_jitter = max_delay * jitter

        return float(min(delay_with_jitter, 300.0))

    async def make_request_async(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make an async request to the Alpha Vantage API with retry logic.

        Args:
            params: API request parameters.

        Returns:
            JSON response from the API.

        Raises:
            AlphaVantageAuthenticationError: If API key is invalid.
            AlphaVantageTimeoutError: If request times out.
            AlphaVantageDataError: If response data is invalid.
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

                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                async with self._aio_session.get(
                    self.config.base_url, params=params, timeout=timeout
                ) as response:
                    # Enhanced HTTP status code handling
                    if response.status == 401 or response.status == 403:
                        error_text = await response.text()
                        self.logger.error(
                            "Authentication failed (status %d): %s",
                            response.status,
                            error_text,
                        )
                        raise AlphaVantageAuthenticationError(
                            f"Invalid API key or insufficient permissions (HTTP {response.status})"
                        )

                    if response.status == 429:
                        self.logger.warning("Rate limit hit (HTTP 429)")
                        if attempt < self.config.max_retries - 1:
                            wait_time = self._calculate_backoff_delay_with_jitter(
                                attempt
                            )
                            self.logger.info(
                                "Rate limit backoff: %.2f seconds", wait_time
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise AlphaVantageRateLimitError(
                                f"Rate limit exceeded after {self.config.max_retries} attempts (HTTP 429)"
                            )

                    if not (200 <= response.status < 300):
                        error_text = await response.text()
                        self.logger.error(
                            "HTTP error %d: %s", response.status, error_text
                        )
                        raise AlphaVantageRequestError(
                            f"HTTP {response.status}: {error_text}"
                        )

                    try:
                        data: dict[str, Any] = await response.json()
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        self.logger.error("Failed to parse JSON response: %s", str(e))
                        raise AlphaVantageDataError(
                            "Invalid JSON response from API"
                        ) from e

                # Check for API errors in response data
                if AlphaVantageResponseKey.ERROR_MESSAGE.value in data:
                    error_msg = data[AlphaVantageResponseKey.ERROR_MESSAGE.value]
                    self.logger.error("API error received: %s", error_msg)
                    raise AlphaVantageAPIError(f"API Error: {error_msg}")

                if AlphaVantageResponseKey.NOTE.value in data:
                    # Rate limit hit, wait and retry
                    note_msg = data[AlphaVantageResponseKey.NOTE.value]
                    self.logger.warning("Rate limit detected in response: %s", note_msg)

                    if attempt < self.config.max_retries - 1:
                        wait_time = self._calculate_backoff_delay_with_jitter(attempt)
                        self.logger.info("Rate limit backoff: %.2f seconds", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise AlphaVantageRateLimitError(
                            f"Rate limit exceeded after {self.config.max_retries} attempts: {note_msg}"
                        )

                # Apply rate limiting and return data
                await asyncio.sleep(self.config.rate_limit_delay)
                self.logger.debug("Async API request successful")
                return data

            except asyncio.TimeoutError as e:
                last_exception = e
                self.logger.warning(
                    "Async request timeout (attempt %d/%d)",
                    attempt + 1,
                    self.config.max_retries,
                )

                if attempt < self.config.max_retries - 1:
                    wait_time = self._calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Timeout retry in %.2f seconds", wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise AlphaVantageTimeoutError(
                        f"Request timed out after {self.config.max_retries} attempts"
                    ) from e

            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning(
                    "Async request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    str(e),
                )

                if attempt < self.config.max_retries - 1:
                    wait_time = self._calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Retrying in %.2f seconds", wait_time)
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
