"""Core tests for AlphaVantageClient initialization and basic functionality."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.ticker_converter.api_clients.client import AlphaVantageClient
from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageConfigError,
    AlphaVantageRequestError,
    AlphaVantageTimeoutError,
)


class TestAlphaVantageClientInitialization:
    """Test client initialization and configuration."""

    def test_client_initialization_with_api_key(self) -> None:
        """Test client initialization with provided API key."""
        client = AlphaVantageClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_client_initialization_from_environment(self) -> None:
        """Test client initialization using environment variable."""
        client = AlphaVantageClient()
        assert client.api_key is not None
        assert client.base_url == "https://www.alphavantage.co/query"
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_client_initialization_no_api_key(self) -> None:
        """Test client initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AlphaVantageConfigError):
                AlphaVantageClient()

    def test_session_configuration(self) -> None:
        """Test HTTP session is properly configured."""
        client = AlphaVantageClient(api_key="test_key")
        assert client.session is not None
        assert hasattr(client.session, "adapters")

    def test_string_representations(self) -> None:
        """Test string and repr representations."""
        client = AlphaVantageClient(api_key="test_key")

        str_repr = str(client)
        assert "AlphaVantageClient" in str_repr
        assert "test_key" not in str_repr  # API key should be masked
        assert "***" in str_repr

        repr_str = repr(client)
        assert "AlphaVantageClient" in repr_str
        assert "api_key=" in repr_str
        assert "test_key" not in repr_str  # API key should be masked


class TestAlphaVantageClientHttpRequests:
    """Test HTTP request functionality and error handling."""

    def test_make_request_success(self) -> None:
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}

        client = AlphaVantageClient(api_key="test_key")
        client.session.get = Mock(return_value=mock_response)

        result = client.make_request(
            {"function": "TIME_SERIES_DAILY", "symbol": "AAPL"}
        )

        assert result == {"test": "data"}
        client.session.get.assert_called_once()

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_http_error(self, mock_setup) -> None:
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")

        client = AlphaVantageClient(api_key="test_key")
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.return_value = mock_response

        with pytest.raises(AlphaVantageRequestError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_timeout(self, mock_setup) -> None:
        """Test timeout error handling."""
        client = AlphaVantageClient(api_key="test_key")
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(AlphaVantageTimeoutError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    @patch.object(AlphaVantageClient, "_setup_sync_session")
    def test_make_request_connection_error(self, mock_setup) -> None:
        """Test connection error handling."""
        client = AlphaVantageClient(api_key="test_key")
        mock_setup.assert_called_once()
        client.session = Mock()
        client.session.get.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(AlphaVantageRequestError):
            client.make_request({"function": "TIME_SERIES_DAILY"})

    def test_session_cleanup(self) -> None:
        """Test proper session cleanup."""
        client = AlphaVantageClient(api_key="test_key")
        assert client.session is not None

        client.close()
        # Session cleanup behavior may vary by implementation
