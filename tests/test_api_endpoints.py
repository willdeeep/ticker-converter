"""Unit tests for Magnificent Seven Stock Performance API."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import (
    _build_stock_performance_details,
    _build_top_performer_stock,
    app,
)
from api.models import StockPerformanceDetails, TopPerformerStock


class TestModelBuilders:
    """Test the model builder functions."""

    def test_build_top_performer_stock(self):
        """Test building TopPerformerStock from database row."""
        row = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "price_usd": 150.25,
            "price_gbp": 120.50,
            "daily_return": 2.5,
            "volume": 1000000,
            "trade_date": date(2024, 1, 15),
            "performance_rank": 1,
        }

        result = _build_top_performer_stock(row)

        assert isinstance(result, TopPerformerStock)
        assert result.symbol == "AAPL"
        assert result.company_name == "Apple Inc."
        assert result.price_usd == 150.25
        assert result.price_gbp == 120.50
        assert result.daily_return == 2.5
        assert result.volume == 1000000
        assert result.trade_date == date(2024, 1, 15)
        assert result.performance_rank == 1

    def test_build_top_performer_stock_with_nulls(self):
        """Test building TopPerformerStock with null values."""
        row = {
            "symbol": "MSFT",
            "company_name": "Microsoft Corporation",
            "price_usd": 350.00,
            "price_gbp": None,
            "daily_return": None,
            "volume": 500000,
            "trade_date": date(2024, 1, 15),
            "performance_rank": None,
        }

        result = _build_top_performer_stock(row)

        assert result.symbol == "MSFT"
        assert result.price_gbp is None
        assert result.daily_return is None
        assert result.performance_rank is None

    def test_build_stock_performance_details(self):
        """Test building StockPerformanceDetails from database row."""
        row = {
            "symbol": "GOOGL",
            "company_name": "Alphabet Inc.",
            "price_usd": 2500.00,
            "price_gbp": 2000.00,
            "daily_return": 1.5,
            "volume": 800000,
            "trade_date": date(2024, 1, 15),
            "avg_price_30d_usd": 2450.00,
            "avg_volume_30d": 750000,
            "price_change_30d_pct": 5.2,
            "volatility_30d": 0.025,
            "performance_rank": 2,
        }

        result = _build_stock_performance_details(row)

        assert isinstance(result, StockPerformanceDetails)
        assert result.symbol == "GOOGL"
        assert result.company_name == "Alphabet Inc."
        assert result.avg_price_30d_usd == 2450.00
        assert result.avg_volume_30d == 750000
        assert result.price_change_30d_pct == 5.2
        assert result.volatility_30d == 0.025


@pytest.mark.asyncio
class TestAPIEndpoints:
    """Test the FastAPI endpoints."""

    @patch("api.main.get_db")
    @patch("api.main.get_sql_query")
    async def test_health_check(self, mock_get_sql, mock_get_db):  # pylint: disable=unused-argument
        """Test the health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "magnificent-seven-stock-api"

    @patch("api.main.get_db")
    @patch("api.main.get_sql_query")
    async def test_top_performers_success(self, mock_get_sql, mock_get_db):
        """Test top performers endpoint with successful response."""
        # Mock database response
        mock_db = AsyncMock()
        mock_db.execute_query.return_value = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "price_usd": 150.25,
                "price_gbp": 120.50,
                "daily_return": 2.5,
                "volume": 1000000,
                "trade_date": date(2024, 1, 15),
                "performance_rank": 1,
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "price_usd": 350.00,
                "price_gbp": 280.00,
                "daily_return": 1.8,
                "volume": 500000,
                "trade_date": date(2024, 1, 15),
                "performance_rank": 2,
            },
        ]

        mock_get_db.return_value = mock_db
        mock_get_sql.return_value = "SELECT * FROM test;"

        client = TestClient(app)
        response = client.get("/api/stocks/top-performers")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["daily_return"] == 2.5
        assert data[1]["symbol"] == "MSFT"

    @patch("api.main.get_db")
    @patch("api.main.get_sql_query")
    async def test_top_performers_no_data(self, mock_get_sql, mock_get_db):
        """Test top performers endpoint with no data available."""
        mock_db = AsyncMock()
        mock_db.execute_query.return_value = []

        mock_get_db.return_value = mock_db
        mock_get_sql.return_value = "SELECT * FROM test;"

        client = TestClient(app)
        response = client.get("/api/stocks/top-performers")

        assert response.status_code == 404
        data = response.json()
        assert "No performance data available" in data["detail"]

    @patch("api.main.get_db")
    @patch("api.main.get_sql_query")
    async def test_performance_details_success(self, mock_get_sql, mock_get_db):
        """Test performance details endpoint with successful response."""
        mock_db = AsyncMock()
        mock_db.execute_query.return_value = [
            {
                "symbol": "NVDA",
                "company_name": "NVIDIA Corporation",
                "price_usd": 800.00,
                "price_gbp": 640.00,
                "daily_return": 3.2,
                "volume": 2000000,
                "trade_date": date(2024, 1, 15),
                "avg_price_30d_usd": 750.00,
                "avg_volume_30d": 1800000,
                "price_change_30d_pct": 6.7,
                "volatility_30d": 0.035,
                "performance_rank": 1,
            }
        ]

        mock_get_db.return_value = mock_db
        mock_get_sql.return_value = "SELECT * FROM test;"

        client = TestClient(app)
        response = client.get("/api/stocks/performance-details")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "NVDA"
        assert data[0]["avg_price_30d_usd"] == 750.00
        assert data[0]["volatility_30d"] == 0.035
