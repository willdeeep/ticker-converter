"""Utility functions for Alpha Vantage API client.

This module contains helper functions for retry logic, backoff calculations,
and other utilities used by the API client.
"""

import random
from typing import Any


def calculate_backoff_delay(attempt: int, base_delay: int = 12) -> int:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-based).
        base_delay: Base delay in seconds.

    Returns:
        Delay in seconds.
    """
    delay = base_delay * (2**attempt)
    return min(int(delay), 300)  # Max 5 minutes


def calculate_backoff_delay_with_jitter(attempt: int, base_delay: int = 12) -> float:
    """Calculate exponential backoff delay with jitter.

    Jitter helps prevent thundering herd problems when multiple
    clients retry simultaneously.

    Args:
        attempt: Current attempt number (0-based).
        base_delay: Base delay in seconds.

    Returns:
        Delay in seconds with jitter.
    """
    base_delay_calc = base_delay * (2**attempt)
    max_delay = min(base_delay_calc, 300)  # Max 5 minutes

    # Add jitter: random factor between 0.5 and 1.5
    jitter = 0.5 + random.random()
    delay_with_jitter = max_delay * jitter

    return min(delay_with_jitter, 300.0)


def prepare_api_params(params: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Prepare API parameters by adding API key and copying dict.

    Args:
        params: Original parameters.
        api_key: Alpha Vantage API key.

    Returns:
        New dict with API key added.
    """
    prepared_params = params.copy()
    prepared_params["apikey"] = api_key
    return prepared_params


def validate_api_response_data(data: dict[str, Any]) -> None:
    """Validate API response data for common issues.

    Args:
        data: Response data from API.

    Raises:
        ValueError: If data appears invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("API response must be a dictionary")

    if not data:
        raise ValueError("API response is empty")


def extract_error_message(response_data: dict[str, Any]) -> str | None:
    """Extract error message from API response.

    Args:
        response_data: Response data from API.

    Returns:
        Error message if found, None otherwise.
    """
    # Common error message keys in Alpha Vantage responses
    error_keys = ["Error Message", "error", "message"]

    for key in error_keys:
        if key in response_data:
            return str(response_data[key])

    return None


def extract_rate_limit_message(response_data: dict[str, Any]) -> str | None:
    """Extract rate limit message from API response.

    Args:
        response_data: Response data from API.

    Returns:
        Rate limit message if found, None otherwise.
    """
    # Common rate limit keys in Alpha Vantage responses
    rate_limit_keys = ["Note", "note", "Information"]

    for key in rate_limit_keys:
        if key in response_data:
            message = str(response_data[key])
            # Check if this looks like a rate limit message
            if any(
                keyword in message.lower()
                for keyword in [
                    "rate limit",
                    "frequency",
                    "calls per",
                    "thank you for using",
                ]
            ):
                return message

    return None
