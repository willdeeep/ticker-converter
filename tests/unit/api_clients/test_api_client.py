"""Unit tests for Alpha Vantage API client."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from src.ticker_converter.api_clients.api_client import (
    AlphaVantageAPIError,
    AlphaVantageClient,
)


class TestAlphaVantageClient:
    """Test Alpha Vantage API client."""

    def test_client_initialization_with_api_key(self):
        """Test client initializes correctly with API key."""
        client = AlphaVantageClient("test_key")

        assert client.api_key == "test_key"
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.rate_limit_delay == 12  # Alpha Vantage free tier rate limit
        assert client.session is not None

    def test_client_initialization_without_api_key_raises_error(self):
        """Test client raises error when no API key provided."""
        # Mock config to return empty API key
        with patch(
            "src.ticker_converter.api_clients.api_client.get_api_config"
        ) as mock_get_config:
            mock_get_config.side_effect = ValueError(
                "ALPHA_VANTAGE_API_KEY environment variable is required"
            )

            with pytest.raises(
                ValueError,
                match="ALPHA_VANTAGE_API_KEY environment variable is required",
            ):
                AlphaVantageClient()

    def test_client_uses_config_api_key(self, mock_config):  # pylint: disable=unused-argument
        """Test client uses config API key when none provided."""
        client = AlphaVantageClient()
        assert client.api_key == "test_api_key"

    @patch("time.sleep")
    def test_make_request_success(
        self, mock_sleep, alpha_vantage_client, sample_daily_response
    ):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_daily_response

        with patch.object(
            alpha_vantage_client.session, "get", return_value=mock_response
        ):
            result = alpha_vantage_client.make_request(
                {"function": "TIME_SERIES_DAILY"}
            )

        assert result == sample_daily_response
        mock_sleep.assert_called_once_with(
            12
        )  # Rate limiting (12 seconds for free tier)

    @patch("time.sleep")
    def test_make_request_api_error(
        self, mock_sleep, alpha_vantage_client
    ):  # pylint: disable=unused-argument
        """Test API error handling."""
        error_response = {"Error Message": "Invalid API call"}
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = error_response

        with patch.object(
            alpha_vantage_client.session, "get", return_value=mock_response
        ):
            with pytest.raises(
                AlphaVantageAPIError, match="API Error: Invalid API call"
            ):
                alpha_vantage_client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch("time.sleep")
    def test_make_request_rate_limit_retry(
        self, mock_sleep, alpha_vantage_client, sample_daily_response
    ):
        """Test rate limit handling with retry."""
        rate_limit_response = {"Note": "API rate limit reached"}

        mock_response_rate_limit = Mock()
        mock_response_rate_limit.raise_for_status.return_value = None
        mock_response_rate_limit.json.return_value = rate_limit_response

        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = sample_daily_response

        with patch.object(
            alpha_vantage_client.session,
            "get",
            side_effect=[mock_response_rate_limit, mock_response_success],
        ):
            result = alpha_vantage_client.make_request(
                {"function": "TIME_SERIES_DAILY"}
            )

        assert result == sample_daily_response
        # Should sleep for rate limit (1.0) then final rate limiting (1.0)
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_make_request_max_retries_exceeded(
        self, mock_sleep, alpha_vantage_client
    ):  # pylint: disable=unused-argument
        """Test max retries exceeded."""
        with patch.object(
            alpha_vantage_client.session,
            "get",
            side_effect=requests.RequestException("Connection error"),
        ):
            with pytest.raises(
                AlphaVantageAPIError, match="Request failed after 3 attempts"
            ):
                alpha_vantage_client.make_request({"function": "TIME_SERIES_DAILY"})

    def test_get_daily_stock_data_success(
        self, alpha_vantage_client, sample_daily_response
    ):
        """Test successful daily stock data retrieval."""
        with patch.object(
            alpha_vantage_client, "make_request", return_value=sample_daily_response
        ):
            df = alpha_vantage_client.get_daily_stock_data("AAPL")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Symbol",
        ]
        assert df["Symbol"].iloc[0] == "AAPL"
        assert df["Close"].iloc[-1] == 229.35  # Latest close price

    def test_get_daily_stock_data_unexpected_format(self, alpha_vantage_client):
        """Test handling of unexpected response format."""
        invalid_response = {"Unexpected": "format"}

        with patch.object(
            alpha_vantage_client, "make_request", return_value=invalid_response
        ):
            with pytest.raises(
                AlphaVantageAPIError, match="Unexpected response format"
            ):
                alpha_vantage_client.get_daily_stock_data("AAPL")

    def test_get_intraday_stock_data_success(
        self, alpha_vantage_client, sample_intraday_response
    ):
        """Test successful intraday stock data retrieval."""
        with patch.object(
            alpha_vantage_client, "make_request", return_value=sample_intraday_response
        ):
            df = alpha_vantage_client.get_intraday_stock_data("AAPL", "5min")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "DateTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Symbol",
        ]
        assert df["Symbol"].iloc[0] == "AAPL"

    def test_get_company_overview_success(
        self, alpha_vantage_client, sample_company_overview
    ):
        """Test successful company overview retrieval."""
        with patch.object(
            alpha_vantage_client, "make_request", return_value=sample_company_overview
        ):
            result = alpha_vantage_client.get_company_overview("AAPL")

        assert result == sample_company_overview
        assert result["Name"] == "Apple Inc"
        assert result["Sector"] == "TECHNOLOGY"

    def test_symbol_case_handling(self, alpha_vantage_client, sample_daily_response):
        """Test that symbols are properly converted to uppercase."""
        with patch.object(
            alpha_vantage_client, "make_request", return_value=sample_daily_response
        ) as mock_request:
            alpha_vantage_client.get_daily_stock_data("aapl")

        # Check that the request was made with uppercase symbol
        mock_request.assert_called_once_with(
            {"function": "TIME_SERIES_DAILY", "symbol": "AAPL", "outputsize": "compact"}
        )
