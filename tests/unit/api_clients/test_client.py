"""Unit tests for the refactored Alpha Vantage API client."""

from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
import pandas as pd
from requests.exceptions import RequestException, Timeout

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageAPIError,
    AlphaVantageRateLimitError,
    AlphaVantageInvalidAPIKeyError,
    AlphaVantageInvalidFunctionError,
    AlphaVantageConnectionError,
)
from src.ticker_converter.api_clients.constants import OutputSize, Interval


class TestAlphaVantageClient:
    """Test suite for the refactored AlphaVantageClient."""

    def test_client_initialization(self):
        """Test client initialization with default and custom settings."""
        # Test with default settings
        client = AlphaVantageClient()
        assert client.api_key is not None
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.timeout == 30
        assert client.max_retries == 3

        # Test with custom settings
        custom_client = AlphaVantageClient(
            api_key="custom_key",
            timeout=60,
            max_retries=5
        )
        assert custom_client.api_key == "custom_key"
        assert custom_client.timeout == 60
        assert custom_client.max_retries == 5

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        
        # Test successful request
        result = client._make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})
        
        assert result == {"test": "data"}
        mock_get.assert_called_once()

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_rate_limit_error(self, mock_get):
        """Test API rate limit error handling."""
        # Setup mock response for rate limit
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "You have reached the 5 API requests per minute limit"
        }
        mock_get.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageRateLimitError):
            client._make_request({"function": "TIME_SERIES_DAILY"})

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_invalid_api_key(self, mock_get):
        """Test invalid API key error handling."""
        # Setup mock response for invalid API key
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "Invalid API call. Please retry or visit the documentation"
        }
        mock_get.return_value = mock_response

        client = AlphaVantageClient(api_key="invalid_key")
        
        with pytest.raises(AlphaVantageInvalidAPIKeyError):
            client._make_request({"function": "TIME_SERIES_DAILY"})

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_http_error(self, mock_get):
        """Test HTTP error handling."""
        # Setup mock response for HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
        mock_get.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageConnectionError):
            client._make_request({"function": "TIME_SERIES_DAILY"})

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_timeout(self, mock_get):
        """Test timeout error handling."""
        # Setup mock for timeout
        mock_get.side_effect = Timeout("Request timed out")

        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageConnectionError):
            client._make_request({"function": "TIME_SERIES_DAILY"})

    @patch('src.ticker_converter.api_clients.client.requests.get')
    def test_make_request_connection_error(self, mock_get):
        """Test connection error handling."""
        # Setup mock for connection error
        mock_get.side_effect = RequestException("Connection failed")

        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageConnectionError):
            client._make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_daily_stock_data_success(self, mock_make_request):
        """Test successful daily stock data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Symbol": "AAPL"
            },
            "Time Series (Daily)": {
                "2025-08-14": {
                    "1. open": "220.00",
                    "2. high": "225.00",
                    "3. low": "219.00",
                    "4. close": "224.50",
                    "5. volume": "1000000"
                }
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_daily_stock_data("AAPL", OutputSize.COMPACT)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_intraday_stock_data_success(self, mock_make_request):
        """Test successful intraday stock data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Intraday (5min) data",
                "2. Symbol": "AAPL"
            },
            "Time Series (5min)": {
                "2025-08-14 16:00:00": {
                    "1. open": "220.00",
                    "2. high": "225.00",
                    "3. low": "219.00",
                    "4. close": "224.50",
                    "5. volume": "1000000"
                }
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_intraday_stock_data("AAPL", Interval.FIVE_MIN, OutputSize.COMPACT)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_company_overview_success(self, mock_make_request):
        """Test successful company overview retrieval."""
        # Setup mock response
        mock_response = {
            "Symbol": "AAPL",
            "AssetType": "Common Stock",
            "Name": "Apple Inc",
            "Description": "Apple Inc. designs, manufactures, and markets smartphones",
            "Exchange": "NASDAQ",
            "Currency": "USD",
            "Country": "USA",
            "Sector": "TECHNOLOGY",
            "Industry": "Electronic Computers",
            "MarketCapitalization": "3000000000000"
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_company_overview("AAPL")
        
        assert result["Symbol"] == "AAPL"
        assert result["Name"] == "Apple Inc"
        assert result["Sector"] == "TECHNOLOGY"

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_currency_exchange_rate_success(self, mock_make_request):
        """Test successful currency exchange rate retrieval."""
        # Setup mock response
        mock_response = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "2. From_Currency Name": "United States Dollar",
                "3. To_Currency Code": "GBP",
                "4. To_Currency Name": "British Pound Sterling",
                "5. Exchange Rate": "0.73500000",
                "6. Last Refreshed": "2025-08-14 16:00:00",
                "7. Time Zone": "UTC",
                "8. Bid Price": "0.73490000",
                "9. Ask Price": "0.73510000"
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_currency_exchange_rate("USD", "GBP")
        
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "GBP"
        assert "exchange_rate" in result
        assert "last_refreshed" in result

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_forex_daily_success(self, mock_make_request):
        """Test successful forex daily data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Forex Daily",
                "2. From Symbol": "USD",
                "3. To Symbol": "GBP"
            },
            "Time Series FX (Daily)": {
                "2025-08-14": {
                    "1. open": "0.7340",
                    "2. high": "0.7360",
                    "3. low": "0.7330",
                    "4. close": "0.7350"
                }
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_forex_daily("USD", "GBP", OutputSize.COMPACT)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_digital_currency_daily_success(self, mock_make_request):
        """Test successful digital currency daily data retrieval."""
        # Setup mock response
        mock_response = {
            "Meta Data": {
                "1. Information": "Digital Currency Daily",
                "2. Digital Currency Code": "BTC",
                "3. Digital Currency Name": "Bitcoin",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar"
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
                    "6. market cap (USD)": "900000000000.00000000"
                }
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_digital_currency_daily("BTC", "USD")
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_invalid_symbol_validation(self):
        """Test validation of invalid symbols."""
        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data("", OutputSize.COMPACT)
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data(None, OutputSize.COMPACT)

    def test_invalid_currency_validation(self):
        """Test validation of invalid currency codes."""
        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(ValueError, match="Currency codes cannot be empty"):
            client.get_currency_exchange_rate("", "GBP")
        
        with pytest.raises(ValueError, match="Currency codes cannot be empty"):
            client.get_currency_exchange_rate("USD", "")

    @patch.object(AlphaVantageClient, '_make_request')
    def test_empty_response_handling(self, mock_make_request):
        """Test handling of empty or malformed responses."""
        # Test empty response
        mock_make_request.return_value = {}
        
        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageAPIError, match="No data available"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, '_make_request')
    def test_malformed_time_series_response(self, mock_make_request):
        """Test handling of malformed time series response."""
        # Test response with missing time series data
        mock_response = {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Symbol": "AAPL"
            }
            # Missing "Time Series (Daily)" key
        }
        mock_make_request.return_value = mock_response
        
        client = AlphaVantageClient(api_key="test_key")
        
        with pytest.raises(AlphaVantageAPIError, match="No time series data found"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    def test_str_representation(self):
        """Test string representation of the client."""
        client = AlphaVantageClient(api_key="test_key")
        str_repr = str(client)
        
        assert "AlphaVantageClient" in str_repr
        assert "test_key" not in str_repr  # API key should be masked
        assert "***" in str_repr  # Should show masked API key

    def test_repr_representation(self):
        """Test repr representation of the client."""
        client = AlphaVantageClient(api_key="test_key")
        repr_str = repr(client)
        
        assert "AlphaVantageClient" in repr_str
        assert "api_key=" in repr_str
        assert "test_key" not in repr_str  # API key should be masked
