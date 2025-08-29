"""Constants and configuration for Alpha Vantage API client."""

import os
from dataclasses import dataclass
from enum import Enum


class AlphaVantageFunction(str, Enum):
    """Alpha Vantage API function names."""

    TIME_SERIES_DAILY = "TIME_SERIES_DAILY"
    TIME_SERIES_INTRADAY = "TIME_SERIES_INTRADAY"
    OVERVIEW = "OVERVIEW"
    CURRENCY_EXCHANGE_RATE = "CURRENCY_EXCHANGE_RATE"
    FX_DAILY = "FX_DAILY"
    DIGITAL_CURRENCY_DAILY = "DIGITAL_CURRENCY_DAILY"

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class AlphaVantageResponseKey(str, Enum):
    """Alpha Vantage API response keys."""

    TIME_SERIES_DAILY = "Time Series (Daily)"
    TIME_SERIES_FX_DAILY = "Time Series FX (Daily)"
    REALTIME_CURRENCY_EXCHANGE_RATE = "Realtime Currency Exchange Rate"
    ERROR_MESSAGE = "Error Message"
    NOTE = "Note"

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class AlphaVantageValueKey(str, Enum):
    """Alpha Vantage time series value keys."""

    OPEN = "1. open"
    HIGH = "2. high"
    LOW = "3. low"
    CLOSE = "4. close"
    VOLUME = "5. volume"
    EXCHANGE_RATE = "5. Exchange Rate"
    LAST_REFRESHED = "6. Last Refreshed"

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class OutputSize(str, Enum):
    """Output size options for Alpha Vantage API."""

    COMPACT = "compact"
    FULL = "full"

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


@dataclass(frozen=True)
class APIConfig:
    """Configuration for Alpha Vantage API client."""

    api_key: str
    base_url: str
    timeout: int
    max_retries: int
    rate_limit_delay: int


def get_api_config() -> APIConfig:
    """Get API configuration from environment variables.

    Returns:
        APIConfig instance with environment-based configuration

    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is required")

    return APIConfig(
        api_key=api_key,
        base_url="https://www.alphavantage.co/query",
        timeout=30,
        max_retries=3,
        rate_limit_delay=12,  # Alpha Vantage free tier allows 5 requests per minute
    )


# Default configuration instance
try:
    config = get_api_config()
except ValueError:
    # Use demo config for testing when API key is not available
    config = APIConfig(
        api_key="demo",
        base_url="https://www.alphavantage.co/query",
        timeout=30,
        max_retries=3,
        rate_limit_delay=12,
    )
