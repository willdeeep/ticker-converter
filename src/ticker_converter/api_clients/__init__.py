"""API clients for external data sources.

This package provides modular API clients with clean separation of concerns:
- client: Main AlphaVantageClient with core functionality
- exceptions: Comprehensive exception hierarchy
- data_processors: DataFrame conversion utilities
- utils: Helper functions for retry logic and data processing
- constants: API constants and enums
"""

from .client import AlphaVantageClient
from .constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    OutputSize,
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

__all__ = [
    # Main client
    "AlphaVantageClient",
    # Constants
    "AlphaVantageFunction",
    "AlphaVantageResponseKey",
    "AlphaVantageValueKey",
    "OutputSize",
    # Exceptions
    "AlphaVantageAPIError",
    "AlphaVantageAuthenticationError",
    "AlphaVantageConfigError",
    "AlphaVantageDataError",
    "AlphaVantageRateLimitError",
    "AlphaVantageRequestError",
    "AlphaVantageTimeoutError",
]
