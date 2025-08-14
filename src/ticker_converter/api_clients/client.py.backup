"""Streamlined Alpha Vantage API client with modern patterns.

This module provides a focused API client for the Alpha Vantage API with:
- Clean separation of concerns using extracted modules
- Modern Python 3.11 type hints and patterns
- Comprehensive error handling
- Async and sync support with connection pooling
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any

import aiohttp
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    OutputSize,
)
from .data_processors import (
    convert_time_series_to_dataframe,
    process_digital_currency_time_series,
    process_forex_time_series,
)
from .exceptions import (
    AlphaVantageAPIError,
    AlphaVantageAuthenticationError,
    AlphaVantageConfigError,
    AlphaVantageDataError,
    AlphaVantageRateLimitError,
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)
from .utils import (
    calculate_backoff_delay_with_jitter,
    extract_error_message,
    extract_rate_limit_message,
    prepare_api_params,
)


class AlphaVantageClient:
    """Modern Alpha Vantage API client with enhanced error handling and async support."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Alpha Vantage API client.

        Args:
            api_key: Alpha Vantage API key. If None, will use environment variable.

        Raises:
            AlphaVantageConfigError: If API key is not provided or invalid.
        """
        # Simple configuration approach for refactoring
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")

        if not self.api_key:
            raise AlphaVantageConfigError(
                "Alpha Vantage API key is required. Set ALPHA_VANTAGE_API_KEY environment variable "
                "or provide api_key parameter."
            )

        # Configuration values
        self.base_url = "https://www.alphavantage.co/query"
        self.timeout = 30
        self.max_retries = 3
        self.rate_limit_delay = 12

        self.logger = logging.getLogger(__name__)
        self._setup_sync_session()
        self._aio_session: aiohttp.ClientSession | None = None

    def _setup_sync_session(self) -> None:
        """Set up synchronous session with connection pooling and retry strategy."""
        retry_strategy = Retry(
            total=0,  # We handle retries manually for better control
            backoff_factor=0,
            status_forcelist=[],
        )

        adapter = HTTPAdapter(
            pool_connections=10, pool_maxsize=20, max_retries=retry_strategy
        )

        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {"User-Agent": f"TickerConverter/1.0 (Python/{sys.version.split()[0]})"}
        )

    async def __aenter__(self) -> "AlphaVantageClient":
        """Async context manager entry with optimized connection pooling."""
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(
            total=self.timeout, connect=30, sock_read=self.timeout
        )

        self._aio_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": f"TickerConverter/1.0 (Python/{sys.version.split()[0]})"
            },
        )
        self.logger.debug("Async session initialized with connection pooling")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with proper cleanup."""
        if self._aio_session:
            await self._aio_session.close()
            self.logger.debug("Async session closed")

    def close(self) -> None:
        """Close synchronous session."""
        self.session.close()
        self.logger.debug("Sync session closed")

    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self._aio_session:
            await self._aio_session.close()
            self.logger.debug("Async session closed")

    def make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a synchronous request to the Alpha Vantage API with retry logic.

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
        prepared_params = prepare_api_params(params, self.api_key)
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    "Making API request (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    params.get("function", "unknown"),
                )

                response = self.session.get(
                    self.base_url,
                    params=prepared_params,
                    timeout=self.timeout,
                )

                # Enhanced HTTP status code handling
                if response.status_code == 401 or response.status_code == 403:
                    self.logger.error(
                        "Authentication failed (status %d): %s",
                        response.status_code,
                        response.text,
                    )
                    raise AlphaVantageAuthenticationError(
                        f"Invalid API key or insufficient permissions (HTTP {response.status_code})"
                    )

                if response.status_code == 429:
                    self.logger.warning("Rate limit hit (HTTP 429)")
                    if attempt < self.max_retries - 1:
                        wait_time = calculate_backoff_delay_with_jitter(attempt)
                        self.logger.info("Rate limit backoff: %.2f seconds", wait_time)
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AlphaVantageRateLimitError(
                            f"Rate limit exceeded after {self.max_retries} attempts (HTTP 429)"
                        )

                response.raise_for_status()

                try:
                    data: dict[str, Any] = response.json()
                except ValueError as e:
                    self.logger.error("Failed to parse JSON response: %s", str(e))
                    raise AlphaVantageDataError("Invalid JSON response from API") from e

                # Check for API errors in response
                error_msg = extract_error_message(data)
                if error_msg:
                    self.logger.error("API error received: %s", error_msg)
                    raise AlphaVantageAPIError(f"API Error: {error_msg}")

                rate_limit_msg = extract_rate_limit_message(data)
                if rate_limit_msg:
                    self.logger.warning(
                        "Rate limit detected in response: %s", rate_limit_msg
                    )

                    if attempt < self.max_retries - 1:
                        wait_time = calculate_backoff_delay_with_jitter(attempt)
                        self.logger.info("Rate limit backoff: %.2f seconds", wait_time)
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AlphaVantageRateLimitError(
                            f"Rate limit exceeded after {self.max_retries} attempts: {rate_limit_msg}"
                        )

                # Apply rate limiting and return data
                time.sleep(self.rate_limit_delay)
                self.logger.debug("API request successful")
                return data

            except requests.Timeout as e:
                last_exception = e
                self.logger.warning(
                    "Request timeout (attempt %d/%d)",
                    attempt + 1,
                    self.max_retries,
                )

                if attempt < self.max_retries - 1:
                    wait_time = calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Timeout retry in %.2f seconds", wait_time)
                    time.sleep(wait_time)
                    continue
                else:
                    raise AlphaVantageTimeoutError(
                        f"Request timed out after {self.max_retries} attempts"
                    ) from e

            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    str(e),
                )

                if attempt < self.max_retries - 1:
                    wait_time = calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Retrying in %.2f seconds", wait_time)
                    time.sleep(wait_time)
                    continue

        # All attempts failed
        raise AlphaVantageRequestError(
            f"Request failed after {self.max_retries} attempts"
        ) from last_exception

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

        prepared_params = prepare_api_params(params, self.api_key)
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    "Making async API request (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    params.get("function", "unknown"),
                )

                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with self._aio_session.get(
                    self.base_url, params=prepared_params, timeout=timeout
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
                        if attempt < self.max_retries - 1:
                            wait_time = calculate_backoff_delay_with_jitter(attempt)
                            self.logger.info(
                                "Rate limit backoff: %.2f seconds", wait_time
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise AlphaVantageRateLimitError(
                                f"Rate limit exceeded after {self.max_retries} attempts (HTTP 429)"
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
                error_msg = extract_error_message(data)
                if error_msg:
                    self.logger.error("API error received: %s", error_msg)
                    raise AlphaVantageAPIError(f"API Error: {error_msg}")

                rate_limit_msg = extract_rate_limit_message(data)
                if rate_limit_msg:
                    self.logger.warning(
                        "Rate limit detected in response: %s", rate_limit_msg
                    )

                    if attempt < self.max_retries - 1:
                        wait_time = calculate_backoff_delay_with_jitter(attempt)
                        self.logger.info("Rate limit backoff: %.2f seconds", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise AlphaVantageRateLimitError(
                            f"Rate limit exceeded after {self.max_retries} attempts: {rate_limit_msg}"
                        )

                # Apply rate limiting and return data
                await asyncio.sleep(self.rate_limit_delay)
                self.logger.debug("Async API request successful")
                return data

            except asyncio.TimeoutError as e:
                last_exception = e
                self.logger.warning(
                    "Async request timeout (attempt %d/%d)",
                    attempt + 1,
                    self.max_retries,
                )

                if attempt < self.max_retries - 1:
                    wait_time = calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Timeout retry in %.2f seconds", wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise AlphaVantageTimeoutError(
                        f"Request timed out after {self.max_retries} attempts"
                    ) from e

            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning(
                    "Async request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    str(e),
                )

                if attempt < self.max_retries - 1:
                    wait_time = calculate_backoff_delay_with_jitter(attempt)
                    self.logger.info("Retrying in %.2f seconds", wait_time)
                    await asyncio.sleep(wait_time)
                    continue

        # All attempts failed
        raise AlphaVantageRequestError(
            f"Async request failed after {self.max_retries} attempts"
        ) from last_exception

    # ===== HIGH-LEVEL API METHODS =====

    def get_daily_stock_data(
        self, symbol: str, outputsize: OutputSize = OutputSize.COMPACT
    ) -> pd.DataFrame:
        """Get daily stock data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            outputsize: Output size (compact or full)

        Returns:
            DataFrame with daily stock data (Date, Open, High, Low, Close, Volume).

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": AlphaVantageFunction.TIME_SERIES_DAILY.value,
            "symbol": symbol,
            "outputsize": outputsize.value,
        }

        try:
            data = self.make_request(params)
            time_series_key = AlphaVantageResponseKey.TIME_SERIES_DAILY.value

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            # Convert to DataFrame using helper function
            return convert_time_series_to_dataframe(
                time_series, datetime_key="Date", additional_columns={"Symbol": symbol}
            )

        except Exception as e:
            self.logger.error(
                "Failed to get daily stock data for %s: %s", symbol, str(e)
            )
            raise

    def get_intraday_stock_data(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: OutputSize = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Get intraday stock data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval ('1min', '5min', '15min', '30min', '60min')
            outputsize: Output size (compact or full)

        Returns:
            DataFrame with intraday stock data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": AlphaVantageFunction.TIME_SERIES_INTRADAY.value,
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize.value,
        }

        try:
            data = self.make_request(params)
            time_series_key = f"Time Series ({interval})"

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            # Convert to DataFrame using helper function
            return convert_time_series_to_dataframe(
                time_series,
                datetime_key="DateTime",
                additional_columns={"Symbol": symbol, "Interval": interval},
            )

        except Exception as e:
            self.logger.error(
                "Failed to get intraday stock data for %s (%s): %s",
                symbol,
                interval,
                str(e),
            )
            raise

    def get_forex_daily(
        self,
        from_symbol: str,
        to_symbol: str,
        outputsize: OutputSize = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Get daily forex data.

        Args:
            from_symbol: From currency symbol (e.g., 'USD')
            to_symbol: To currency symbol (e.g., 'EUR')
            outputsize: Output size (compact or full)

        Returns:
            DataFrame with forex time series data.

        Raises:
            AlphaVantageAPIError: If the API request fails.
        """
        params = {
            "function": AlphaVantageFunction.FX_DAILY.value,
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": outputsize.value,
        }

        try:
            data = self.make_request(params)
            time_series_key = AlphaVantageResponseKey.TIME_SERIES_FX_DAILY.value

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            # Convert to DataFrame using specialized function
            return process_forex_time_series(time_series, from_symbol, to_symbol)

        except Exception as e:
            self.logger.error(
                "Failed to get forex data for %s/%s: %s", from_symbol, to_symbol, str(e)
            )
            raise

    def get_digital_currency_daily(
        self, symbol: str, market: str = "USD"
    ) -> pd.DataFrame:
        """Get daily digital currency data.

        Args:
            symbol: Digital currency symbol (e.g., 'BTC')
            market: Market currency (e.g., 'USD')

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

        try:
            data = self.make_request(params)
            time_series_key = f"Time Series (Digital Currency Daily)"

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            # Convert to DataFrame using specialized function
            return process_digital_currency_time_series(time_series, symbol, market)

        except Exception as e:
            self.logger.error(
                "Failed to get digital currency data for %s/%s: %s",
                symbol,
                market,
                str(e),
            )
            raise

    # ===== ASYNC METHODS =====

    async def get_daily_async(
        self, symbol: str, outputsize: OutputSize = OutputSize.COMPACT
    ) -> pd.DataFrame:
        """Async version of get_daily_stock_data."""
        params = {
            "function": AlphaVantageFunction.TIME_SERIES_DAILY.value,
            "symbol": symbol,
            "outputsize": outputsize.value,
        }

        try:
            data = await self.make_request_async(params)
            time_series_key = AlphaVantageResponseKey.TIME_SERIES_DAILY.value

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            return convert_time_series_to_dataframe(
                time_series, datetime_key="Date", additional_columns={"Symbol": symbol}
            )

        except Exception as e:
            self.logger.error(
                "Failed to get daily stock data for %s: %s", symbol, str(e)
            )
            raise

    async def get_intraday_async(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: OutputSize = OutputSize.COMPACT,
    ) -> pd.DataFrame:
        """Async version of get_intraday_stock_data."""
        params = {
            "function": AlphaVantageFunction.TIME_SERIES_INTRADAY.value,
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize.value,
        }

        try:
            data = await self.make_request_async(params)
            time_series_key = f"Time Series ({interval})"

            if time_series_key not in data:
                raise AlphaVantageDataError(
                    f"Expected key '{time_series_key}' not found in response"
                )

            time_series = data[time_series_key]

            return convert_time_series_to_dataframe(
                time_series,
                datetime_key="DateTime",
                additional_columns={"Symbol": symbol, "Interval": interval},
            )

        except Exception as e:
            self.logger.error(
                "Failed to get intraday stock data for %s (%s): %s",
                symbol,
                interval,
                str(e),
            )
            raise
