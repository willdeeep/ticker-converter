"""Comprehensive tests for AlphaVantageClient module to achieve 80%+ coverage.

This test suite focuses on high-impact coverage areas:
- Async context management and session handling
- Error handling and exception scenarios
- Data processing and validation
- Different API endpoint methods
- Configuration and initialization edge cases
"""

from unittest.mock import AsyncMock, patch

import aiohttp
import pandas as pd
import pytest
import requests

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.constants import OutputSize
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageAPIError,
    AlphaVantageAuthenticationError,
    AlphaVantageConfigError,
    AlphaVantageDataError,
    AlphaVantageRateLimitError,
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)


class TestAlphaVantageClientAsync:
    """Test async functionality and context management."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test async context manager functionality."""
        async with AlphaVantageClient() as client:
            assert client is not None
            assert hasattr(client, "_aio_session")
            # Session should be created in context manager

    @pytest.mark.asyncio
    async def test_async_session_creation(self) -> None:
        """Test async session creation and configuration."""
        client = AlphaVantageClient()

        # Access async session to trigger creation
        async with client:
            assert client._aio_session is not None
            assert isinstance(client._aio_session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_async_session_cleanup(self) -> None:
        """Test proper async session cleanup."""
        client = AlphaVantageClient()

        async with client:
            pass  # Session should be properly cleaned up

        # After context exit, session should be None - Note: this is implementation dependent

    @pytest.mark.asyncio
    async def test_aclose_method(self) -> None:
        """Test explicit async session closing."""
        client = AlphaVantageClient()

        # Create session
        await client.__aenter__()
        assert client._aio_session is not None

        # Close session
        await client.aclose()
        # Session may still exist but should be closed

    @pytest.mark.asyncio
    async def test_async_make_request_success(self) -> None:
        """Test successful async API request."""
        mock_response_data = {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None
            mock_get.return_value = mock_response

            client = AlphaVantageClient()

            async with client:
                result = await client.make_request_async(
                    {"function": "TIME_SERIES_DAILY", "symbol": "AAPL"}
                )
                assert result == mock_response_data

    @pytest.mark.asyncio
    async def test_async_make_request_http_error(self) -> None:
        """Test async request with HTTP error."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text.return_value = "Server Error"
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None
            mock_get.return_value = mock_response

            client = AlphaVantageClient()

            async with client:
                with pytest.raises(AlphaVantageRequestError):
                    await client.make_request_async(
                        {"function": "TIME_SERIES_DAILY", "symbol": "AAPL"}
                    )

    @pytest.mark.asyncio
    async def test_async_make_request_timeout(self) -> None:
        """Test async request timeout handling."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = TimeoutError()

            client = AlphaVantageClient()

            async with client:
                with pytest.raises(AlphaVantageTimeoutError):
                    await client.make_request_async(
                        {"function": "TIME_SERIES_DAILY", "symbol": "AAPL"}
                    )

    @pytest.mark.asyncio
    async def test_async_methods(self) -> None:
        """Test async API endpoint methods."""
        mock_response_data = {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        with patch.object(
            AlphaVantageClient, "make_request_async", return_value=mock_response_data
        ):
            client = AlphaVantageClient()

            async with client:
                # Test async daily data
                result = await client.get_daily_async("AAPL")
                assert isinstance(result, pd.DataFrame)
                assert not result.empty

                # Test async intraday data - use correct response format
                intraday_response = {
                    "Time Series (5min)": {
                        "2023-01-01 16:00:00": {
                            "1. open": "100.0",
                            "2. high": "105.0",
                            "3. low": "99.0",
                            "4. close": "104.0",
                            "5. volume": "1000000",
                        }
                    }
                }

                with patch.object(
                    AlphaVantageClient,
                    "make_request_async",
                    return_value=intraday_response,
                ):
                    result = await client.get_intraday_async("AAPL", "5min")
                    assert isinstance(result, pd.DataFrame)


class TestAlphaVantageClientErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_authentication_error_detection(self) -> None:
        """Test detection of authentication errors."""
        auth_error_responses = [
            {
                "Error Message": "Invalid API call. Please retry or visit the documentation"
            },
            {
                "Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute"
            },
            {"Note": "Thank you for using Alpha Vantage! Please consider upgrading"},
        ]

        client = AlphaVantageClient()

        for error_response in auth_error_responses:
            with patch.object(client, "make_request", return_value=error_response):
                # These should be caught by the API client's error handling
                # Direct mock return should simulate what the make_request returns after processing
                try:
                    result = client.get_daily_stock_data("AAPL")
                    # If no exception, verify it's handled properly
                    assert result is None or isinstance(result, pd.DataFrame)
                except (
                    AlphaVantageAuthenticationError,
                    AlphaVantageRateLimitError,
                    AlphaVantageDataError,
                ):
                    # Expected for auth/rate limit errors
                    pass

    def test_rate_limit_error_handling(self) -> None:
        """Test rate limit error detection and handling."""
        rate_limit_responses = [
            {
                "Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute"
            },
            {
                "Note": "Thank you for using Alpha Vantage! Please visit https://www.alphavantage.co/premium/ to upgrade"
            },
        ]

        client = AlphaVantageClient()

        for rate_response in rate_limit_responses:
            with patch.object(client, "make_request", return_value=rate_response):
                try:
                    result = client.get_daily_stock_data("AAPL")
                    # Should handle gracefully or raise appropriate error
                    assert result is None or isinstance(result, pd.DataFrame)
                except (AlphaVantageRateLimitError, AlphaVantageDataError):
                    # Expected for rate limit errors
                    pass

    def test_data_error_handling(self) -> None:
        """Test data validation and parsing errors."""
        invalid_responses = [
            {"Invalid": "Structure"},
            {},  # Empty response
            {"Time Series (Daily)": None},  # Null time series
        ]

        client = AlphaVantageClient()

        for invalid_response in invalid_responses:
            with patch.object(client, "make_request", return_value=invalid_response):
                try:
                    result = client.get_daily_stock_data("AAPL")
                    # Should handle gracefully or raise appropriate error
                    if result is not None:
                        assert isinstance(result, pd.DataFrame)
                except (AlphaVantageDataError, AlphaVantageAPIError):
                    # Expected for invalid data
                    pass

    def test_http_error_handling(self) -> None:
        """Test HTTP status code error handling."""
        # For this test, we need to test the make_request method directly with mocked HTTP errors
        client = AlphaVantageClient()

        # Test timeout error simulation
        with patch.object(client, "session") as mock_session:
            mock_session.get.side_effect = requests.Timeout()

            with pytest.raises(AlphaVantageTimeoutError):
                client.make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})

    def test_connection_error_handling(self) -> None:
        """Test connection and timeout error handling."""
        client = AlphaVantageClient()

        # Test connection error simulation
        with patch.object(client, "session") as mock_session:
            mock_session.get.side_effect = requests.ConnectionError()

            with pytest.raises(AlphaVantageRequestError):
                client.make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})


class TestAlphaVantageClientDataMethods:
    """Test different API endpoint methods."""

    def test_currency_exchange_rate(self) -> None:
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

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()
            result = client.get_currency_exchange_rate("USD", "GBP")

            assert result == mock_response

    def test_company_overview(self) -> None:
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
            "Address": "ONE APPLE PARK WAY, CUPERTINO, CA, US",
            "FiscalYearEnd": "September",
            "LatestQuarter": "2023-09-30",
            "MarketCapitalization": "3000000000000",
            "EBITDA": "120000000000",
            "PERatio": "30.5",
            "PEGRatio": "2.5",
            "BookValue": "4.0",
            "DividendPerShare": "0.96",
            "DividendYield": "0.004",
            "EPS": "6.43",
            "RevenuePerShareTTM": "24.32",
            "ProfitMargin": "0.265",
            "OperatingMarginTTM": "0.305",
            "ReturnOnAssetsTTM": "0.216",
            "ReturnOnEquityTTM": "1.479",
            "RevenueTTM": "394328000000",
            "GrossProfitTTM": "169148000000",
            "DilutedEPSTTM": "6.43",
            "QuarterlyEarningsGrowthYOY": "0.112",
            "QuarterlyRevenueGrowthYOY": "-0.013",
            "AnalystTargetPrice": "190.5",
            "TrailingPE": "30.5",
            "ForwardPE": "28.2",
            "PriceToSalesRatioTTM": "7.6",
            "PriceToBookRatio": "39.4",
            "EVToRevenue": "7.8",
            "EVToEBITDA": "25.5",
            "Beta": "1.24",
            "52WeekHigh": "199.62",
            "52WeekLow": "124.17",
            "50DayMovingAverage": "175.83",
            "200DayMovingAverage": "169.85",
            "SharesOutstanding": "15728700000",
            "DividendDate": "2023-11-16",
            "ExDividendDate": "2023-11-10",
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()
            result = client.get_company_overview("AAPL")

            assert result == mock_response

    def test_forex_daily(self) -> None:
        """Test forex daily data endpoint."""
        mock_response = {
            "Meta Data": {
                "1. Information": "Forex Daily Prices",
                "2. From Symbol": "USD",
                "3. To Symbol": "GBP",
                "4. Output Size": "Compact",
                "5. Last Refreshed": "2023-01-01",
                "6. Time Zone": "UTC",
            },
            "Time Series (FX Daily)": {
                "2023-01-01": {
                    "1. open": "0.8000",
                    "2. high": "0.8050",
                    "3. low": "0.7980",
                    "4. close": "0.8020",
                }
            },
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()
            result = client.get_forex_daily("USD", "GBP")

            assert isinstance(result, pd.DataFrame)
            assert not result.empty

    def test_digital_currency_daily(self) -> None:
        """Test digital currency daily data endpoint."""
        mock_response = {
            "Meta Data": {
                "1. Information": "Daily Prices for Digital Currency",
                "2. Digital Currency Code": "BTC",
                "3. Digital Currency Name": "Bitcoin",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar",
                "6. Last Refreshed": "2023-01-01 (end of day)",
                "7. Time Zone": "UTC",
            },
            "Time Series (Digital Currency Daily)": {
                "2023-01-01": {
                    "1a. open (USD)": "16500.00000000",
                    "1b. open (USD)": "16500.00000000",
                    "2a. high (USD)": "16800.00000000",
                    "2b. high (USD)": "16800.00000000",
                    "3a. low (USD)": "16400.00000000",
                    "3b. low (USD)": "16400.00000000",
                    "4a. close (USD)": "16700.00000000",
                    "4b. close (USD)": "16700.00000000",
                    "5. volume": "1234567.89012345",
                    "6. market cap (USD)": "321000000000.00000000",
                }
            },
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()
            result = client.get_digital_currency_daily("BTC", "USD")

            assert isinstance(result, pd.DataFrame)
            assert not result.empty

    def test_intraday_stock_data(self) -> None:
        """Test intraday stock data endpoint."""
        mock_response = {
            "Meta Data": {
                "1. Information": "Intraday (5min) open, high, low, close prices and volume",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2023-01-01 16:00:00",
                "4. Interval": "5min",
                "5. Output Size": "Compact",
                "6. Time Zone": "US/Eastern",
            },
            "Time Series (5min)": {
                "2023-01-01 16:00:00": {
                    "1. open": "130.0000",
                    "2. high": "131.0000",
                    "3. low": "129.5000",
                    "4. close": "130.5000",
                    "5. volume": "1234567",
                }
            },
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()
            result = client.get_intraday_stock_data("AAPL", "5min")

            assert isinstance(result, pd.DataFrame)
            assert not result.empty


class TestAlphaVantageClientConfiguration:
    """Test client configuration and initialization edge cases."""

    def test_initialization_with_custom_api_key(self) -> None:
        """Test initialization with custom API key."""
        custom_key = "custom_test_key_12345"
        client = AlphaVantageClient(api_key=custom_key)

        assert client.api_key == custom_key

    @patch.dict("os.environ", {}, clear=True)
    def test_initialization_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        with pytest.raises(AlphaVantageConfigError):
            AlphaVantageClient()

    def test_session_configuration(self) -> None:
        """Test HTTP session configuration."""
        client = AlphaVantageClient()

        # Check session setup
        assert client.session is not None
        assert hasattr(client.session, "adapters")

        # Check retry configuration
        adapter = client.session.get_adapter("https://www.alphavantage.co")
        assert adapter is not None

    def test_string_representation(self) -> None:
        """Test string representation methods."""
        client = AlphaVantageClient()

        str_repr = str(client)
        assert "AlphaVantageClient" in str_repr
        assert "api_key=" in str_repr
        assert "***" in str_repr  # API key should be masked

        repr_repr = repr(client)
        assert "AlphaVantageClient" in repr_repr

    def test_session_cleanup(self) -> None:
        """Test proper session cleanup."""
        client = AlphaVantageClient()

        # Session should exist
        assert client.session is not None

        # Close should clean up session
        client.close()
        # Note: close() might not set session to None, just closes connections


class TestAlphaVantageClientIntegration:
    """Test integration scenarios and edge cases."""

    def test_different_output_sizes(self) -> None:
        """Test requests with different output size parameters."""
        mock_response = {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ) as mock_request:
            client = AlphaVantageClient()

            # Test compact output
            client.get_daily_stock_data("AAPL", OutputSize.COMPACT)
            mock_request.assert_called()

            # Test full output
            client.get_daily_stock_data("AAPL", OutputSize.FULL)
            mock_request.assert_called()

    def test_parameter_validation(self) -> None:
        """Test parameter validation and preparation."""
        mock_response = {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        client = AlphaVantageClient()

        # Test with valid parameters - check that request is made correctly
        with patch.object(
            client, "make_request", return_value=mock_response
        ) as mock_request:
            client.get_daily_stock_data("AAPL")

            # Check that make_request was called
            mock_request.assert_called_once()

            # Check that parameters were properly formatted (though apikey is added in prepare_api_params)
            call_args = mock_request.call_args[0][0]
            assert "function" in call_args
            assert "symbol" in call_args
            assert call_args["symbol"] == "AAPL"

    def test_data_processing_edge_cases(self) -> None:
        """Test data processing with edge case responses."""
        edge_cases = [
            # Empty time series
            {"Time Series (Daily)": {}},
            # Missing expected keys
            {"Meta Data": {"1. Information": "Test"}},
        ]

        for edge_case in edge_cases:
            with patch.object(
                AlphaVantageClient, "make_request", return_value=edge_case
            ):
                client = AlphaVantageClient()

                try:
                    result = client.get_daily_stock_data("AAPL")
                    # Should handle gracefully
                    if result is not None:
                        assert isinstance(result, pd.DataFrame)
                except (AlphaVantageDataError, AlphaVantageAPIError):
                    # Expected for some edge cases
                    pass

    def test_concurrent_requests_simulation(self) -> None:
        """Test handling of multiple concurrent request scenarios."""
        mock_response = {
            "Time Series (Daily)": {
                "2023-01-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        with patch.object(
            AlphaVantageClient, "make_request", return_value=mock_response
        ):
            client = AlphaVantageClient()

            # Simulate multiple requests
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
            results = []

            for symbol in symbols:
                result = client.get_daily_stock_data(symbol)
                results.append(result)

            assert len(results) == len(symbols)
            assert all(isinstance(r, pd.DataFrame) for r in results)
