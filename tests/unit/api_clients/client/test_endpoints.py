"""Tests for API endpoint methods and data retrieval."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.constants import OutputSize
from src.ticker_converter.api_clients.exceptions import AlphaVantageDataError


class TestStockDataEndpoints:
    """Test stock data API endpoints."""

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_daily_stock_data_success(self, mock_make_request: Mock) -> None:
        """Test successful daily stock data retrieval."""
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
    def test_get_intraday_stock_data_no_data(self, mock_make_request: Mock) -> None:
        """Test successful intraday stock data retrieval."""
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

    def test_invalid_symbol_validation(self) -> None:
        """Test validation of invalid symbols."""
        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data("", OutputSize.COMPACT)

        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            client.get_daily_stock_data(None, OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, "make_request")
    def test_different_output_sizes(self, mock_make_request) -> None:
        """Test requests with different output size parameters."""
        mock_response = {
            "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"},
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            },
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")

        # Test compact output
        result_compact = client.get_daily_stock_data("AAPL", OutputSize.COMPACT)
        assert isinstance(result_compact, pd.DataFrame)

        # Test full output
        result_full = client.get_daily_stock_data("AAPL", OutputSize.FULL)
        assert isinstance(result_full, pd.DataFrame)


class TestForexAndCryptoEndpoints:
    """Test forex and cryptocurrency API endpoints."""

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_forex_daily_success(self, mock_make_request: Mock) -> None:
        """Test successful forex daily data retrieval."""
        mock_response = {
            "Meta Data": {
                "1. Information": "Forex Daily",
                "2. From Symbol": "USD",
                "3. To Symbol": "GBP",
            },
            "Time Series FX (Daily)": {
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
    def test_get_digital_currency_daily_success(self, mock_make_request: Mock) -> None:
        """Test successful digital currency daily data retrieval."""
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

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_currency_exchange_rate(self, mock_make_request) -> None:
        """Test currency exchange rate endpoint."""
        mock_response = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "2. From_Currency Name": "United States Dollar",
                "3. To_Currency Code": "GBP",
                "4. To_Currency Name": "British Pound Sterling",
                "5. Exchange Rate": "0.80000000",
                "6. Last Refreshed": "2023-01-01 12:00:00",
                "7. Time Zone": "UTC",
                "8. Bid Price": "0.79950000",
                "9. Ask Price": "0.80050000",
            }
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_currency_exchange_rate("USD", "GBP")

        assert result == mock_response

    @patch.object(AlphaVantageClient, "make_request")
    def test_get_company_overview(self, mock_make_request) -> None:
        """Test company overview endpoint."""
        mock_response = {
            "Symbol": "AAPL",
            "AssetType": "Common Stock",
            "Name": "Apple Inc",
            "Description": "Apple Inc is an American multinational technology company",
            "CIK": "320193",
            "Exchange": "NASDAQ",
            "Currency": "USD",
            "Country": "USA",
            "Sector": "TECHNOLOGY",
            "Industry": "Electronic Computers",
            "MarketCapitalization": "3000000000000",
            "EBITDA": "120000000000",
            "PERatio": "30.5",
            "EPS": "6.43",
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")
        result = client.get_company_overview("AAPL")

        assert result == mock_response


class TestDataValidationAndErrorHandling:
    """Test data validation and error handling for API endpoints."""

    @patch.object(AlphaVantageClient, "make_request")
    def test_empty_response_handling(self, mock_make_request: Mock) -> None:
        """Test handling of empty or malformed responses."""
        mock_make_request.return_value = {}

        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(AlphaVantageDataError, match="Expected key"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, "make_request")
    def test_malformed_time_series_response(self, mock_make_request: Mock) -> None:
        """Test handling of malformed time series response."""
        mock_response = {
            "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"}
            # Missing "Time Series (Daily)" key
        }
        mock_make_request.return_value = mock_response

        client = AlphaVantageClient(api_key="test_key")

        with pytest.raises(AlphaVantageDataError, match="Expected key"):
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)

    @patch.object(AlphaVantageClient, "make_request")
    def test_data_processing_edge_cases(self, mock_make_request) -> None:
        """Test data processing with edge case responses."""
        edge_cases = [
            # Empty time series
            {
                "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"},
                "Time Series (Daily)": {},
            },
            # Null time series
            {
                "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "AAPL"},
                "Time Series (Daily)": None,
            },
        ]

        client = AlphaVantageClient(api_key="test_key")

        for edge_case in edge_cases:
            mock_make_request.return_value = edge_case

            try:
                result = client.get_daily_stock_data("AAPL")
                # Should handle gracefully
                if result is not None:
                    assert isinstance(result, pd.DataFrame)
            except AlphaVantageDataError:
                # Expected for some edge cases
                pass
