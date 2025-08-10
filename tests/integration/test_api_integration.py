"""Integration tests for API functionality.

These tests can be run with real API calls for full integration testing.
Set INTEGRATION_TEST=true to enable real API calls.
"""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.ticker_converter.api_client import AlphaVantageAPIError, AlphaVantageClient
from src.ticker_converter.core import FinancialDataPipeline

# Skip integration tests unless explicitly enabled
INTEGRATION_ENABLED = os.getenv("INTEGRATION_TEST", "false").lower() == "true"
REAL_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

integration_test = pytest.mark.skipif(
    not INTEGRATION_ENABLED or not REAL_API_KEY,
    reason="Integration tests require INTEGRATION_TEST=true and valid API key",
)


class TestAPIIntegration:
    """Integration tests for API functionality."""

    @integration_test
    def test_real_api_daily_data_fetch(self):
        """Test fetching real daily data from Alpha Vantage."""
        client = AlphaVantageClient(REAL_API_KEY)

        # Test with a well-known stock
        df = client.get_daily_stock_data("AAPL", "compact")

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
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

        # Check data types
        assert pd.api.types.is_datetime64_any_dtype(df["Date"])
        assert pd.api.types.is_numeric_dtype(df["Open"])
        assert pd.api.types.is_numeric_dtype(df["High"])
        assert pd.api.types.is_numeric_dtype(df["Low"])
        assert pd.api.types.is_numeric_dtype(df["Close"])
        assert pd.api.types.is_integer_dtype(df["Volume"])

    @integration_test
    def test_real_api_company_overview(self):
        """Test fetching real company overview from Alpha Vantage."""
        client = AlphaVantageClient(REAL_API_KEY)

        # Test with Apple
        overview = client.get_company_overview("AAPL")

        assert isinstance(overview, dict)
        assert overview.get("Symbol") == "AAPL"
        assert overview.get("Name") == "Apple Inc"
        assert "Sector" in overview
        assert "MarketCapitalization" in overview

    @integration_test
    def test_real_api_invalid_symbol(self):
        """Test API behavior with invalid symbol."""
        client = AlphaVantageClient(REAL_API_KEY)

        # This should handle gracefully or raise appropriate error
        with pytest.raises(AlphaVantageAPIError):
            client.get_daily_stock_data("INVALID_SYMBOL_12345")

    @integration_test
    def test_pipeline_integration(self):
        """Test full pipeline integration with real API."""
        pipeline = FinancialDataPipeline(REAL_API_KEY)

        # Test daily data
        daily_data = pipeline.fetch_stock_data("MSFT", "1mo")
        assert isinstance(daily_data, pd.DataFrame)
        assert len(daily_data) > 0

        # Test company info
        company_info = pipeline.get_company_info("MSFT")
        assert isinstance(company_info, dict)
        assert company_info.get("Symbol") == "MSFT"


class TestMockedIntegration:
    """Integration tests using mocked responses (always run)."""

    def test_end_to_end_data_flow(self, sample_daily_response, sample_company_overview):
        """Test complete data flow from API to pipeline."""
        with patch("requests.Session") as mock_session_class:
            # Mock the session and response
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = [
                sample_daily_response,
                sample_company_overview,
            ]

            # Create pipeline and test full flow
            pipeline = FinancialDataPipeline("test_key")

            # Fetch stock data
            stock_data = pipeline.fetch_stock_data("AAPL", "1mo")
            assert isinstance(stock_data, pd.DataFrame)
            assert len(stock_data) == 2
            assert stock_data["Symbol"].iloc[0] == "AAPL"

            # Fetch company info
            company_info = pipeline.get_company_info("AAPL")
            assert company_info["Name"] == "Apple Inc"
            assert company_info["Sector"] == "TECHNOLOGY"

    def test_error_recovery_flow(self):
        """Test error handling across the full pipeline."""
        with patch("requests.Session") as mock_session_class:
            # Mock API error
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"Error Message": "Invalid API call"}

            pipeline = FinancialDataPipeline("test_key")

            # Should handle error gracefully
            result = pipeline.fetch_stock_data("INVALID")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_data_consistency(self, sample_daily_response):
        """Test data consistency across multiple calls."""
        with patch("requests.Session") as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_daily_response

            pipeline = FinancialDataPipeline("test_key")

            # Fetch same data twice
            data1 = pipeline.fetch_stock_data("AAPL", "1mo")
            data2 = pipeline.fetch_stock_data("AAPL", "1mo")

            # Should be identical
            pd.testing.assert_frame_equal(data1, data2)
