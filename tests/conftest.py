"""Pytest configuration and shared fixtures."""

from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.ticker_converter.api_client import AlphaVantageClient
from src.ticker_converter.core import FinancialDataPipeline


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch("src.ticker_converter.api_client.config") as mock_cfg:
        mock_cfg.ALPHA_VANTAGE_API_KEY = "test_api_key"
        mock_cfg.ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
        mock_cfg.API_TIMEOUT = 30
        mock_cfg.MAX_RETRIES = 3
        mock_cfg.RATE_LIMIT_DELAY = 1.0
        yield mock_cfg


@pytest.fixture
def sample_daily_response() -> dict[str, Any]:
    """Sample Alpha Vantage daily response data."""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2025-08-08",
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern",
        },
        "Time Series (Daily)": {
            "2025-08-08": {
                "1. open": "220.83",
                "2. high": "231.00",
                "3. low": "219.25",
                "4. close": "229.35",
                "5. volume": "113853967",
            },
            "2025-08-07": {
                "1. open": "218.875",
                "2. high": "220.85",
                "3. low": "216.58",
                "4. close": "220.03",
                "5. volume": "90224834",
            },
        },
    }


@pytest.fixture
def sample_intraday_response() -> dict[str, Any]:
    """Sample Alpha Vantage intraday response data."""
    return {
        "Meta Data": {
            "1. Information": "Intraday (5min) open, high, low, close prices and volume",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2025-08-08 16:00:00",
            "4. Interval": "5min",
            "5. Output Size": "Compact",
            "6. Time Zone": "US/Eastern",
        },
        "Time Series (5min)": {
            "2025-08-08 16:00:00": {
                "1. open": "229.30",
                "2. high": "229.40",
                "3. low": "229.20",
                "4. close": "229.35",
                "5. volume": "1234567",
            },
            "2025-08-08 15:55:00": {
                "1. open": "229.10",
                "2. high": "229.35",
                "3. low": "229.05",
                "4. close": "229.30",
                "5. volume": "987654",
            },
        },
    }


@pytest.fixture
def sample_company_overview() -> dict[str, Any]:
    """Sample Alpha Vantage company overview response."""
    return {
        "Symbol": "AAPL",
        "AssetType": "Common Stock",
        "Name": "Apple Inc",
        "Description": "Apple Inc. designs, manufactures, and markets smartphones...",
        "CIK": "320193",
        "Exchange": "NASDAQ",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "TECHNOLOGY",
        "Industry": "Electronic Computers",
        "MarketCapitalization": "3403645714000",
        "EBITDA": "131000000000",
        "PERatio": "29.1",
        "PEGRatio": "2.97",
        "BookValue": "4.382",
    }


@pytest.fixture
def mock_requests_session():
    """Mock requests session for API testing."""
    with patch("requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def alpha_vantage_client(mock_config):
    """Alpha Vantage client instance for testing."""
    return AlphaVantageClient("test_api_key")


@pytest.fixture
def financial_pipeline(mock_config):
    """Financial data pipeline instance for testing."""
    return FinancialDataPipeline("test_api_key")


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2025-08-07", "2025-08-08"]),
            "Open": [218.875, 220.83],
            "High": [220.85, 231.00],
            "Low": [216.58, 219.25],
            "Close": [220.03, 229.35],
            "Volume": [90224834, 113853967],
            "Symbol": ["AAPL", "AAPL"],
        }
    )
