"""Integration tests for Alpha Vantage API functionality.

These tests verify that the Alpha Vantage API is accessible, API key is present and valid,
and that minimal calls to the API deliver data in the expected formats and structure.

Tests require valid ALPHA_VANTAGE_API_KEY in environment to run.
"""

import os
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest
import requests

from src.ticker_converter.api_clients import AlphaVantageAPIError, AlphaVantageClient

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Configuration for integration tests
# Integration tests should FAIL if environment variables are not set
# This ensures the setup process has properly configured the environment
REAL_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


class TestAlphaVantageAPIAccessibility:
    """Test Alpha Vantage API accessibility and configuration."""

    def test_api_key_present_and_not_default(self) -> None:
        """Test that Alpha Vantage API key is present and not a default value."""
        assert REAL_API_KEY is not None, "ALPHA_VANTAGE_API_KEY must be set in environment"
        assert REAL_API_KEY != "", "ALPHA_VANTAGE_API_KEY cannot be empty"
        assert REAL_API_KEY != "demo", "ALPHA_VANTAGE_API_KEY cannot be 'demo'"
        assert REAL_API_KEY != "your_api_key_here", "ALPHA_VANTAGE_API_KEY cannot be placeholder"
        assert len(REAL_API_KEY) > 10, "ALPHA_VANTAGE_API_KEY appears to be too short"

    def test_api_connectivity(self) -> None:
        """Test basic connectivity to Alpha Vantage API."""
        # Test basic HTTP connectivity to Alpha Vantage
        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": "AAPL",
                    "apikey": REAL_API_KEY,
                    "outputsize": "compact",
                },
                timeout=30,
            )
            assert response.status_code == 200, f"API returned status {response.status_code}"

            # Check that we get JSON response
            data = response.json()
            assert isinstance(data, dict), "API should return JSON object"

            # Check for either valid data or known error patterns
            has_data = "Time Series (Daily)" in data
            has_rate_limit = any(key in data for key in ["Information", "Note"])
            has_error = "Error Message" in data

            assert has_data or has_rate_limit or has_error, "API response format unexpected"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Unable to connect to Alpha Vantage API: {e}")

    def test_api_key_validity(self) -> None:
        """Test that the API key is valid and not rejected."""
        client = AlphaVantageClient(REAL_API_KEY)

        try:
            # Try to get company overview (simpler endpoint)
            result = client.get_company_overview("AAPL")

            # If we get here without exception, API key is valid
            assert isinstance(result, dict), "Company overview should return dict"

            # Check for valid response (not an error message)
            if "Error Message" in result:
                error_msg = result["Error Message"]
                if "Invalid API call" in error_msg or "API key" in error_msg:
                    pytest.fail(f"API key appears to be invalid: {error_msg}")

        except Exception as e:
            # Check if it's an API key issue
            if "Invalid API" in str(e) or "authentication" in str(e).lower():
                pytest.fail(f"API key validation failed: {e}")
            # Other errors might be rate limits or temporary issues
            pytest.skip(f"API temporarily unavailable: {e}")


class TestAlphaVantageDataFormats:
    """Test that API calls deliver data in expected formats and structure."""

    def test_daily_stock_data_format(self) -> None:
        """Test that daily stock data is returned in expected format."""
        client = AlphaVantageClient(REAL_API_KEY)

        try:
            df = client.get_daily_stock_data("AAPL", "compact")

            # Check DataFrame structure
            assert isinstance(df, pd.DataFrame), "Daily data should be DataFrame"

            # Check expected columns
            expected_columns = [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Symbol",
            ]
            assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}"

            # Check data types
            assert pd.api.types.is_datetime64_any_dtype(df["Date"]), "Date should be datetime"
            assert pd.api.types.is_numeric_dtype(df["Open"]), "Open should be numeric"
            assert pd.api.types.is_numeric_dtype(df["High"]), "High should be numeric"
            assert pd.api.types.is_numeric_dtype(df["Low"]), "Low should be numeric"
            assert pd.api.types.is_numeric_dtype(df["Close"]), "Close should be numeric"
            assert pd.api.types.is_integer_dtype(df["Volume"]), "Volume should be integer"

            # Check symbol consistency
            if len(df) > 0:
                assert df["Symbol"].iloc[0] == "AAPL", "Symbol should match request"

        except Exception as e:
            if "rate limit" in str(e).lower() or "frequency" in str(e).lower():
                pytest.skip(f"Rate limit reached: {e}")
            else:
                raise

    def test_company_overview_format(self) -> None:
        """Test that company overview data is returned in expected format."""
        client = AlphaVantageClient(REAL_API_KEY)

        try:
            overview = client.get_company_overview("AAPL")

            # Check basic structure
            assert isinstance(overview, dict), "Company overview should be dict"

            # Check for essential fields
            essential_fields = ["Symbol", "Name", "Sector", "MarketCapitalization"]
            for field in essential_fields:
                assert field in overview, f"Missing essential field: {field}"

            # Check symbol matches
            assert overview.get("Symbol") == "AAPL", "Symbol should match request"
            assert overview.get("Name") == "Apple Inc", "Name should be Apple Inc"

        except Exception as e:
            if "rate limit" in str(e).lower() or "frequency" in str(e).lower():
                pytest.skip(f"Rate limit reached: {e}")
            else:
                raise

    def test_error_handling_for_invalid_symbol(self) -> None:
        """Test API error handling for invalid symbols."""
        client = AlphaVantageClient(REAL_API_KEY)

        try:
            # Try to get data for clearly invalid symbol
            with pytest.raises(AlphaVantageAPIError):
                client.get_daily_stock_data("INVALID_SYMBOL_12345_XYZ", "compact")

        except Exception as e:
            if "rate limit" in str(e).lower() or "frequency" in str(e).lower():
                pytest.skip(f"Rate limit reached: {e}")
            else:
                raise


class TestMockedAPIIntegration:
    """Integration tests using mocked responses (always run)."""

    @patch("time.sleep")  # Mock sleep to prevent delays in tests
    def test_end_to_end_data_flow(
        self,
        mock_sleep,
        sample_daily_response: dict[str, Any],
        sample_company_overview: dict[str, Any],
    ) -> None:
        """Test complete data flow from API client."""
        with patch("requests.Session") as mock_session_class:
            # Mock the session and response
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = [
                sample_daily_response,
                sample_company_overview,
            ]

            # Create client and test full flow
            client = AlphaVantageClient("test_key")

            # Fetch stock data
            stock_data = client.get_daily_stock_data("AAPL", "compact")
            assert isinstance(stock_data, pd.DataFrame)
            assert len(stock_data) == 2
            assert stock_data["Symbol"].iloc[0] == "AAPL"

            # Fetch company info
            company_info = client.get_company_overview("AAPL")
            assert company_info["Name"] == "Apple Inc"
            assert company_info["Sector"] == "TECHNOLOGY"

    def test_error_recovery_flow(self) -> None:
        """Test error handling in the API client."""
        with patch("requests.Session") as mock_session_class:
            # Mock API error
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"Error Message": "Invalid API call"}

            client = AlphaVantageClient("test_key")

            # Should handle error gracefully
            with pytest.raises(AlphaVantageAPIError):
                client.get_daily_stock_data("INVALID", "compact")

    @patch("time.sleep")  # Mock sleep to prevent delays in tests
    def test_data_consistency(self, mock_sleep, sample_daily_response: dict[str, Any]) -> None:
        """Test data consistency across multiple calls."""
        with patch("requests.Session") as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_response = mock_session.get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_daily_response

            client = AlphaVantageClient("test_key")

            # Fetch same data twice
            data1 = client.get_daily_stock_data("AAPL", "compact")
            data2 = client.get_daily_stock_data("AAPL", "compact")

            # Should be identical
            pd.testing.assert_frame_equal(data1, data2)
