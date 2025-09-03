"""Simple endpoint test for debugging."""

from collections.abc import AsyncIterator
from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.ticker_converter.api.dependencies import get_db, get_sql_query
from src.ticker_converter.api.main import app


@pytest.mark.asyncio
class TestSimpleStockDataEndpoint:
    """Simple test class for stock data endpoint."""

    def __init__(self) -> None:
        """Initialize test class attributes."""
        self.mock_db: AsyncMock | None = None
        self.client: TestClient | None = None

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        # Create mock database
        self.mock_db = AsyncMock()

        # Create mock dependencies
        async def mock_get_db() -> AsyncIterator[AsyncMock]:
            assert self.mock_db is not None
            yield self.mock_db

        def mock_get_sql_query(filename: str) -> str:
            """Mock SQL query function."""
            return "SELECT 1;"

        # Override FastAPI dependencies
        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_sql_query] = mock_get_sql_query

        # Create test client
        self.client = TestClient(app)

    def teardown_method(self) -> None:
        """Clean up after each test method."""
        # Clear dependency overrides
        app.dependency_overrides.clear()

    async def test_simple_endpoint_call(self) -> None:
        """Simple test for endpoint functionality."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "TEST",
                "company_name": "Test Corp",
                "trade_date": date(2024, 1, 15),
                "price_usd": 100.0,
                "price_gbp": 80.0,
                "usd_to_gbp_rate": 0.8,
                "volume": 1000,
                "daily_return": 1.0,
                "market_cap_usd": 1000000.0,
                "market_cap_gbp": 800000.0,
            }
        ]

        response = self.client.get("/api/stocks/data-with-currency")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "TEST"
