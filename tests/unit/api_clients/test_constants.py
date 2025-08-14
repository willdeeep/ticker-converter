"""Unit tests for Alpha Vantage API constants."""

import pytest

from src.ticker_converter.api_clients.constants import (
    AlphaVantageFunction,
    AlphaVantageResponseKey,
    AlphaVantageValueKey,
    OutputSize,
)


class TestConstants:
    """Test suite for Alpha Vantage API constants."""

    def test_output_size_enum(self) -> None:
        """Test OutputSize enumeration values."""
        assert OutputSize.COMPACT == "compact"
        assert OutputSize.FULL == "full"

        # Test string conversion
        assert str(OutputSize.COMPACT) == "compact"
        assert str(OutputSize.FULL) == "full"

    def test_output_size_comparison(self) -> None:
        """Test OutputSize comparison operations."""
        # Test equality
        assert OutputSize.COMPACT == "compact"
        assert OutputSize.FULL == "full"

        # Test inequality
        assert OutputSize.COMPACT != "full"
        assert OutputSize.FULL != "compact"

    def test_alpha_vantage_function_enum(self) -> None:
        """Test AlphaVantageFunction enumeration values."""
        assert AlphaVantageFunction.TIME_SERIES_DAILY == "TIME_SERIES_DAILY"
        assert AlphaVantageFunction.TIME_SERIES_INTRADAY == "TIME_SERIES_INTRADAY"
        assert AlphaVantageFunction.OVERVIEW == "OVERVIEW"
        assert AlphaVantageFunction.CURRENCY_EXCHANGE_RATE == "CURRENCY_EXCHANGE_RATE"
        assert AlphaVantageFunction.FX_DAILY == "FX_DAILY"
        assert AlphaVantageFunction.DIGITAL_CURRENCY_DAILY == "DIGITAL_CURRENCY_DAILY"

    def test_alpha_vantage_response_key_enum(self) -> None:
        """Test AlphaVantageResponseKey enumeration values."""
        assert AlphaVantageResponseKey.TIME_SERIES_DAILY == "Time Series (Daily)"
        assert AlphaVantageResponseKey.TIME_SERIES_FX_DAILY == "Time Series (FX Daily)"
        assert (
            AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE
            == "Realtime Currency Exchange Rate"
        )
        assert AlphaVantageResponseKey.ERROR_MESSAGE == "Error Message"
        assert AlphaVantageResponseKey.NOTE == "Note"

    def test_alpha_vantage_value_key_enum(self) -> None:
        """Test AlphaVantageValueKey enumeration values."""
        assert AlphaVantageValueKey.OPEN == "1. open"
        assert AlphaVantageValueKey.HIGH == "2. high"
        assert AlphaVantageValueKey.LOW == "3. low"
        assert AlphaVantageValueKey.CLOSE == "4. close"
        assert AlphaVantageValueKey.VOLUME == "5. volume"
        assert AlphaVantageValueKey.EXCHANGE_RATE == "5. Exchange Rate"
        assert AlphaVantageValueKey.LAST_REFRESHED == "6. Last Refreshed"

    def test_enum_membership(self) -> None:
        """Test membership checks for enums."""
        # Test OutputSize membership
        assert "compact" in [e.value for e in OutputSize]
        assert "full" in [e.value for e in OutputSize]
        assert "invalid" not in [e.value for e in OutputSize]

        # Test Function membership
        assert "TIME_SERIES_DAILY" in [e.value for e in AlphaVantageFunction]
        assert "OVERVIEW" in [e.value for e in AlphaVantageFunction]
        assert "invalid" not in [e.value for e in AlphaVantageFunction]

    def test_enum_iteration(self) -> None:
        """Test iteration over enum values."""
        # Test OutputSize iteration
        output_sizes = list(OutputSize)
        assert len(output_sizes) == 2
        assert OutputSize.COMPACT in output_sizes
        assert OutputSize.FULL in output_sizes

        # Test Function iteration
        functions = list(AlphaVantageFunction)
        assert len(functions) >= 6  # At least 6 functions defined
        assert AlphaVantageFunction.TIME_SERIES_DAILY in functions
        assert AlphaVantageFunction.OVERVIEW in functions

    def test_enum_case_sensitivity(self) -> None:
        """Test that enum values are case-sensitive."""
        # OutputSize should be lowercase
        assert OutputSize.COMPACT == "compact"
        assert OutputSize.COMPACT != "COMPACT"
        assert OutputSize.COMPACT != "Compact"

        # Functions should be uppercase
        assert AlphaVantageFunction.TIME_SERIES_DAILY == "TIME_SERIES_DAILY"
        assert AlphaVantageFunction.TIME_SERIES_DAILY != "time_series_daily"

    def test_value_key_numbering(self) -> None:
        """Test that value keys have correct Alpha Vantage numbering."""
        # Alpha Vantage uses specific numbering for OHLCV data
        assert AlphaVantageValueKey.OPEN.startswith("1.")
        assert AlphaVantageValueKey.HIGH.startswith("2.")
        assert AlphaVantageValueKey.LOW.startswith("3.")
        assert AlphaVantageValueKey.CLOSE.startswith("4.")
        assert AlphaVantageValueKey.VOLUME.startswith("5.")

    def test_enum_unique_values(self) -> None:
        """Test that enum values are unique."""
        # Test OutputSize uniqueness
        output_size_values = [e.value for e in OutputSize]
        assert len(output_size_values) == len(set(output_size_values))

        # Test Function uniqueness
        function_values = [e.value for e in AlphaVantageFunction]
        assert len(function_values) == len(set(function_values))

        # Test ResponseKey uniqueness
        response_key_values = [e.value for e in AlphaVantageResponseKey]
        assert len(response_key_values) == len(set(response_key_values))

    def test_enum_string_representation(self) -> None:
        """Test string representation of enum members."""
        # Test that str() returns the value
        assert str(OutputSize.COMPACT) == "compact"
        assert str(AlphaVantageFunction.TIME_SERIES_DAILY) == "TIME_SERIES_DAILY"
        assert str(AlphaVantageResponseKey.TIME_SERIES_DAILY) == "Time Series (Daily)"

        # Test that repr() shows the enum member
        assert "OutputSize.COMPACT" in repr(OutputSize.COMPACT)
        assert "AlphaVantageFunction.TIME_SERIES_DAILY" in repr(
            AlphaVantageFunction.TIME_SERIES_DAILY
        )

    def test_enum_attribute_access(self) -> None:
        """Test that enum members can be accessed as attributes."""
        # Test attribute access
        assert hasattr(OutputSize, "COMPACT")
        assert hasattr(OutputSize, "FULL")
        assert hasattr(AlphaVantageFunction, "TIME_SERIES_DAILY")
        assert hasattr(AlphaVantageFunction, "OVERVIEW")

        # Test that invalid attributes raise AttributeError
        with pytest.raises(AttributeError):
            _ = OutputSize.INVALID

        with pytest.raises(AttributeError):
            _ = AlphaVantageFunction.INVALID

    def test_enum_comparison_types(self) -> None:
        """Test comparison between enum members and different types."""
        # Enum members should equal their string values
        assert OutputSize.COMPACT == "compact"
        assert AlphaVantageFunction.TIME_SERIES_DAILY == "TIME_SERIES_DAILY"

        # Enum members should not equal other types
        assert OutputSize.COMPACT != 1
        assert OutputSize.COMPACT != ["compact"]
        assert OutputSize.COMPACT != {"value": "compact"}

        # Enum members should not equal None
        assert OutputSize.COMPACT is not None
        assert OutputSize.COMPACT != None

    def test_response_key_values(self) -> None:
        """Test specific response key values."""
        # Test that response keys match Alpha Vantage API documentation
        assert AlphaVantageResponseKey.TIME_SERIES_DAILY == "Time Series (Daily)"
        assert AlphaVantageResponseKey.ERROR_MESSAGE == "Error Message"
        assert (
            AlphaVantageResponseKey.REALTIME_CURRENCY_EXCHANGE_RATE
            == "Realtime Currency Exchange Rate"
        )

    def test_value_key_consistency(self) -> None:
        """Test that value keys are consistent with Alpha Vantage format."""
        # Test OHLCV keys follow Alpha Vantage pattern
        ohlcv_keys = [
            AlphaVantageValueKey.OPEN,
            AlphaVantageValueKey.HIGH,
            AlphaVantageValueKey.LOW,
            AlphaVantageValueKey.CLOSE,
            AlphaVantageValueKey.VOLUME,
        ]

        for i, key in enumerate(ohlcv_keys, 1):
            assert key.startswith(f"{i}.")
            assert " " in key  # Should have space after number
