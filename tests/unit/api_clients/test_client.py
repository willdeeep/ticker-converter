"""Unit tests for the refactored Alpha Vantage API client."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests
from requests.exceptions import RequestException, Timeout

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.constants import OutputSize
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageAuthenticationError,
    AlphaVantageConfigError,
    AlphaVantageDataError,
    AlphaVantageRateLimitError,
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)


class TestAlphaVantageClient:
    """Test suite for the refactored AlphaVantageClient."""

    def test_client_initialization(self) -> None:
        """Test client initialization with default and custom settings."""
        # Test with default settings (should use environment variable)
        client = AlphaVantageClient()
        assert client.api_key is not None
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.timeout == 30
        assert client.max_retries == 3

        # Test with custom API key
        custom_client = AlphaVantageClient(api_key="custom_key")
        assert custom_client.api_key == "custom_key"
        assert custom_client.base_url == "https://www.alphavantage.co/query"
        assert custom_client.timeout == 30
        assert custom_client.max_retries == 3

    def test_client_initialization_no_api_key(self) -> None:
        """Test client initialization with no API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AlphaVantageConfigError):
                AlphaVantageClient()

    def test_make_request_success(self) -> None:
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}

        client = AlphaVantageClient(api_key="test_key")

        # Mock the session.get method directly
        client.session.get = Mock(return_value=mock_response)

        # Test successful request
        result = client.make_request(
            {"function": "TIME_SERIES_DAILY", "symbol": "AAPL"}
        )

        assert result == {"test": "data"}
        client.session.get.assert_called_once()

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_rate_limit_error(self, mock_setup) -> None:
        """Test API rate limit error handling."""
        # Setup mock response for rate limit
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "You have reached the 5 API requests per minute limit"
        }

        client = AlphaVantageClient(api_key="test_key")
        # Verify that session setup was mocked
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageRateLimitError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_invalid_api_key(self, mock_setup) -> None:
        """Test invalid API key error handling."""
        # Setup mock response for pure authentication error (no rate limit keywords)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "Invalid API call. Please retry or visit the documentation (https://www.alphavantage.co/documentation/). If the error persists, please contact support."
        }

        client = AlphaVantageClient(api_key="test_invalid_key")
        # Verify that session setup was mocked
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageAuthenticationError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_http_error(self, mock_setup) -> None:
        """Test HTTP error handling."""
        # Setup mock response for HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")

        client = AlphaVantageClient(api_key="test_key")
        # Verify that session setup was mocked
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageRequestError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_timeout(self, mock_setup) -> None:
        """Test timeout error handling."""
        # Setup mock for timeout
        client = AlphaVantageClient(api_key="test_key")
        # Verify that session setup was mocked
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.side_effect = Timeout("Request timed out")

        with pytest.raises(AlphaVantageTimeoutError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_connection_error(self, mock_setup) -> None:
        """Test connection error handling."""
        # Setup mock for connection error
        client = AlphaVantageClient(api_key="test_key")
        # Verify that session setup was mocked
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.side_effect = RequestException("Connection failed")

        with pytest.raises(AlphaVantageRequestError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_daily_stock_data_success(self, mock_make_request) -> None:
        """Test successful daily stock data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"},
            "Time Series (Daily)": {
                "2025-08-14": {
                    "1. open": "220.00",
                    "2. high": "225.00",
                    "3. low": "219.00",
                    "4. close": "224.50",
                    "5. volume": "1000000",
                }
            },
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        assert "Date" in result.columns
        assert "Symbol" in result.columns
        assert len(result) == 1
        assert result.iloc[0]["Symbol"] == "AAPL"

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_intraday_stock_data_success(self, mock_make_request) -> None:
        """Test successful intraday stock data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Intraday (5min) data",
                "2. Symbol": "AAPL",
            },
            "Time Series (5min)": {
                "2025-08-14 16:00:00": {
                    "1. open": "220.00",
                    "2. high": "225.00",
                    "3. low": "219.00",
                    "4. close": "224.50",
                    "5. volume": "1000000",
                }
            },
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_intraday_stock_data("AAPL", "5min", OutputSize.COMPACT)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_forex_daily_success(self, mock_make_request) -> None:
        """Test successful forex daily data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Forex Daily",
                "2. From Symbol": "USD",
                "3. To Symbol": "GBP",
            },
            "Time Series (FX Daily)": {
                "2025-08-14": {
                    "1. open": "0.7340",
                    "2. high": "0.7360",
                    "3. low": "0.7330",
                    "4. close": "0.7350",
                }
            },
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_forex_daily("USD", "GBP", OutputSize.COMPACT)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_digital_currency_daily_success(self, mock_make_request) -> None:
        """Test successful digital currency daily data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Digital Currency Daily",
                "2. Digital Currency Code": "BTC",
                "3. Digital Currency Name": "Bitcoin",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar",
            },
            "Time Series (Digital Currency Daily)": {
                "2025-08-14": {
                    "1a. open (USD)": "45000.00000000",
                    "1b. open (USD)": "45000.00000000",
                    "2a. high (USD)": "46000.00000000",
                    "2b. high (USD)": "46000.00000000",
                    "3a. low (USD)": "44500.00000000",
                    "3b. low (USD)": "44500.00000000",
                    "4a. close (USD)": "45800.00000000",
                    "4b. close (USD)": "45800.00000000",
                    "5. volume": "1000000.00000000",
                    "6. market cap (USD)": "900000000000.00000000",
                }
            },
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_digital_currency_daily("BTC", "USD")

        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_invalid_symbol_validation(self) -> None:
        """Test validation of invalid symbols."""
        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data("", OutputSize.COMPACT)

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data(None, OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, "make_request")
    def test_empty_response_handling(self, mock_make_request) -> None:
        """Test handling of empty or malformed responses."""
        # Test empty response
        mock_make_request.return_value = {}

        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(AlphaVantageDataError, match="Expected key"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, "make_request")
    def test_malformed_time_series_response(self, mock_make_request) -> None:
        """Test handling of malformed time series response."""
        # Test response with missing time series data
        mock_response = {
            "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"}
            # Missing "Time Series (Daily)" key
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(AlphaVantageDataError, match="Expected key"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    def test_str_representation(self) -> None:
        """Test string representation of the client."""
        client = AlphaVantageClient(api_key="test_key")
        str_repr = str(client)

        assert "AlphaVantageClient" in str_repr
        assert "test_key" not in str_repr  # API key should be masked
        assert "***" in str_repr  # Should show masked API key

    def test_repr_representation(self) -> None:
        """Test repr representation of the client."""
        client = AlphaVantageClient(api_key="test_key")
        repr_str = repr(client)

        assert "AlphaVantageClient" in repr_str
        assert "api_key=" in repr_str
        assert "test_key" not in repr_str  # API key should be masked
