"""Integration tests for USD/GBP stock data API endpoint.

This module implements real integration testing for the new API endpoint that provides
stock data with side-by-side USD and GBP price data based on the day's exchange rate.
Tests use real PostgreSQL database connections and verify end-to-end functionality.
"""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import psycopg2
import pytest
from fastapi.testclient import TestClient
from psycopg2 import sql

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

from src.ticker_converter.api.main import app
from src.ticker_converter.api.models import StockDataWithCurrency

# Load database configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


class TestStockDataWithCurrencyModel:
    """Test the StockDataWithCurrency model validation."""

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
    """Test the model builder function for StockDataWithCurrency."""

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


@pytest.mark.integration
class TestStockDataEndpointIntegration:
    """Integration tests for the stock data with currency API endpoint.

    These tests require a running PostgreSQL database and will insert/query real data.
    """

    @classmethod
    def setup_class(cls) -> None:
        """Set up test class with database connection."""
        cls.test_date = date.today()
        cls.test_symbols = ["AAPL", "MSFT", "GOOGL"]
        cls.test_exchange_rate = 0.8017

    def _get_db_connection(self) -> psycopg2.extensions.connection:
        """Get a database connection for testing."""
        return psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

    def _insert_test_currencies(self, conn: psycopg2.extensions.connection) -> tuple[int, int]:
        """Insert test currency data and return currency IDs."""
        with conn.cursor() as cur:
            # Insert USD currency
            cur.execute(
                """
                INSERT INTO dim_currency (currency_code, currency_name) 
                VALUES ('USD', 'US Dollar') 
                ON CONFLICT (currency_code) DO UPDATE SET currency_name = EXCLUDED.currency_name
                RETURNING currency_id;
            """
            )
            usd_id = cur.fetchone()[0]

            # Insert GBP currency
            cur.execute(
                """
                INSERT INTO dim_currency (currency_code, currency_name) 
                VALUES ('GBP', 'British Pound') 
                ON CONFLICT (currency_code) DO UPDATE SET currency_name = EXCLUDED.currency_name
                RETURNING currency_id;
            """
            )
            gbp_id = cur.fetchone()[0]

        conn.commit()
        return usd_id, gbp_id

    def _insert_test_date(self, conn: psycopg2.extensions.connection, test_date: date) -> int:
        """Insert test date and return date ID."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dim_date (date_value, year, month, day, quarter, day_of_week) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON CONFLICT (date_value) DO UPDATE SET year = EXCLUDED.year
                RETURNING date_id;
            """,
                (
                    test_date,
                    test_date.year,
                    test_date.month,
                    test_date.day,
                    (test_date.month - 1) // 3 + 1,
                    test_date.weekday() + 1,
                ),
            )
            date_id = cur.fetchone()[0]

        conn.commit()
        return date_id

    def _insert_test_stocks(self, conn: psycopg2.extensions.connection) -> dict[str, int]:
        """Insert test stock data and return stock IDs."""
        stock_data = {
            "AAPL": ("Apple Inc.", "Technology"),
            "MSFT": ("Microsoft Corporation", "Technology"),
            "GOOGL": ("Alphabet Inc.", "Technology"),
        }

        stock_ids = {}
        with conn.cursor() as cur:
            for symbol, (company_name, sector) in stock_data.items():
                cur.execute(
                    """
                    INSERT INTO dim_stocks (symbol, company_name, sector, is_active) 
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (symbol) DO UPDATE SET company_name = EXCLUDED.company_name
                    RETURNING stock_id;
                """,
                    (symbol, company_name, sector, True),
                )
                stock_ids[symbol] = cur.fetchone()[0]

        conn.commit()
        return stock_ids

    def _insert_test_exchange_rates(
        self, conn: psycopg2.extensions.connection, date_id: int, usd_id: int, gbp_id: int
    ) -> None:
        """Insert test exchange rate data."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fact_currency_rates (date_id, from_currency_id, to_currency_id, exchange_rate) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (date_id, from_currency_id, to_currency_id) 
                DO UPDATE SET exchange_rate = EXCLUDED.exchange_rate;
            """,
                (date_id, usd_id, gbp_id, self.test_exchange_rate),
            )

        conn.commit()

    def _insert_test_stock_prices(
        self, conn: psycopg2.extensions.connection, date_id: int, stock_ids: dict[str, int]
    ) -> None:
        """Insert test stock price data."""
        price_data = {
            "AAPL": {"price": 150.25, "volume": 1000000, "daily_return": 2.5},
            "MSFT": {"price": 350.00, "volume": 500000, "daily_return": 1.8},
            "GOOGL": {"price": 2500.00, "volume": 800000, "daily_return": 3.2},
        }

        with conn.cursor() as cur:
            for symbol, data in price_data.items():
                cur.execute(
                    """
                    INSERT INTO fact_stock_prices (date_id, stock_id, closing_price, volume, daily_return) 
                    VALUES (%s, %s, %s, %s, %s) 
                    ON CONFLICT (date_id, stock_id) 
                    DO UPDATE SET 
                        closing_price = EXCLUDED.closing_price,
                        volume = EXCLUDED.volume,
                        daily_return = EXCLUDED.daily_return;
                """,
                    (date_id, stock_ids[symbol], data["price"], data["volume"], data["daily_return"]),
                )

        conn.commit()

    def _setup_test_data(self) -> None:
        """Set up comprehensive test data in the database."""
        conn = self._get_db_connection()
        try:
            # Insert all test data
            usd_id, gbp_id = self._insert_test_currencies(conn)
            date_id = self._insert_test_date(conn, self.test_date)
            stock_ids = self._insert_test_stocks(conn)
            self._insert_test_exchange_rates(conn, date_id, usd_id, gbp_id)
            self._insert_test_stock_prices(conn, date_id, stock_ids)

        finally:
            conn.close()

    def _cleanup_test_data(self) -> None:
        """Clean up test data from the database."""
        conn = self._get_db_connection()
        try:
            with conn.cursor() as cur:
                # Clean up in reverse order of dependencies
                cur.execute(
                    "DELETE FROM fact_stock_prices WHERE date_id IN (SELECT date_id FROM dim_date WHERE date_value = %s);",
                    (self.test_date,),
                )
                cur.execute(
                    "DELETE FROM fact_currency_rates WHERE date_id IN (SELECT date_id FROM dim_date WHERE date_value = %s);",
                    (self.test_date,),
                )
                cur.execute("DELETE FROM dim_date WHERE date_value = %s;", (self.test_date,))
                # Note: Not deleting stocks and currencies as they might be used by other tests

            conn.commit()
        finally:
            conn.close()

    def test_database_environment_setup(self) -> None:
        """Test that database environment variables are properly configured."""
        required_vars = {
            "POSTGRES_HOST": POSTGRES_HOST,
            "POSTGRES_PORT": POSTGRES_PORT,
            "POSTGRES_DB": POSTGRES_DB,
            "POSTGRES_USER": POSTGRES_USER,
            "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
        }

        for var_name, var_value in required_vars.items():
            assert var_value is not None, f"{var_name} must be set in environment"
            assert var_value != "", f"{var_name} cannot be empty"

    def test_database_connectivity(self) -> None:
        """Test that we can connect to the PostgreSQL database."""
        conn = self._get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                assert result[0] == 1
        finally:
            conn.close()

    def test_database_schema_exists(self) -> None:
        """Test that required database tables exist."""
        required_tables = ["dim_currency", "dim_date", "dim_stocks", "fact_currency_rates", "fact_stock_prices"]

        conn = self._get_db_connection()
        try:
            with conn.cursor() as cur:
                for table in required_tables:
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        );
                    """,
                        (table,),
                    )
                    exists = cur.fetchone()[0]
                    assert exists, f"Required table {table} does not exist"
        finally:
            conn.close()

    def test_endpoint_with_real_database_all_stocks(self) -> None:
        """Test endpoint returns real data from database for all stocks."""
        # Setup test data
        self._setup_test_data()

        try:
            client = TestClient(app)
            response = client.get("/api/stocks/data-with-currency")

            assert response.status_code == 200
            data = response.json()

            # Should have at least our test data
            assert len(data) >= 3, f"Expected at least 3 stocks, got {len(data)}"

            # Verify test stocks are present
            symbols_found = {item["symbol"] for item in data}
            for test_symbol in self.test_symbols:
                assert test_symbol in symbols_found, f"Test symbol {test_symbol} not found in response"

            # Verify data structure for first stock
            first_stock = data[0]
            required_fields = [
                "symbol",
                "company_name",
                "trade_date",
                "price_usd",
                "price_gbp",
                "usd_to_gbp_rate",
                "volume",
                "daily_return",
            ]
            for field in required_fields:
                assert field in first_stock, f"Required field {field} missing from response"

            # Verify currency conversion logic worked
            aapl_data = next((item for item in data if item["symbol"] == "AAPL"), None)
            if aapl_data and aapl_data["price_gbp"] and aapl_data["usd_to_gbp_rate"]:
                expected_gbp = round(aapl_data["price_usd"] * aapl_data["usd_to_gbp_rate"], 4)
                assert abs(aapl_data["price_gbp"] - expected_gbp) < 0.01, "Currency conversion calculation incorrect"

        finally:
            self._cleanup_test_data()

    def test_endpoint_with_real_database_specific_symbol(self) -> None:
        """Test endpoint returns real data for specific symbol filter."""
        self._setup_test_data()

        try:
            client = TestClient(app)
            response = client.get("/api/stocks/data-with-currency?symbol=AAPL")

            assert response.status_code == 200
            data = response.json()

            # Should return only AAPL data
            assert len(data) >= 1, "Should return at least one record for AAPL"

            for item in data:
                assert item["symbol"] == "AAPL", f"Expected only AAPL, got {item['symbol']}"
                assert item["company_name"] == "Apple Inc."
                assert item["price_usd"] == 150.25
                assert item["volume"] == 1000000

        finally:
            self._cleanup_test_data()

    def test_endpoint_with_real_database_specific_date(self) -> None:
        """Test endpoint returns real data for specific date filter."""
        self._setup_test_data()

        try:
            client = TestClient(app)
            response = client.get(f"/api/stocks/data-with-currency?date={self.test_date}")

            assert response.status_code == 200
            data = response.json()

            # Should return data for our test date
            assert len(data) >= 3, f"Expected at least 3 stocks for {self.test_date}, got {len(data)}"

            for item in data:
                assert item["trade_date"] == str(
                    self.test_date
                ), f"Expected date {self.test_date}, got {item['trade_date']}"

        finally:
            self._cleanup_test_data()

    def test_endpoint_data_freshness_check(self) -> None:
        """Test that the endpoint returns the most recent data when no date filter is specified."""
        # Setup data for multiple dates
        self._setup_test_data()

        # Add data for yesterday
        yesterday = self.test_date - timedelta(days=1)
        conn = self._get_db_connection()
        try:
            usd_id, gbp_id = self._insert_test_currencies(conn)
            yesterday_date_id = self._insert_test_date(conn, yesterday)
            stock_ids = self._insert_test_stocks(conn)
            self._insert_test_exchange_rates(conn, yesterday_date_id, usd_id, gbp_id)

            # Insert older stock prices with different values
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO fact_stock_prices (date_id, stock_id, closing_price, volume, daily_return) 
                    VALUES (%s, %s, %s, %s, %s) 
                    ON CONFLICT (date_id, stock_id) 
                    DO UPDATE SET closing_price = EXCLUDED.closing_price;
                """,
                    (yesterday_date_id, stock_ids["AAPL"], 140.00, 900000, 1.5),
                )  # Different price
            conn.commit()

        finally:
            conn.close()

        try:
            client = TestClient(app)
            response = client.get("/api/stocks/data-with-currency")

            assert response.status_code == 200
            data = response.json()

            # Verify we get the most recent data (today's data should come first due to ORDER BY date DESC)
            aapl_data = next((item for item in data if item["symbol"] == "AAPL"), None)
            assert aapl_data is not None, "AAPL data should be present"

            # Should be today's price (150.25), not yesterday's (140.00)
            assert aapl_data["price_usd"] == 150.25, f"Expected today's price 150.25, got {aapl_data['price_usd']}"
            assert aapl_data["trade_date"] == str(
                self.test_date
            ), f"Expected today's date {self.test_date}, got {aapl_data['trade_date']}"

        finally:
            # Cleanup both dates
            self._cleanup_test_data()
            conn = self._get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM fact_stock_prices WHERE date_id IN (SELECT date_id FROM dim_date WHERE date_value = %s);",
                        (yesterday,),
                    )
                    cur.execute(
                        "DELETE FROM fact_currency_rates WHERE date_id IN (SELECT date_id FROM dim_date WHERE date_value = %s);",
                        (yesterday,),
                    )
                    cur.execute("DELETE FROM dim_date WHERE date_value = %s;", (yesterday,))
                conn.commit()
            finally:
                conn.close()

    def test_endpoint_with_missing_exchange_rate_data(self) -> None:
        """Test endpoint handles missing exchange rate data gracefully."""
        # Setup data without exchange rates
        conn = self._get_db_connection()
        try:
            usd_id, gbp_id = self._insert_test_currencies(conn)
            date_id = self._insert_test_date(conn, self.test_date)
            stock_ids = self._insert_test_stocks(conn)
            # Note: NOT inserting exchange rates
            self._insert_test_stock_prices(conn, date_id, stock_ids)

        finally:
            conn.close()

        try:
            client = TestClient(app)
            response = client.get("/api/stocks/data-with-currency")

            assert response.status_code == 200
            data = response.json()

            # Should still return data but with null GBP values
            assert len(data) >= 3, f"Expected at least 3 stocks, got {len(data)}"

            aapl_data = next((item for item in data if item["symbol"] == "AAPL"), None)
            assert aapl_data is not None, "AAPL data should be present"
            assert aapl_data["price_usd"] == 150.25, "USD price should be present"
            assert aapl_data["price_gbp"] is None, "GBP price should be null when no exchange rate"
            assert aapl_data["usd_to_gbp_rate"] is None, "Exchange rate should be null"

        finally:
            self._cleanup_test_data()


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
