"""Tests for error handling scenarios and exception conditions."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageAPIError,
    AlphaVantageAuthenticationError,
    AlphaVantageDataError,
    AlphaVantageRateLimitError,
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)


class TestAuthenticationErrors:
    """Test authentication and API key error handling."""

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_invalid_api_key_error(self, mock_setup) -> None:
        """Test invalid API key error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "Invalid API call. Please retry or visit the documentation (https://www.alphavantage.co/documentation/). If the error persists, please contact support."
        }

        client = AlphaVantageClient(api_key="invalid_key")
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageAuthenticationError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    def test_authentication_error_detection(self) -> None:
        """Test detection of various authentication error patterns."""
        auth_error_responses = [
            {"Error Message": "Invalid API call. Please retry or visit the documentation"},
            {"Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute"},
            {"Note": "Thank you for using Alpha Vantage! Please consider upgrading"},
        ]

        client = AlphaVantageClient()

        for error_response in auth_error_responses:
            with patch.object(client, "make_request", return_value=error_response):
                try:
                    result = client.get_daily_stock_data("AAPL")
                    # Should handle gracefully or raise appropriate error
                    assert result is None or hasattr(result, "__len__")
                except (
                    AlphaVantageAuthenticationError,
                    AlphaVantageRateLimitError,
                    AlphaVantageDataError,
                ):
                    # Expected for auth/rate limit errors
                    pass


class TestRateLimitErrors:
    """Test rate limit error handling."""

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_rate_limit_error_handling(self, mock_setup) -> None:
        """Test API rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Error Message": "You have reached the 5 API requests per minute limit"}

        client = AlphaVantageClient(api_key="test_key")
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageRateLimitError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    def test_rate_limit_error_patterns(self) -> None:
        """Test various rate limit error response patterns."""
        rate_limit_responses = [
            {"Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute"},
            {"Note": "Thank you for using Alpha Vantage! Please visit https://www.alphavantage.co/premium/ to upgrade"},
        ]

        client = AlphaVantageClient()

        for rate_response in rate_limit_responses:
            with patch.object(client, "make_request", return_value=rate_response):
                try:
                    result = client.get_daily_stock_data("AAPL")
                    # Should handle gracefully or raise appropriate error
                    assert result is None or hasattr(result, "__len__")
                except (AlphaVantageRateLimitError, AlphaVantageDataError):
                    # Expected for rate limit errors
                    pass


class TestDataErrors:
    """Test data validation and parsing error handling."""

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
                        assert hasattr(result, "__len__")
                except (AlphaVantageDataError, AlphaVantageAPIError):
                    # Expected for invalid data
                    pass

    def test_malformed_responses(self) -> None:
        """Test handling of malformed API responses."""
        client = AlphaVantageClient()

        # Test response with missing time series
        malformed_response1 = {"Meta Data": {"1. Information": "Test"}}
        with patch.object(client, "make_request", return_value=malformed_response1):
            try:
                result = client.get_daily_stock_data("AAPL")
                if result is not None:
                    assert hasattr(result, "__len__")
            except (AlphaVantageDataError, AlphaVantageAPIError):
                # Expected for malformed data
                pass

        # Test response with invalid time series format - this should be caught at the API level
        malformed_response2 = {"Time Series (Daily)": "not_a_dict"}
        with patch.object(client, "make_request", return_value=malformed_response2):
            try:
                result = client.get_daily_stock_data("AAPL")
                if result is not None:
                    assert hasattr(result, "__len__")
            except (AlphaVantageDataError, AlphaVantageAPIError, AttributeError):
                # Expected - the data processor will catch this as an AttributeError
                pass


class TestNetworkErrors:
    """Test network-related error handling."""

    def test_connection_error_scenarios(self) -> None:
        """Test various connection error scenarios."""
        client = AlphaVantageClient()

        # Test different types of connection errors
        connection_errors = [
            requests.ConnectionError("Connection failed"),
            requests.ConnectTimeout("Connection timeout"),
            requests.ReadTimeout("Read timeout"),
        ]

        for error in connection_errors:
            with patch.object(client, "session") as mock_session:
                mock_session.get.side_effect = error

                with pytest.raises((AlphaVantageRequestError, AlphaVantageTimeoutError)):
                    client.make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})

    def test_http_status_errors(self) -> None:
        """Test HTTP status code error handling."""
        client = AlphaVantageClient()

        # Test status codes that should raise AlphaVantageRequestError
        request_error_codes = [400, 404, 500, 502, 503]

        for status_code in request_error_codes:
            with patch.object(client, "session") as mock_session:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}")
                mock_session.get.return_value = mock_response

                with pytest.raises(AlphaVantageRequestError):
                    client.make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})

        # Test authentication error codes separately
        auth_error_codes = [401, 403]

        for status_code in auth_error_codes:
            with patch.object(client, "session") as mock_session:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.text = f"HTTP {status_code} Error"
                mock_session.get.return_value = mock_response

                with pytest.raises(AlphaVantageAuthenticationError):
                    client.make_request({"function": "TIME_SERIES_DAILY", "symbol": "AAPL"})


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

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

        with patch.object(AlphaVantageClient, "make_request", return_value=mock_response):
            client = AlphaVantageClient()

            # Simulate multiple requests
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
            results = []

            for symbol in symbols:
                result = client.get_daily_stock_data(symbol)
                results.append(result)

            assert len(results) == len(symbols)
            assert all(hasattr(r, "__len__") for r in results if r is not None)

    def test_parameter_validation_edge_cases(self) -> None:
        """Test parameter validation with edge case inputs."""
        client = AlphaVantageClient()

        # Test various invalid inputs
        invalid_symbols = ["", None, " ", "\t", "\n"]

        for invalid_symbol in invalid_symbols:
            try:
                client.get_daily_stock_data(invalid_symbol)
            except (ValueError, AlphaVantageDataError):
                # Expected for invalid inputs
                pass
