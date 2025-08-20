"""Tests for async functionality and context management."""

from unittest.mock import AsyncMock, patch

import aiohttp
import pandas as pd
import pytest

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)


class TestAsyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test async context manager functionality."""
        async with AlphaVantageClient() as client:
            assert client is not None
            assert hasattr(client, "_aio_session")

    @pytest.mark.asyncio
    async def test_async_session_creation(self) -> None:
        """Test async session creation and configuration."""
        client = AlphaVantageClient()

        async with client:
            assert client._aio_session is not None
            assert isinstance(client._aio_session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_aclose_method(self) -> None:
        """Test explicit async session closing."""
        client = AlphaVantageClient()

        # Create session
        await client.__aenter__()
        assert client._aio_session is not None

        # Close session
        await client.aclose()


class TestAsyncRequests:
    """Test async HTTP request functionality."""

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
                result = await client.make_request_async({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})
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
                    await client.make_request_async({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})

    @pytest.mark.asyncio
    async def test_async_make_request_timeout(self) -> None:
        """Test async request timeout handling."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = TimeoutError()

            client = AlphaVantageClient()

            async with client:
                with pytest.raises(AlphaVantageTimeoutError):
                    await client.make_request_async({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})


class TestAsyncEndpoints:
    """Test async API endpoint methods."""

    @pytest.mark.asyncio
    async def test_async_daily_data(self) -> None:
        """Test async daily stock data retrieval."""
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

        with patch.object(AlphaVantageClient, "make_request_async", return_value=mock_response_data):
            client = AlphaVantageClient()

            async with client:
                result = await client.get_daily_async("AAPL")
                assert isinstance(result, pd.DataFrame)
                assert not result.empty

    @pytest.mark.asyncio
    async def test_async_intraday_data(self) -> None:
        """Test async intraday stock data retrieval."""
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
            client = AlphaVantageClient()

            async with client:
                result = await client.get_intraday_async("AAPL", "5min")
                assert isinstance(result, pd.DataFrame)
                assert not result.empty
