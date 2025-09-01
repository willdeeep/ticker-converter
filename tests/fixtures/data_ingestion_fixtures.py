"""Optimized fixtures for data ingestion tests.

This module provides reusable fixtures to eliminate repetitive mock setup
across data ingestion test classes, improving test performance and maintainability.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from src.ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator


class MockDataIngestionComponents:
    """Container for commonly used mock components in data ingestion tests."""

    def __init__(self) -> None:
        """Initialize mock components with standard configurations."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()

        # Set up common mock configurations
        self._setup_mock_defaults()

    def _setup_mock_defaults(self) -> None:
        """Set up common default behaviors for mocks."""
        # Default database behavior
        self.mock_db.is_database_empty.return_value = False
        self.mock_db.insert_stock_data.return_value = 0
        self.mock_db.insert_currency_data.return_value = 0

        # Default NYSE fetcher behavior
        self.mock_nyse.MAGNIFICENT_SEVEN = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
        self.mock_nyse.fetch_and_prepare_all_data.return_value = []
        self.mock_nyse.check_data_freshness.return_value = {}

        # Default currency fetcher behavior
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"
        self.mock_currency.fetch_and_prepare_fx_data.return_value = []
        self.mock_currency.get_current_exchange_rate.return_value = None

    def create_orchestrator(self) -> DataIngestionOrchestrator:
        """Create orchestrator instance with these mock components."""
        return DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def reset_mocks(self) -> None:
        """Reset all mocks and restore default configurations."""
        self.mock_db.reset_mock()
        self.mock_nyse.reset_mock()
        self.mock_currency.reset_mock()
        self._setup_mock_defaults()


@pytest.fixture
def mock_components() -> MockDataIngestionComponents:
    """Provide reusable mock components for data ingestion tests.

    Returns:
        MockDataIngestionComponents: Container with pre-configured mocks

    Example:
        def test_something(mock_components):
            orchestrator = mock_components.create_orchestrator()
            mock_components.mock_db.some_method.return_value = "test"
            # Test implementation
    """
    return MockDataIngestionComponents()


@pytest.fixture
def orchestrator_with_mocks(
    mock_components: MockDataIngestionComponents,
) -> tuple[DataIngestionOrchestrator, MockDataIngestionComponents]:
    """Provide orchestrator with mock components for convenient testing.

    Args:
        mock_components: Injected mock components fixture

    Returns:
        tuple: (orchestrator_instance, mock_components_container)

    Example:
        def test_something(orchestrator_with_mocks):
            orchestrator, mocks = orchestrator_with_mocks
            mocks.mock_db.some_method.return_value = "test"
            result = orchestrator.some_operation()
    """
    orchestrator = mock_components.create_orchestrator()
    return orchestrator, mock_components


@pytest.fixture
def sample_stock_data() -> list[dict[str, Any]]:
    """Provide sample stock data for testing.

    Returns:
        list: Sample stock data records for testing insertion operations
    """
    return [
        {
            "symbol": "AAPL",
            "data_date": "2025-08-17",
            "open_price": 220.50,
            "high_price": 231.00,
            "low_price": 219.25,
            "close_price": 229.35,
            "volume": 45000000,
            "source": "alpha_vantage",
            "created_at": "2025-08-17T10:00:00Z",
        },
        {
            "symbol": "MSFT",
            "data_date": "2025-08-17",
            "open_price": 350.00,
            "high_price": 365.50,
            "low_price": 348.75,
            "close_price": 360.25,
            "volume": 25000000,
            "source": "alpha_vantage",
            "created_at": "2025-08-17T10:00:00Z",
        },
    ]


@pytest.fixture
def sample_currency_data() -> list[dict[str, Any]]:
    """Provide sample currency data for testing.

    Returns:
        list: Sample USD/GBP exchange rate data for testing
    """
    return [
        {
            "data_date": "2025-08-17",
            "exchange_rate": 0.7850,
            "source": "alpha_vantage",
            "created_at": "2025-08-17T10:00:00Z",
            "from_currency": "USD",
            "to_currency": "GBP",
        },
        {
            "data_date": "2025-08-16",
            "exchange_rate": 0.7823,
            "source": "alpha_vantage",
            "created_at": "2025-08-16T10:00:00Z",
            "from_currency": "USD",
            "to_currency": "GBP",
        },
    ]


@pytest.fixture
def mock_successful_setup(
    mock_components: MockDataIngestionComponents,
    sample_stock_data: list[dict[str, Any]],
    sample_currency_data: list[dict[str, Any]],
) -> MockDataIngestionComponents:
    """Configure mocks for successful data ingestion scenarios.

    Args:
        mock_components: Base mock components
        sample_stock_data: Sample stock data to return
        sample_currency_data: Sample currency data to return

    Returns:
        MockDataIngestionComponents: Configured for successful operations
    """
    # Configure successful data fetching
    mock_components.mock_nyse.fetch_and_prepare_all_data.return_value = sample_stock_data
    mock_components.mock_currency.fetch_and_prepare_fx_data.return_value = sample_currency_data

    # Configure successful database operations
    mock_components.mock_db.insert_stock_data.return_value = len(sample_stock_data)
    mock_components.mock_db.insert_currency_data.return_value = len(sample_currency_data)

    return mock_components


@pytest.fixture
def mock_empty_database(mock_components: MockDataIngestionComponents) -> MockDataIngestionComponents:
    """Configure mocks for empty database scenarios.

    Args:
        mock_components: Base mock components

    Returns:
        MockDataIngestionComponents: Configured for empty database testing
    """
    mock_components.mock_db.is_database_empty.return_value = True
    mock_components.mock_db.insert_stock_data.return_value = 0
    mock_components.mock_db.insert_currency_data.return_value = 0

    return mock_components


@pytest.fixture
def mock_api_errors(mock_components: MockDataIngestionComponents) -> MockDataIngestionComponents:
    """Configure mocks for API error scenarios.

    Args:
        mock_components: Base mock components

    Returns:
        MockDataIngestionComponents: Configured for API error testing
    """
    from src.ticker_converter.api_clients.exceptions import AlphaVantageAPIError

    # Configure API errors
    mock_components.mock_nyse.fetch_and_prepare_all_data.side_effect = AlphaVantageAPIError("API rate limit exceeded")
    mock_components.mock_currency.fetch_and_prepare_fx_data.side_effect = AlphaVantageAPIError("API connection failed")

    return mock_components


@pytest.fixture
def mock_database_errors(mock_components: MockDataIngestionComponents) -> MockDataIngestionComponents:
    """Configure mocks for database error scenarios.

    Args:
        mock_components: Base mock components

    Returns:
        MockDataIngestionComponents: Configured for database error testing
    """
    from src.ticker_converter.exceptions import DatabaseConnectionException

    # Configure database errors
    mock_components.mock_db.insert_stock_data.side_effect = DatabaseConnectionException("Database connection failed")
    mock_components.mock_db.insert_currency_data.side_effect = DatabaseConnectionException("Database connection failed")

    return mock_components
