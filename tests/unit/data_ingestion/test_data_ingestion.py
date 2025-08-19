"""Tests for data ingestion functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from ticker_converter.data_ingestion.currency_fetcher import CurrencyDataFetcher
from ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher
from ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator


class TestNYSEDataFetcher:
    """Test NYSE data fetcher functionality."""

    def test_magnificent_seven_symbols(self) -> None:
        """Test that Magnificent Seven symbols are correctly defined."""
        fetcher = NYSEDataFetcher()
        expected_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
        assert fetcher.MAGNIFICENT_SEVEN == expected_symbols

    @patch("src.ticker_converter.data_ingestion.base_fetcher.AlphaVantageClient")
    def test_fetch_daily_data_success(self, mock_client_class: Mock) -> None:
        """Test successful daily data fetch."""
        # Mock API client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock data response
        mock_df = pd.DataFrame(
            {
                "Date": [datetime.now() - timedelta(days=1), datetime.now()],
                "Open": [150.0, 151.0],
                "High": [155.0, 156.0],
                "Low": [149.0, 150.0],
                "Close": [154.0, 155.0],
                "Volume": [1000000, 1100000],
                "Symbol": ["AAPL", "AAPL"],
            }
        )
        mock_client.get_daily_stock_data.return_value = mock_df

        fetcher = NYSEDataFetcher(mock_client)
        result = fetcher.fetch_daily_data("AAPL", days_back=2)

        assert result is not None
        assert len(result) == 2
        assert list(result.columns) == [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Symbol",
        ]

    def test_prepare_for_sql_insert(self) -> None:
        """Test data preparation for SQL insertion."""
        fetcher = NYSEDataFetcher()

        # Create test DataFrame
        test_df = pd.DataFrame(
            {
                "Date": [datetime(2025, 8, 11)],
                "Open": [150.0],
                "High": [155.0],
                "Low": [149.0],
                "Close": [154.0],
                "Volume": [1000000],
            }
        )

        records = fetcher.prepare_for_sql_insert(test_df, "AAPL")

        assert len(records) == 1
        record = records[0]
        assert record["symbol"] == "AAPL"
        assert record["open_price"] == 150.0
        assert record["high_price"] == 155.0
        assert record["low_price"] == 149.0
        assert record["close_price"] == 154.0
        assert record["volume"] == 1000000
        assert record["source"] == "alpha_vantage"


class TestCurrencyDataFetcher:
    """Test currency data fetcher functionality."""

    def test_currency_pair_configuration(self) -> None:
        """Test currency pair is correctly configured."""
        fetcher = CurrencyDataFetcher()
        assert fetcher.FROM_CURRENCY == "USD"
        assert fetcher.TO_CURRENCY == "GBP"

    @patch("src.ticker_converter.data_ingestion.base_fetcher.AlphaVantageClient")
    def test_fetch_current_exchange_rate_success(self, mock_client_class: Mock) -> None:
        """Test successful current exchange rate fetch."""
        # Mock API client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock exchange rate response
        mock_response = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "3. To_Currency Code": "GBP",
                "5. Exchange Rate": "0.7850",
                "6. Last Refreshed": "2025-08-11 16:00:00",
                "7. Time Zone": "UTC",
                "8. Bid Price": "0.7849",
                "9. Ask Price": "0.7851",
            }
        }
        mock_client.get_currency_exchange_rate.return_value = mock_response

        fetcher = CurrencyDataFetcher(mock_client)
        result = fetcher.fetch_current_exchange_rate()

        assert result is not None
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "GBP"
        assert result["exchange_rate"] == 0.7850

    def test_prepare_current_rate_for_sql(self) -> None:
        """Test current rate data preparation for SQL."""
        fetcher = CurrencyDataFetcher()

        rate_data = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "exchange_rate": 0.7850,
            "last_refreshed": "2025-08-11 16:00:00",
        }

        record = fetcher.prepare_current_rate_for_sql(rate_data)

        assert record is not None
        assert record["from_currency"] == "USD"
        assert record["to_currency"] == "GBP"
        assert record["exchange_rate"] == 0.7850
        assert record["source"] == "alpha_vantage"


class TestDataIngestionOrchestrator:
    """Test data ingestion orchestrator functionality."""

    def test_orchestrator_initialization(self) -> None:
        """Test orchestrator initializes with default components."""
        orchestrator = DataIngestionOrchestrator()

        assert orchestrator.db_manager is not None
        assert orchestrator.nyse_fetcher is not None
        assert orchestrator.currency_fetcher is not None

    @patch("src.ticker_converter.data_ingestion.orchestrator.DatabaseManager")
    def test_run_full_ingestion_empty_database(
        self, mock_db_manager_class: Mock
    ) -> None:
        """Test full ingestion with empty database performs initial setup."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_db_manager_class.return_value = mock_db_manager
        mock_db_manager.is_database_empty.return_value = True
        mock_db_manager.health_check.return_value = {
            "status": "healthy",
            "stock_records": 0,
            "currency_records": 0,
        }

        # Mock other components
        mock_nyse_fetcher = Mock()
        mock_currency_fetcher = Mock()

        orchestrator = DataIngestionOrchestrator(
            db_manager=mock_db_manager,
            nyse_fetcher=mock_nyse_fetcher,
            currency_fetcher=mock_currency_fetcher,
        )

        # Mock the perform_initial_setup method
        with patch.object(orchestrator, "perform_initial_setup") as mock_setup:
            mock_setup.return_value = {"success": True, "total_records_inserted": 100}

            result = orchestrator.run_full_ingestion()

            assert result["was_empty"] is True
            assert result["operation_performed"] == "initial_setup"
            mock_setup.assert_called_once_with(days_back=10)

    @patch("src.ticker_converter.data_ingestion.orchestrator.DatabaseManager")
    def test_run_full_ingestion_existing_data(
        self, mock_db_manager_class: Mock
    ) -> None:
        """Test full ingestion with existing data performs daily update."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_db_manager_class.return_value = mock_db_manager
        mock_db_manager.is_database_empty.return_value = False
        mock_db_manager.health_check.return_value = {
            "status": "healthy",
            "stock_records": 70,
            "currency_records": 10,
        }

        # Mock other components
        mock_nyse_fetcher = Mock()
        mock_currency_fetcher = Mock()

        orchestrator = DataIngestionOrchestrator(
            db_manager=mock_db_manager,
            nyse_fetcher=mock_nyse_fetcher,
            currency_fetcher=mock_currency_fetcher,
        )

        # Mock the perform_daily_update method
        with patch.object(orchestrator, "perform_daily_update") as mock_update:
            mock_update.return_value = {"success": True, "total_records_inserted": 10}

            result = orchestrator.run_full_ingestion()

            assert result["was_empty"] is False
            assert result["operation_performed"] == "daily_update"
            mock_update.assert_called_once()


@pytest.fixture
def sample_stock_data() -> pd.DataFrame:
    """Sample stock data for testing."""
    return pd.DataFrame(
        {
            "Date": [datetime(2025, 8, 10), datetime(2025, 8, 11)],
            "Open": [150.0, 151.0],
            "High": [155.0, 156.0],
            "Low": [149.0, 150.0],
            "Close": [154.0, 155.0],
            "Volume": [1000000, 1100000],
            "Symbol": ["AAPL", "AAPL"],
        }
    )


@pytest.fixture
def sample_currency_data() -> pd.DataFrame:
    """Sample currency data for testing."""
    return pd.DataFrame(
        {
            "Date": [datetime(2025, 8, 10), datetime(2025, 8, 11)],
            "Open": [0.7840, 0.7850],
            "High": [0.7860, 0.7870],
            "Low": [0.7830, 0.7840],
            "Close": [0.7850, 0.7860],
            "From_Symbol": ["USD", "USD"],
            "To_Symbol": ["GBP", "GBP"],
        }
    )


class TestIntegration:
    """Integration tests for data ingestion components."""

    def test_end_to_end_data_flow(
        self, sample_stock_data: pd.DataFrame, sample_currency_data: pd.DataFrame
    ) -> None:  # pylint: disable=redefined-outer-name
        """Test complete data flow from fetch to SQL preparation."""
        # Test NYSE fetcher
        nyse_fetcher = NYSEDataFetcher()
        stock_records = nyse_fetcher.prepare_for_sql_insert(sample_stock_data, "AAPL")

        assert len(stock_records) == 2
        assert all(record["symbol"] == "AAPL" for record in stock_records)

        # Test currency fetcher
        currency_fetcher = CurrencyDataFetcher()
        currency_records = currency_fetcher.prepare_for_sql_insert(sample_currency_data)

        assert len(currency_records) == 2
        assert all(record["from_currency"] == "USD" for record in currency_records)
        assert all(record["to_currency"] == "GBP" for record in currency_records)

    def test_magnificent_seven_coverage(self) -> None:
        """Test that we're covering all Magnificent Seven companies."""
        fetcher = NYSEDataFetcher()

        # Verify we have exactly 7 companies
        assert len(fetcher.MAGNIFICENT_SEVEN) == 7

        # Verify all expected companies are present
        expected_companies = {"AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"}
        actual_companies = set(fetcher.MAGNIFICENT_SEVEN)

        assert actual_companies == expected_companies

        # Verify no duplicates
        assert len(fetcher.MAGNIFICENT_SEVEN) == len(set(fetcher.MAGNIFICENT_SEVEN))
