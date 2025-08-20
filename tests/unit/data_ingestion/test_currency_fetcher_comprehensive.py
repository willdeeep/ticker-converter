"""Comprehensive tests for CurrencyDataFetcher module.

This module provides comprehensive testing for currency data fetching functionality,
covering current exchange rates, historical data, SQL preparation, and error scenarios.
"""

from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd

from src.ticker_converter.api_clients.exceptions import AlphaVantageAPIError
from src.ticker_converter.data_ingestion.currency_fetcher import CurrencyDataFetcher


class TestCurrencyDataFetcherInitialization:
    """Test CurrencyDataFetcher initialization and configuration."""

    def test_initialization_default(self) -> None:
        """Test fetcher initialization with default settings."""
        fetcher = CurrencyDataFetcher()

        assert fetcher.api_client is not None
        assert fetcher.FROM_CURRENCY == "USD"
        assert fetcher.TO_CURRENCY == "GBP"
        assert fetcher.REQUIRED_COLUMNS == ["Date"]

    def test_class_constants(self) -> None:
        """Test class-level constants are properly defined."""
        assert CurrencyDataFetcher.FROM_CURRENCY == "USD"
        assert CurrencyDataFetcher.TO_CURRENCY == "GBP"
        assert CurrencyDataFetcher.REQUIRED_COLUMNS == ["Date"]

    @patch("src.ticker_converter.data_ingestion.base_fetcher.AlphaVantageClient")
    def test_initialization_with_custom_api_client(self, mock_client_class: Mock) -> None:
        """Test initialization with custom API client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        CurrencyDataFetcher()

        # The fetcher will create its own client via BaseDataFetcher
        mock_client_class.assert_called_once()


class TestCurrencyDataFetcherCurrentExchangeRate:
    """Test current exchange rate fetching functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fetcher = CurrencyDataFetcher()
        self.mock_api_client = Mock()
        self.fetcher.api_client = self.mock_api_client

    def test_fetch_current_exchange_rate_success(self) -> None:
        """Test successful current exchange rate fetching."""
        mock_response: dict[str, Any] = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "3. To_Currency Code": "GBP",
                "5. Exchange Rate": "0.7865",
                "6. Last Refreshed": "2025-08-17 10:30:00",
                "7. Time Zone": "UTC",
                "8. Bid Price": "0.7863",
                "9. Ask Price": "0.7867",
            }
        }

        self.mock_api_client.get_currency_exchange_rate.return_value = mock_response

        result = self.fetcher.fetch_current_exchange_rate()

        assert result is not None
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "GBP"
        assert result["exchange_rate"] == 0.7865
        assert result["last_refreshed"] == "2025-08-17 10:30:00"
        assert result["timezone"] == "UTC"
        assert result["bid_price"] == 0.7863
        assert result["ask_price"] == 0.7867

        self.mock_api_client.get_currency_exchange_rate.assert_called_once_with("USD", "GBP")

    def test_fetch_current_exchange_rate_missing_data(self) -> None:
        """Test handling of response with missing exchange rate data."""
        mock_response: dict[str, Any] = {"Some Other Data": {}}

        self.mock_api_client.get_currency_exchange_rate.return_value = mock_response

        result = self.fetcher.fetch_current_exchange_rate()

        assert result is None

    def test_fetch_current_exchange_rate_empty_response(self) -> None:
        """Test handling of empty response."""
        mock_response: dict[str, Any] = {}

        self.mock_api_client.get_currency_exchange_rate.return_value = mock_response

        result = self.fetcher.fetch_current_exchange_rate()

        assert result is None

    def test_fetch_current_exchange_rate_partial_data(self) -> None:
        """Test handling of response with partial data."""
        mock_response = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "5. Exchange Rate": "0.7865",
                # Missing some fields
            }
        }

        self.mock_api_client.get_currency_exchange_rate.return_value = mock_response

        result = self.fetcher.fetch_current_exchange_rate()

        assert result is not None
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "GBP"  # Default value
        assert result["exchange_rate"] == 0.7865
        assert result["last_refreshed"] == ""  # Default value
        assert result["timezone"] == "UTC"  # Default value

    def test_fetch_current_exchange_rate_api_error(self) -> None:
        """Test handling of AlphaVantage API errors."""
        self.mock_api_client.get_currency_exchange_rate.side_effect = AlphaVantageAPIError("API limit exceeded")

        with patch.object(self.fetcher, "_handle_api_error") as mock_handle_api_error:
            result = self.fetcher.fetch_current_exchange_rate()

            assert result is None
            mock_handle_api_error.assert_called_once()

    def test_fetch_current_exchange_rate_data_error(self) -> None:
        """Test handling of data processing errors."""
        mock_response = {
            "Realtime Currency Exchange Rate": {
                "5. Exchange Rate": "invalid_number",  # This will cause _safe_float_conversion to return 0.0
            }
        }

        self.mock_api_client.get_currency_exchange_rate.return_value = mock_response

        result = self.fetcher.fetch_current_exchange_rate()

        # The result should NOT be None because _safe_float_conversion returns 0.0, not None
        assert result is not None
        assert result["exchange_rate"] == 0.0  # safe conversion returns 0.0


class TestCurrencyDataFetcherDailyFxData:
    """Test daily FX data fetching functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fetcher = CurrencyDataFetcher()
        self.mock_api_client = Mock()
        self.fetcher.api_client = self.mock_api_client

    def test_fetch_daily_fx_data_success(self) -> None:
        """Test successful daily FX data fetching."""
        # Create a mock DataFrame that mimics the real API client behavior
        mock_df = Mock(spec=pd.DataFrame)
        mock_df.empty = False
        mock_df.tail.return_value = mock_df  # Return self when tail() is called
        mock_df.__len__ = Mock(return_value=5)  # Add len() support

        self.mock_api_client.get_forex_daily.return_value = mock_df

        result = self.fetcher.fetch_daily_fx_data(days_back=5)

        assert result == mock_df
        self.mock_api_client.get_forex_daily.assert_called_once_with("USD", "GBP", "compact")

    def test_fetch_daily_fx_data_no_time_series(self) -> None:
        """Test handling of empty DataFrame result."""
        mock_df = Mock(spec=pd.DataFrame)
        mock_df.empty = True

        self.mock_api_client.get_forex_daily.return_value = mock_df

        result = self.fetcher.fetch_daily_fx_data()

        assert result is None

    def test_fetch_daily_fx_data_empty_dataframe(self) -> None:
        """Test handling of empty DataFrame result."""
        mock_response = {"Time Series FX (Daily)": {"2025-08-17": {"1. open": "0.7850", "4. close": "0.7865"}}}

        self.mock_api_client.get_fx_daily.return_value = mock_response

        with patch("pandas.DataFrame.from_dict") as mock_from_dict:
            mock_df = Mock(spec=pd.DataFrame)
            mock_df.empty = True
            mock_from_dict.return_value = mock_df

            result = self.fetcher.fetch_daily_fx_data()

            assert result is None

    def test_fetch_daily_fx_data_large_dataset(self) -> None:
        """Test fetching large dataset with full output size."""
        mock_df = Mock(spec=pd.DataFrame)
        mock_df.empty = False
        mock_df.tail.return_value = mock_df
        mock_df.__len__ = Mock(return_value=200)  # Add len() support

        self.mock_api_client.get_forex_daily.return_value = mock_df

        result = self.fetcher.fetch_daily_fx_data(days_back=200)  # Should trigger "full" output size

        assert result == mock_df
        self.mock_api_client.get_forex_daily.assert_called_once_with("USD", "GBP", "full")

    def test_fetch_daily_fx_data_api_error(self) -> None:
        """Test handling of API errors during daily data fetch."""
        self.mock_api_client.get_forex_daily.side_effect = AlphaVantageAPIError("API error")

        result = self.fetcher.fetch_daily_fx_data()

        assert result is None

    def test_fetch_daily_fx_data_data_error(self) -> None:
        """Test handling of data processing errors."""
        self.mock_api_client.get_forex_daily.side_effect = ValueError("Data processing error")

        result = self.fetcher.fetch_daily_fx_data()

        assert result is None


class TestCurrencyDataFetcherSqlPreparation:
    """Test SQL data preparation functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fetcher = CurrencyDataFetcher()

    def test_prepare_for_sql_insert_success(self) -> None:
        """Test successful SQL preparation from DataFrame."""
        # Create DataFrame with Date column (not as index)
        data = {"Date": ["2025-08-17", "2025-08-16"], "4. close": [0.7865, 0.7850]}
        df = pd.DataFrame(data)

        result = self.fetcher.prepare_for_sql_insert(df)

        assert len(result) == 2
        assert result[0]["data_date"].strftime("%Y-%m-%d") == "2025-08-17"  # data_date is a date object
        assert result[0]["from_currency"] == "USD"
        assert result[0]["to_currency"] == "GBP"
        assert result[0]["exchange_rate"] == 0.7865
        assert result[1]["data_date"].strftime("%Y-%m-%d") == "2025-08-16"
        assert result[1]["exchange_rate"] == 0.7850

    def test_prepare_for_sql_insert_missing_close_column(self) -> None:
        """Test SQL preparation with missing close column."""
        data = {
            "Date": ["2025-08-17"],
            "1. open": [0.7850],
            "2. high": [0.7890],
            "3. low": [0.7840],
            # Missing "4. close"
        }
        df = pd.DataFrame(data)
        df.set_index("Date", inplace=True)

        with patch.object(self.fetcher, "_extract_exchange_rate", return_value=None):
            result = self.fetcher.prepare_for_sql_insert(df)

            # Should skip rows with None exchange rate
            assert len(result) == 0

    def test_prepare_for_sql_insert_empty_dataframe(self) -> None:
        """Test SQL preparation with empty DataFrame."""
        df = pd.DataFrame()

        result = self.fetcher.prepare_for_sql_insert(df)

        assert not result

    def test_extract_exchange_rate_success(self) -> None:
        """Test successful exchange rate extraction."""
        columns = pd.Index(["1. open", "2. high", "3. low", "4. close"])
        row = pd.Series([0.7850, 0.7890, 0.7840, 0.7865], index=columns)

        result = self.fetcher._extract_exchange_rate(row, columns)

        assert result == 0.7865

    def test_extract_exchange_rate_missing_close(self) -> None:
        """Test exchange rate extraction with missing close column."""
        columns = pd.Index(["1. open", "2. high", "3. low"])
        row = pd.Series([0.7850, 0.7890, 0.7840], index=columns)

        result = self.fetcher._extract_exchange_rate(row, columns)

        # Should fall back to first numeric column (1. open = 0.7850)
        assert result == 0.7850

    def test_extract_exchange_rate_invalid_value(self) -> None:
        """Test exchange rate extraction with invalid value."""
        columns = pd.Index(["4. close"])
        row = pd.Series(["invalid"], index=columns)

        with patch.object(self.fetcher, "_safe_float_conversion", return_value=None):
            result = self.fetcher._extract_exchange_rate(row, columns)

            assert result is None

    def test_prepare_current_rate_for_sql_success(self) -> None:
        """Test SQL preparation for current rate data."""
        current_rate_data = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "exchange_rate": 0.7865,
            "last_refreshed": "2025-08-17 10:30:00",
            "timezone": "UTC",
        }

        result = self.fetcher.prepare_current_rate_for_sql(current_rate_data)

        assert result is not None
        assert result["data_date"].strftime("%Y-%m-%d") == "2025-08-17"  # data_date, not date
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "GBP"
        assert result["exchange_rate"] == 0.7865

    def test_prepare_current_rate_for_sql_missing_data(self) -> None:
        """Test SQL preparation with missing current rate data."""
        result = self.fetcher.prepare_current_rate_for_sql(None)  # type: ignore[arg-type]

        assert result is None

    def test_prepare_current_rate_for_sql_invalid_date(self) -> None:
        """Test SQL preparation with invalid date format."""
        current_rate_data = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "exchange_rate": 0.7865,
            "last_refreshed": "invalid-date-format",
            "timezone": "UTC",
        }

        # Invalid date format should fall back to datetime.now().date()
        result = self.fetcher.prepare_current_rate_for_sql(current_rate_data)

        assert result is not None
        assert result["exchange_rate"] == 0.7865
        # Should fall back to current date when parsing fails
        assert result["data_date"] is not None


class TestCurrencyDataFetcherIntegration:
    """Test integrated functionality and end-to-end scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fetcher = CurrencyDataFetcher()
        self.mock_api_client = Mock()
        self.fetcher.api_client = self.mock_api_client

    def test_fetch_and_prepare_fx_data_success(self) -> None:
        """Test complete fetch and prepare workflow."""
        # Create a real DataFrame that would come from the API
        mock_df = pd.DataFrame({"Date": ["2025-08-17"], "4. close": [0.7865]})

        with patch.object(self.fetcher, "fetch_daily_fx_data", return_value=mock_df):
            result = self.fetcher.fetch_and_prepare_fx_data(days_back=5)

            assert len(result) == 1
            assert result[0]["data_date"].strftime("%Y-%m-%d") == "2025-08-17"
            assert result[0]["exchange_rate"] == 0.7865

    def test_fetch_and_prepare_fx_data_fetch_failure(self) -> None:
        """Test fetch and prepare with fetch failure."""
        self.mock_api_client.get_fx_daily.side_effect = AlphaVantageAPIError("API error")

        with patch.object(self.fetcher, "_handle_api_error"):
            result = self.fetcher.fetch_and_prepare_fx_data()

            assert not result

    def test_fetch_and_prepare_fx_data_no_data(self) -> None:
        """Test fetch and prepare with no data returned."""
        mock_response: dict[str, Any] = {"Some Other Data": {}}

        self.mock_api_client.get_fx_daily.return_value = mock_response

        result = self.fetcher.fetch_and_prepare_fx_data()

        assert not result

    def test_get_latest_available_rate_success(self) -> None:
        """Test getting latest available exchange rate."""
        mock_current_data = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "exchange_rate": 0.7865,
            "last_refreshed": "2025-08-17 10:30:00",
            "timezone": "UTC",
        }

        with patch.object(self.fetcher, "fetch_current_exchange_rate", return_value=mock_current_data):
            result = self.fetcher.get_latest_available_rate()

            assert result is not None
            date, rate = result
            assert isinstance(date, datetime)
            assert rate == 0.7865

    def test_get_latest_available_rate_failure(self) -> None:
        """Test getting latest rate when fetch fails."""
        with patch.object(self.fetcher, "fetch_current_exchange_rate", return_value=None):
            result = self.fetcher.get_latest_available_rate()

            assert result is None

    def test_get_latest_available_rate_invalid_date(self) -> None:
        """Test getting latest rate with invalid date format."""
        mock_current_data = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "exchange_rate": 0.7865,
            "last_refreshed": "invalid-date",
            "timezone": "UTC",
        }

        with patch.object(self.fetcher, "fetch_current_exchange_rate", return_value=mock_current_data):
            result = self.fetcher.get_latest_available_rate()

            # Should not be None - invalid date should fall back to current time
            assert result is not None
            date, rate = result
            assert isinstance(date, datetime)
            assert rate == 0.7865


class TestCurrencyDataFetcherErrorHandling:
    """Test comprehensive error handling scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fetcher = CurrencyDataFetcher()
        self.mock_api_client = Mock()
        self.fetcher.api_client = self.mock_api_client

    def test_comprehensive_error_scenarios(self) -> None:
        """Test various error scenarios across all methods."""
        # Test TimeoutError - this is caught by the (ValueError, KeyError, TypeError) clause
        self.mock_api_client.get_currency_exchange_rate.side_effect = ValueError("Network timeout simulation")

        result = self.fetcher.fetch_current_exchange_rate()
        assert result is None

    def test_malformed_api_response(self) -> None:
        """Test handling of malformed API responses."""
        # Test with completely malformed response - should handle gracefully
        malformed_responses = [
            {"wrong": "structure"},
            {"Realtime Currency Exchange Rate": None},
            {"Realtime Currency Exchange Rate": {}},  # Empty dict instead of "not a dict"
        ]

        for malformed_response in malformed_responses:
            self.mock_api_client.get_currency_exchange_rate.return_value = malformed_response
            result = self.fetcher.fetch_current_exchange_rate()
            assert result is None

        # Test None response specifically - this would cause AttributeError
        self.mock_api_client.get_currency_exchange_rate.return_value = None
        result = self.fetcher.fetch_current_exchange_rate()
        assert result is None

    def test_safe_float_conversion_edge_cases(self) -> None:
        """Test safe float conversion with various edge cases."""
        # Test the _safe_float_conversion method indirectly through exchange rate extraction
        test_values = [
            ("0.7865", 0.7865),  # Normal string number
            ("", 0.0),  # Empty string -> 0.0
            ("invalid", 0.0),  # Invalid string -> 0.0
            (0.7865, 0.7865),  # Already float
        ]

        for test_input, expected in test_values:
            columns = pd.Index(["4. close"])
            row = pd.Series([test_input], index=columns)

            result = self.fetcher._extract_exchange_rate(row, columns)

            assert result == expected


class TestCurrencyDataFetcherConfiguration:
    """Test configuration and constants validation."""

    def test_currency_pair_constants(self) -> None:
        """Test that currency pair constants are correctly configured."""
        fetcher = CurrencyDataFetcher()

        assert fetcher.FROM_CURRENCY == "USD"
        assert fetcher.TO_CURRENCY == "GBP"
        assert "Date" in fetcher.REQUIRED_COLUMNS

    def test_inheritance_from_base_fetcher(self) -> None:
        """Test that CurrencyDataFetcher properly inherits from BaseDataFetcher."""
        from src.ticker_converter.data_ingestion.base_fetcher import BaseDataFetcher

        fetcher = CurrencyDataFetcher()
        assert isinstance(fetcher, BaseDataFetcher)

        # Test that inherited methods are available
        assert hasattr(fetcher, "logger")
        assert hasattr(fetcher, "_handle_api_error")
        assert hasattr(fetcher, "_handle_data_error")
        assert hasattr(fetcher, "_safe_float_conversion")

    def test_required_columns_validation(self) -> None:
        """Test that required columns are properly validated."""
        fetcher = CurrencyDataFetcher()

        # Test DataFrame with required columns (Date column not as index)
        valid_df = pd.DataFrame({"Date": ["2025-08-17"], "4. close": [0.7865]})

        result = fetcher.prepare_for_sql_insert(valid_df)
        assert len(result) == 1

        # Test DataFrame without required columns
        invalid_df = pd.DataFrame({"SomeColumn": ["value"]})

        result = fetcher.prepare_for_sql_insert(invalid_df)
        assert not result
