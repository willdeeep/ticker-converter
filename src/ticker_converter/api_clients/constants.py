"""Constants for Alpha Vantage API client."""

import os


class AlphaVantageFunction:
    """Alpha Vantage API function names."""
    TIME_SERIES_DAILY = "TIME_SERIES_DAILY"
    TIME_SERIES_INTRADAY = "TIME_SERIES_INTRADAY"
    OVERVIEW = "OVERVIEW"
    CURRENCY_EXCHANGE_RATE = "CURRENCY_EXCHANGE_RATE"
    FX_DAILY = "FX_DAILY"
    DIGITAL_CURRENCY_DAILY = "DIGITAL_CURRENCY_DAILY"


class AlphaVantageResponseKey:
    """Alpha Vantage API response keys."""
    TIME_SERIES_DAILY = "Time Series (Daily)"
    ERROR_MESSAGE = "Error Message"
    NOTE = "Note"


class AlphaVantageValueKey:
    """Alpha Vantage time series value keys."""
    OPEN = "1. open"
    HIGH = "2. high"
    LOW = "3. low"
    CLOSE = "4. close"
    VOLUME = "5. volume"


class OutputSize:
    """Output size options for Alpha Vantage API."""
    COMPACT = "compact"
    FULL = "full"


class Config:
    """Configuration for Alpha Vantage API client."""
    
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 12  # Alpha Vantage free tier allows 5 requests per minute


# Global config instance
config = Config()
