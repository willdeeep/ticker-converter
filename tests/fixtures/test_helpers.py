"""Test helper utilities for common testing patterns.

This module provides utilities to reduce test code duplication and improve
test readability and maintainability.
"""

from typing import Any, Callable
from unittest.mock import Mock

import pytest


class TestDataBuilder:
    """Builder pattern for creating test data with fluent interface."""

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._data: dict[str, Any] = {}

    def with_symbol(self, symbol: str) -> "TestDataBuilder":
        """Set symbol for stock data."""
        self._data["symbol"] = symbol
        return self

    def with_date(self, date: str) -> "TestDataBuilder":
        """Set date for the data."""
        self._data["data_date"] = date
        return self

    def with_prices(self, open_price: float, high: float, low: float, close: float) -> "TestDataBuilder":
        """Set OHLC prices for stock data."""
        self._data.update(
            {
                "open_price": open_price,
                "high_price": high,
                "low_price": low,
                "close_price": close,
            }
        )
        return self

    def with_volume(self, volume: int) -> "TestDataBuilder":
        """Set volume for stock data."""
        self._data["volume"] = volume
        return self

    def with_exchange_rate(self, rate: float) -> "TestDataBuilder":
        """Set exchange rate for currency data."""
        self._data["exchange_rate"] = rate
        return self

    def with_currencies(self, from_currency: str, to_currency: str) -> "TestDataBuilder":
        """Set currency pair."""
        self._data.update(
            {
                "from_currency": from_currency,
                "to_currency": to_currency,
            }
        )
        return self

    def with_source(self, source: str = "alpha_vantage") -> "TestDataBuilder":
        """Set data source."""
        self._data["source"] = source
        return self

    def with_created_at(self, timestamp: str) -> "TestDataBuilder":
        """Set creation timestamp."""
        self._data["created_at"] = timestamp
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the test data dictionary."""
        return self._data.copy()

    def build_list(self, count: int) -> list[dict[str, Any]]:
        """Build a list of test data with sequential modifications."""
        return [self.build() for _ in range(count)]


def assert_mock_called_with_data(mock: Mock, expected_data: list[dict[str, Any]]) -> None:
    """Assert that a mock was called with specific data.

    Args:
        mock: The mock object to check
        expected_data: Expected data that should have been passed

    Raises:
        AssertionError: If the mock wasn't called with expected data
    """
    mock.assert_called_once()
    call_args = mock.call_args[0][0]  # First positional argument
    assert call_args == expected_data, f"Expected {expected_data}, got {call_args}"


def assert_result_structure(result: dict[str, Any], expected_keys: list[str]) -> None:
    """Assert that a result dictionary has the expected structure.

    Args:
        result: Result dictionary to check
        expected_keys: List of keys that should be present

    Raises:
        AssertionError: If any expected keys are missing
    """
    missing_keys = [key for key in expected_keys if key not in result]
    assert not missing_keys, f"Missing keys in result: {missing_keys}"


def assert_error_in_result(result: dict[str, Any], error_substring: str) -> None:
    """Assert that an error containing specific text is in the result.

    Args:
        result: Result dictionary to check
        error_substring: Substring that should appear in error messages

    Raises:
        AssertionError: If the error substring is not found
    """
    errors = result.get("errors", [])
    assert any(
        error_substring in str(error) for error in errors
    ), f"Error containing '{error_substring}' not found in: {errors}"


def create_mock_with_methods(method_configs: dict[str, Any]) -> Mock:
    """Create a mock with pre-configured method return values.

    Args:
        method_configs: Dictionary mapping method names to return values

    Returns:
        Mock: Configured mock object

    Example:
        mock = create_mock_with_methods({
            "get_data": [{"key": "value"}],
            "is_empty": True,
            "count": 42
        })
    """
    mock = Mock()
    for method_name, return_value in method_configs.items():
        setattr(mock, method_name, Mock(return_value=return_value))
    return mock


def expect_no_errors(result: dict[str, Any]) -> None:
    """Assert that a result contains no errors.

    Args:
        result: Result dictionary to check

    Raises:
        AssertionError: If errors are found in the result
    """
    errors = result.get("errors", [])
    assert not errors, f"Unexpected errors found: {errors}"


class MockResetManager:
    """Context manager for automatically resetting mocks after test execution."""

    def __init__(self, *mocks: Mock) -> None:
        """Initialize with mocks to manage.

        Args:
            *mocks: Variable number of Mock objects to reset
        """
        self.mocks = mocks

    def __enter__(self) -> None:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Reset all mocks on exit."""
        for mock in self.mocks:
            mock.reset_mock()


def parametrize_with_data(test_data: list[tuple[str, dict[str, Any]]]) -> Callable:
    """Decorator for parametrized tests with named test cases.

    Args:
        test_data: List of tuples containing (test_name, test_parameters)

    Returns:
        Configured pytest.mark.parametrize decorator

    Example:
        @parametrize_with_data([
            ("success_case", {"input": "valid", "expected": True}),
            ("failure_case", {"input": "invalid", "expected": False}),
        ])
        def test_something(test_name, test_params):
            # Test implementation using test_params
    """
    test_names = [name for name, _ in test_data]
    test_params = [params for _, params in test_data]

    return pytest.mark.parametrize("test_name,test_params", list(zip(test_names, test_params)), ids=test_names)


def create_standard_result_dict() -> dict[str, Any]:
    """Create a standard result dictionary structure for tests.

    Returns:
        dict: Standard result structure with common fields
    """
    return {
        "operation": "test_operation",
        "success": False,
        "total_records_inserted": 0,
        "errors": [],
        "start_time": "2025-08-17T10:00:00Z",
        "end_time": "2025-08-17T10:00:01Z",
        "duration_seconds": 1.0,
    }


def mock_datetime_now(mock_datetime: Mock, fixed_time: str) -> None:
    """Configure datetime mock for consistent test timing.

    Args:
        mock_datetime: Mocked datetime module
        fixed_time: Fixed time string to return for now() calls
    """
    from datetime import datetime

    fixed_datetime = datetime.fromisoformat(fixed_time.replace("Z", "+00:00"))
    mock_datetime.now.return_value = fixed_datetime
    mock_datetime.now().isoformat.return_value = fixed_time


def verify_mock_call_sequence(mock: Mock, expected_sequence: list[str]) -> None:
    """Verify that mock methods were called in the expected sequence.

    Args:
        mock: Mock object to check
        expected_sequence: List of method names in expected call order

    Raises:
        AssertionError: If call sequence doesn't match expected
    """
    actual_calls = [call[0] for call in mock.method_calls]
    assert actual_calls == expected_sequence, f"Expected call sequence {expected_sequence}, got {actual_calls}"
