"""Constants for the ticker converter package."""

from enum import Enum


class AlphaVantageFunction(str, Enum):
    """Alpha Vantage API function names."""

    TIME_SERIES_DAILY = "TIME_SERIES_DAILY"
    TIME_SERIES_INTRADAY = "TIME_SERIES_INTRADAY"
    OVERVIEW = "OVERVIEW"
    CURRENCY_EXCHANGE_RATE = "CURRENCY_EXCHANGE_RATE"
    FX_DAILY = "FX_DAILY"
    DIGITAL_CURRENCY_DAILY = "DIGITAL_CURRENCY_DAILY"


class AlphaVantageResponseKey(str, Enum):
    """Alpha Vantage API response keys."""

    TIME_SERIES_DAILY = "Time Series (Daily)"
    TIME_SERIES_FX_DAILY = "Time Series FX (Daily)"
    TIME_SERIES_DIGITAL_CURRENCY_DAILY = "Time Series (Digital Currency Daily)"
    REALTIME_CURRENCY_EXCHANGE_RATE = "Realtime Currency Exchange Rate"
    ERROR_MESSAGE = "Error Message"
    NOTE = "Note"


class AlphaVantageValueKey(str, Enum):
    """Alpha Vantage API value keys within time series."""

    OPEN = "1. open"
    HIGH = "2. high"
    LOW = "3. low"
    CLOSE = "4. close"
    VOLUME = "5. volume"
    EXCHANGE_RATE = "5. Exchange Rate"
    LAST_REFRESHED = "6. Last Refreshed"


class DataFormat(str, Enum):
    """Data format constants."""

    JSON = "json"
    PARQUET = "parquet"


class TimeInterval(str, Enum):
    """Time interval constants."""

    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"
    THIRTY_MIN = "30min"
    SIXTY_MIN = "60min"


class OutputSize(str, Enum):
    """Output size constants."""

    COMPACT = "compact"
    FULL = "full"


# Default values
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_DELAY = 1.0
DEFAULT_DATA_SOURCE = "alpha_vantage"

# File naming patterns
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
