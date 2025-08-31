"""Test-led development for USD/GBP stock data API endpoint.

This module implements test-driven development for a new API endpoint that provides
stock data with side-by-side USD and GBP price data based on the day's exchange rate.
"""

from datetime import date
from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.ticker_converter.api.dependencies import get_db, get_sql_query
from src.ticker_converter.api.main import app
from src.ticker_converter.api.models import StockDataWithCurrency


class TestStockDataWithCurrencyModel:
    """Test the StockDataWithCurrency model (to be implemented)."""

    def test_stock_data_with_currency_creation(self) -> None:
        """Test creating StockDataWithCurrency model with all fields."""
        stock_data = StockDataWithCurrency(
            symbol="AAPL",
            company_name="Apple Inc.",
            trade_date=date(2024, 1, 15),
            price_usd=150.25,
            price_gbp=120.50,
            usd_to_gbp_rate=0.8017,
            volume=1000000,
            daily_return=2.5,
            market_cap_usd=2500000000.0,
            market_cap_gbp=2003425000.0,
        )

        assert stock_data.symbol == "AAPL"
        assert stock_data.company_name == "Apple Inc."
        assert stock_data.trade_date == date(2024, 1, 15)
        assert stock_data.price_usd == 150.25
        assert stock_data.price_gbp == 120.50
        assert stock_data.usd_to_gbp_rate == 0.8017
        assert stock_data.volume == 1000000
        assert stock_data.daily_return == 2.5
        assert stock_data.market_cap_usd == 2500000000.0
        assert stock_data.market_cap_gbp == 2003425000.0

    def test_stock_data_with_currency_optional_fields(self) -> None:
        """Test creating StockDataWithCurrency model with optional fields as None."""
        stock_data = StockDataWithCurrency(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            trade_date=date(2024, 1, 15),
            price_usd=350.00,
            price_gbp=None,  # No GBP data available
            usd_to_gbp_rate=None,  # No exchange rate data
            volume=500000,
            daily_return=None,  # No return data
            market_cap_usd=None,  # No market cap data
            market_cap_gbp=None,
        )

        assert stock_data.symbol == "MSFT"
        assert stock_data.price_gbp is None
        assert stock_data.usd_to_gbp_rate is None
        assert stock_data.daily_return is None
        assert stock_data.market_cap_usd is None
        assert stock_data.market_cap_gbp is None

    def test_stock_data_with_currency_validation(self) -> None:
        """Test StockDataWithCurrency model field validation."""
        # Test that price_usd must be positive
        with pytest.raises(ValueError, match="price_usd must be positive"):
            StockDataWithCurrency(
                symbol="INVALID",
                company_name="Invalid Corp",
                trade_date=date(2024, 1, 15),
                price_usd=-10.0,  # Invalid negative price
                price_gbp=None,
                usd_to_gbp_rate=None,
                volume=1000,
                daily_return=None,
                market_cap_usd=None,
                market_cap_gbp=None,
            )

        # Test that volume must be non-negative
        with pytest.raises(ValueError, match="volume must be non-negative"):
            StockDataWithCurrency(
                symbol="INVALID",
                company_name="Invalid Corp",
                trade_date=date(2024, 1, 15),
                price_usd=100.0,
                price_gbp=None,
                usd_to_gbp_rate=None,
                volume=-1000,  # Invalid negative volume
                daily_return=None,
                market_cap_usd=None,
                market_cap_gbp=None,
            )


class TestStockDataModelBuilder:
    """Test the model builder function for StockDataWithCurrency (to be implemented)."""

    def test_build_stock_data_with_currency_complete_data(self) -> None:
        """Test building StockDataWithCurrency from complete database row."""
        from src.ticker_converter.api.main import _build_stock_data_with_currency

        row = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "trade_date": date(2024, 1, 15),
            "price_usd": 150.25,
            "price_gbp": 120.50,
            "usd_to_gbp_rate": 0.8017,
            "volume": 1000000,
            "daily_return": 2.5,
            "market_cap_usd": 2500000000.0,
            "market_cap_gbp": 2003425000.0,
        }

        result = _build_stock_data_with_currency(row)

        assert isinstance(result, StockDataWithCurrency)
        assert result.symbol == "AAPL"
        assert result.company_name == "Apple Inc."
        assert result.price_usd == 150.25
        assert result.price_gbp == 120.50
        assert result.usd_to_gbp_rate == 0.8017
        assert result.market_cap_gbp == 2003425000.0

    def test_build_stock_data_with_currency_missing_optional_data(self) -> None:
        """Test building StockDataWithCurrency with missing optional fields."""
        from src.ticker_converter.api.main import _build_stock_data_with_currency

        row = {
            "symbol": "GOOGL",
            "company_name": "Alphabet Inc.",
            "trade_date": date(2024, 1, 15),
            "price_usd": 2500.00,
            "price_gbp": None,
            "usd_to_gbp_rate": None,
            "volume": 800000,
            "daily_return": None,
            "market_cap_usd": None,
            "market_cap_gbp": None,
        }

        result = _build_stock_data_with_currency(row)

        assert result.symbol == "GOOGL"
        assert result.price_gbp is None
        assert result.usd_to_gbp_rate is None
        assert result.daily_return is None
        assert result.market_cap_usd is None
        assert result.market_cap_gbp is None


@pytest.mark.asyncio
class TestStockDataEndpoint:
    """Test the stock data with currency API endpoint (to be implemented)."""

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
            if filename == "stock_data_with_currency.sql":
                return """
                SELECT
                    ds.symbol,
                    ds.company_name,
                    dd.date_value AS trade_date,
                    fsp.closing_price AS price_usd,
                    ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, NULL), 4) AS price_gbp,
                    fcr.exchange_rate AS usd_to_gbp_rate,
                    fsp.volume,
                    fsp.daily_return,
                    fsp.closing_price * fsp.shares_outstanding AS market_cap_usd,
                    (fsp.closing_price * fsp.shares_outstanding * COALESCE(fcr.exchange_rate, NULL)) AS market_cap_gbp
                FROM fact_stock_prices fsp
                INNER JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
                INNER JOIN dim_date dd ON fsp.date_id = dd.date_id
                LEFT JOIN fact_currency_rates fcr ON dd.date_id = fcr.date_id
                WHERE ds.is_active = TRUE
                AND ($1 IS NULL OR ds.symbol = $1)
                AND ($2 IS NULL OR dd.date_value = $2)
                ORDER BY dd.date_value DESC, ds.symbol;
                """
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

    async def test_get_stock_data_with_currency_all_stocks(self) -> None:
        """Test endpoint returns all stocks with USD/GBP data."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response with multiple stocks
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "trade_date": date(2024, 1, 15),
                "price_usd": 150.25,
                "price_gbp": 120.50,
                "usd_to_gbp_rate": 0.8017,
                "volume": 1000000,
                "daily_return": 2.5,
                "market_cap_usd": 2500000000.0,
                "market_cap_gbp": 2003425000.0,
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "trade_date": date(2024, 1, 15),
                "price_usd": 350.00,
                "price_gbp": 280.60,
                "usd_to_gbp_rate": 0.8017,
                "volume": 500000,
                "daily_return": 1.8,
                "market_cap_usd": 3000000000.0,
                "market_cap_gbp": 2405100000.0,
            },
        ]

        response = self.client.get("/api/stocks/data-with-currency")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check first stock (AAPL)
        aapl_data = data[0]
        assert aapl_data["symbol"] == "AAPL"
        assert aapl_data["price_usd"] == 150.25
        assert aapl_data["price_gbp"] == 120.50
        assert aapl_data["usd_to_gbp_rate"] == 0.8017
        assert aapl_data["market_cap_usd"] == 2500000000.0

        # Check second stock (MSFT)
        msft_data = data[1]
        assert msft_data["symbol"] == "MSFT"
        assert msft_data["price_usd"] == 350.00
        assert msft_data["price_gbp"] == 280.60

    async def test_get_stock_data_with_currency_specific_symbol(self) -> None:
        """Test endpoint with specific symbol parameter."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response for specific symbol
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "NVDA",
                "company_name": "NVIDIA Corporation",
                "trade_date": date(2024, 1, 15),
                "price_usd": 800.00,
                "price_gbp": 641.36,
                "usd_to_gbp_rate": 0.8017,
                "volume": 2000000,
                "daily_return": 3.2,
                "market_cap_usd": 2000000000.0,
                "market_cap_gbp": 1603400000.0,
            }
        ]

        response = self.client.get("/api/stocks/data-with-currency?symbol=NVDA")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "NVDA"
        assert data[0]["company_name"] == "NVIDIA Corporation"
        assert data[0]["price_usd"] == 800.00
        assert data[0]["price_gbp"] == 641.36

    async def test_get_stock_data_with_currency_specific_date(self) -> None:
        """Test endpoint with specific date parameter."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response for specific date
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "TSLA",
                "company_name": "Tesla Inc.",
                "trade_date": date(2024, 1, 10),
                "price_usd": 250.00,
                "price_gbp": 200.43,
                "usd_to_gbp_rate": 0.8017,
                "volume": 1500000,
                "daily_return": -1.2,
                "market_cap_usd": 800000000.0,
                "market_cap_gbp": 641360000.0,
            }
        ]

        response = self.client.get("/api/stocks/data-with-currency?date=2024-01-10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "TSLA"
        assert data[0]["trade_date"] == "2024-01-10"
        assert data[0]["daily_return"] == -1.2

    async def test_get_stock_data_with_currency_no_data(self) -> None:
        """Test endpoint when no data is available."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock empty database response
        self.mock_db.execute_query.return_value = []

        response = self.client.get("/api/stocks/data-with-currency")

        assert response.status_code == 404
        data = response.json()
        assert "No stock data available" in data["detail"]

    async def test_get_stock_data_with_currency_missing_exchange_rate(self) -> None:
        """Test endpoint with missing exchange rate data."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response with missing exchange rate
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "META",
                "company_name": "Meta Platforms Inc.",
                "trade_date": date(2024, 1, 15),
                "price_usd": 400.00,
                "price_gbp": None,  # No GBP price due to missing rate
                "usd_to_gbp_rate": None,  # No exchange rate available
                "volume": 750000,
                "daily_return": 0.8,
                "market_cap_usd": 1000000000.0,
                "market_cap_gbp": None,  # No GBP market cap
            }
        ]

        response = self.client.get("/api/stocks/data-with-currency")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "META"
        assert data[0]["price_usd"] == 400.00
        assert data[0]["price_gbp"] is None
        assert data[0]["usd_to_gbp_rate"] is None
        assert data[0]["market_cap_gbp"] is None

    async def test_get_stock_data_with_currency_database_error(self) -> None:
        """Test endpoint when database query fails."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database error
        self.mock_db.execute_query.side_effect = Exception("Database connection failed")

        response = self.client.get("/api/stocks/data-with-currency")

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]

    async def test_get_stock_data_with_currency_symbol_and_date(self) -> None:
        """Test endpoint with both symbol and date parameters."""
        assert self.mock_db is not None
        assert self.client is not None

        # Mock database response for specific symbol and date
        self.mock_db.execute_query.return_value = [
            {
                "symbol": "AMZN",
                "company_name": "Amazon.com Inc.",
                "trade_date": date(2024, 1, 12),
                "price_usd": 3000.00,
                "price_gbp": 2405.10,
                "usd_to_gbp_rate": 0.8017,
                "volume": 900000,
                "daily_return": 4.1,
                "market_cap_usd": 1500000000.0,
                "market_cap_gbp": 1202550000.0,
            }
        ]

        response = self.client.get("/api/stocks/data-with-currency?symbol=AMZN&date=2024-01-12")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AMZN"
        assert data[0]["trade_date"] == "2024-01-12"
        assert data[0]["daily_return"] == 4.1
        assert data[0]["market_cap_usd"] == 1500000000.0

    async def test_get_stock_data_with_currency_invalid_date_format(self) -> None:
        """Test endpoint with invalid date format."""
        assert self.client is not None

        response = self.client.get("/api/stocks/data-with-currency?date=invalid-date")

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


class TestStockDataSQL:
    """Test the SQL query for stock data with currency conversion."""

    def test_stock_data_with_currency_sql_structure(self) -> None:
        """Test that the SQL query has the correct structure."""
        from src.ticker_converter.api.dependencies import get_sql_query

        sql = get_sql_query("stock_data_with_currency.sql")

        # Check that the query contains essential elements
        assert "SELECT" in sql.upper()
        assert "fact_stock_prices" in sql
        assert "fact_currency_rates" in sql
        assert "dim_stocks" in sql
        assert "dim_date" in sql
        assert "closing_price" in sql
        assert "exchange_rate" in sql
        assert "price_usd" in sql
        assert "price_gbp" in sql

    def test_stock_data_with_currency_sql_parameters(self) -> None:
        """Test that the SQL query uses parameterized inputs."""
        from src.ticker_converter.api.dependencies import get_sql_query

        sql = get_sql_query("stock_data_with_currency.sql")

        # Check for parameter placeholders
        assert "$1" in sql  # Symbol parameter
        assert "$2" in sql  # Date parameter

    def test_stock_data_with_currency_sql_joins(self) -> None:
        """Test that the SQL query has proper joins."""
        from src.ticker_converter.api.dependencies import get_sql_query

        sql = get_sql_query("stock_data_with_currency.sql")

        # Check for proper joins
        assert "INNER JOIN dim_stocks" in sql
        assert "INNER JOIN dim_date" in sql
        assert "LEFT JOIN fact_currency_rates" in sql  # Left join for optional currency data

    def test_stock_data_with_currency_sql_currency_handling(self) -> None:
        """Test that the SQL query properly handles currency conversion."""
        from src.ticker_converter.api.dependencies import get_sql_query

        sql = get_sql_query("stock_data_with_currency.sql")

        # Check for currency conversion logic
        assert "COALESCE" in sql  # Handles null exchange rates
        assert "exchange_rate" in sql
        assert "closing_price *" in sql  # Price conversion calculation
