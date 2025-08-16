"""Alpha Vantage API client exceptions.

This module defines a comprehensive exception hierarchy for the Alpha Vantage API client,
providing granular error handling for different types of failures.
"""


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
    """Exception for HTTP request errors."""


class AlphaVantageConfigError(AlphaVantageAPIError):
    """Exception for configuration errors."""


class AlphaVantageAuthenticationError(AlphaVantageAPIError):
    """Exception for authentication/authorization errors."""


class AlphaVantageTimeoutError(AlphaVantageAPIError):
    """Exception for request timeout errors."""


class AlphaVantageDataError(AlphaVantageAPIError):
    """Exception for data parsing/validation errors."""
