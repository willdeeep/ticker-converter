"""Unit tests for NYSE data fetcher."""

from datetime import date
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.ticker_converter.api_clients.constants import OutputSize
from src.ticker_converter.api_clients.exceptions import AlphaVantageAPIError
from src.ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher


class TestNYSEDataFetcher:
    """Test suite for NYSEDataFetcher."""

    def test_initialization_default(self) -> None:
        """Test fetcher initialization with default settings."""
        fetcher = NYSEDataFetcher()

        assert fetcher.api_client is not None
        assert fetcher.MAGNIFICENT_SEVEN == [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]

    def test_initialization_with_custom_client(self) -> None:
        """Test fetcher initialization with custom API client."""
        mock_client = Mock()
        fetcher = NYSEDataFetcher(api_client=mock_client)

        assert fetcher.api_client is mock_client

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.fetch_daily_data"
    )
    def test_fetch_magnificent_seven_data_success(self, mock_fetch_daily: Mock) -> None:
        """Test successful magnificent seven data fetching."""
        # Setup mock data for each symbol
        mock_data = pd.DataFrame(
            {
                "Date": pd.date_range("2025-08-13", periods=2),
                "Open": [220.0, 218.0],
                "High": [225.0, 223.0],
                "Low": [219.0, 217.0],
                "Close": [224.5, 221.5],
                "Volume": [1000000, 900000],
            }
        )

        mock_fetch_daily.return_value = mock_data

        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_magnificent_seven_data(days_back=10)

        # Should be called once for each magnificent seven symbol
        assert mock_fetch_daily.call_count == 7

        # Check that result is a dictionary with symbol data
        assert isinstance(result, dict)
        assert len(result) == 7

        for symbol in fetcher.MAGNIFICENT_SEVEN:
            assert symbol in result
            assert isinstance(result[symbol], pd.DataFrame)

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.fetch_daily_data"
    )
    def test_fetch_magnificent_seven_data_with_failures(
        self, mock_fetch_daily: Mock
    ) -> None:
        """Test magnificent seven data fetching with some failures."""

        # Setup mock to return None for one symbol and succeed for others
        def side_effect(symbol: str, *args: Any, **kwargs: Any) -> pd.DataFrame | None:
            if symbol == "AAPL":
                return None  # Simulate API failure
            return pd.DataFrame(
                {
                    "Date": pd.date_range("2025-08-14", periods=1),
                    "Open": [220.0],
                    "High": [225.0],
                    "Low": [219.0],
                    "Close": [224.5],
                    "Volume": [1000000],
                }
            )

        mock_fetch_daily.side_effect = side_effect

        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_magnificent_seven_data(days_back=10)

        # Should still return data for successful symbols
        assert isinstance(result, dict)
        assert len(result) == 6  # 7 symbols - 1 failed
        assert "AAPL" not in result
        assert "MSFT" in result

    @patch("src.ticker_converter.data_ingestion.base_fetcher.AlphaVantageClient")
    def test_fetch_daily_data_success(self, mock_client_class: Mock) -> None:
        """Test successful daily data fetching for a symbol."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Setup mock DataFrame response with proper column names
        mock_df = pd.DataFrame(
            {
                "Date": pd.date_range("2025-08-13", periods=2),
                "Open": [220.0, 218.0],
                "High": [225.0, 223.0],
                "Low": [219.0, 217.0],
                "Close": [224.5, 221.5],
                "Volume": [1000000, 900000],
            }
        )

        mock_client.get_daily_stock_data.return_value = mock_df

        fetcher = NYSEDataFetcher(api_client=mock_client)
        result = fetcher.fetch_daily_data("AAPL", days_back=10)

        # Verify API client was called correctly
        mock_client.get_daily_stock_data.assert_called_once_with(
            "AAPL", OutputSize.COMPACT
        )

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "Date" in result.columns
        assert "Open" in result.columns

    @patch("src.ticker_converter.api_clients.client.AlphaVantageClient")
    def test_fetch_daily_data_api_error(self, mock_client_class: Mock) -> None:
        """Test daily data fetching with API error."""
        # Setup mock client to raise error
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_daily_stock_data.side_effect = AlphaVantageAPIError("API Error")

        fetcher = NYSEDataFetcher(api_client=mock_client)
        result = fetcher.fetch_daily_data("AAPL", days_back=10)

        # Should return None on error
        assert result is None

    @patch("src.ticker_converter.api_clients.client.AlphaVantageClient")
    def test_fetch_daily_data_invalid_dataframe(self, mock_client_class: Mock) -> None:
        """Test daily data fetching with invalid DataFrame response."""
        # Setup mock client to return DataFrame missing required columns
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_daily_stock_data.return_value = pd.DataFrame(
            {"invalid": [1, 2, 3]}
        )

        fetcher = NYSEDataFetcher(api_client=mock_client)
        result = fetcher.fetch_daily_data("AAPL", days_back=10)

        # Should return None when validation fails
        assert result is None

    def test_prepare_for_sql_insert_success(self) -> None:
        """Test successful data preparation for SQL insertion."""
        fetcher = NYSEDataFetcher()

        # Create valid DataFrame
        df = pd.DataFrame(
            {
                "Date": ["2025-08-13", "2025-08-14"],
                "Open": [220.0, 218.0],
                "High": [225.0, 223.0],
                "Low": [219.0, 217.0],
                "Close": [224.5, 221.5],
                "Volume": [1000000, 900000],
            }
        )

        result = fetcher.prepare_for_sql_insert(df, "AAPL")

        assert isinstance(result, list)
        assert len(result) == 2

        # Check first record structure
        record = result[0]
        assert record["symbol"] == "AAPL"
        assert "data_date" in record
        assert "open_price" in record
        assert "high_price" in record
        assert "low_price" in record
        assert "close_price" in record
        assert "volume" in record

    def test_prepare_for_sql_insert_no_symbol(self) -> None:
        """Test data preparation with missing symbol argument."""
        fetcher = NYSEDataFetcher()
        df = pd.DataFrame({"Date": ["2025-08-13"], "Open": [220.0]})

        with pytest.raises(ValueError, match="Symbol must be provided"):
            fetcher.prepare_for_sql_insert(df)

    def test_prepare_for_sql_insert_invalid_dataframe(self) -> None:
        """Test data preparation with invalid DataFrame."""
        fetcher = NYSEDataFetcher()
        df = pd.DataFrame({"invalid": [1, 2, 3]})

        result = fetcher.prepare_for_sql_insert(df, "AAPL")
        assert not result

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.fetch_magnificent_seven_data"
    )
    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.prepare_for_sql_insert"
    )
    def test_fetch_and_prepare_all_data(
        self, mock_prepare: Mock, mock_fetch_m7: Mock
    ) -> None:
        """Test fetching and preparing all magnificent seven data."""
        # Setup mock data
        mock_df = pd.DataFrame(
            {
                "Date": ["2025-08-13"],
                "Open": [220.0],
                "High": [225.0],
                "Low": [219.0],
                "Close": [224.5],
                "Volume": [1000000],
            }
        )

        mock_fetch_m7.return_value = {"AAPL": mock_df, "MSFT": mock_df}
        mock_prepare.return_value = [{"symbol": "AAPL", "data_date": "2025-08-13"}]

        fetcher = NYSEDataFetcher()
        result = fetcher.fetch_and_prepare_all_data(days_back=10)

        # Verify methods were called
        mock_fetch_m7.assert_called_once_with(10)
        assert mock_prepare.call_count == 2  # Called for each symbol

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2  # 2 symbols * 1 record each

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.fetch_daily_data"
    )
    def test_get_latest_available_date_success(self, mock_fetch_daily: Mock) -> None:
        """Test getting latest available date for a symbol."""
        mock_df = pd.DataFrame(
            {
                "Date": ["2025-08-14"],
                "Open": [220.0],
                "High": [225.0],
                "Low": [219.0],
                "Close": [224.5],
                "Volume": [1000000],
            }
        )

        mock_fetch_daily.return_value = mock_df

        fetcher = NYSEDataFetcher()
        result = fetcher.get_latest_available_date("AAPL")

        mock_fetch_daily.assert_called_once_with("AAPL", days_back=1)
        assert isinstance(result, date)

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.fetch_daily_data"
    )
    def test_get_latest_available_date_no_data(self, mock_fetch_daily: Mock) -> None:
        """Test getting latest available date when no data is available."""
        mock_fetch_daily.return_value = None

        fetcher = NYSEDataFetcher()
        result = fetcher.get_latest_available_date("AAPL")

        assert result is None

    @patch(
        "src.ticker_converter.data_ingestion.nyse_fetcher.NYSEDataFetcher.get_latest_available_date"
    )
    def test_check_data_freshness(self, mock_get_latest: Mock) -> None:
        """Test checking data freshness for all magnificent seven stocks."""
        mock_get_latest.side_effect = lambda symbol: (
            date(2025, 8, 14) if symbol in ["AAPL", "MSFT"] else None
        )

        fetcher = NYSEDataFetcher()
        result = fetcher.check_data_freshness()

        # Should be called for each magnificent seven symbol
        assert mock_get_latest.call_count == 7

        # Should only return data for symbols that had data
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "AAPL" in result
        assert "MSFT" in result
        assert result["AAPL"] == date(2025, 8, 14)

    def test_magnificent_seven_constant(self) -> None:
        """Test that MAGNIFICENT_SEVEN constant contains expected symbols."""
        fetcher = NYSEDataFetcher()

        expected_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
        assert fetcher.MAGNIFICENT_SEVEN == expected_symbols
        assert len(fetcher.MAGNIFICENT_SEVEN) == 7

    def test_required_columns_constant(self) -> None:
        """Test that REQUIRED_COLUMNS constant contains expected columns."""
        fetcher = NYSEDataFetcher()

        expected_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        assert fetcher.REQUIRED_COLUMNS == expected_columns
        assert len(fetcher.REQUIRED_COLUMNS) == 6
