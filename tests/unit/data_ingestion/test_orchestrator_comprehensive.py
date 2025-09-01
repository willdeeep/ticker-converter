"""Comprehensive tests for DataIngestionOrchestrator module.

This module provides comprehensive testing for the data ingestion orchestration functionality,
covering initialization, setup operations, daily updates, full ingestion workflow, and status checking.
"""

from datetime import date
from unittest.mock import Mock, patch

# pylint: disable=import-error  # Test environment import resolution
from src.ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator


class TestDataIngestionOrchestratorInitialization:
    """Test DataIngestionOrchestrator initialization and configuration."""

    def test_init_with_default_components(self) -> None:
        """Test initialization with default component instances."""
        with (
            patch("src.ticker_converter.data_ingestion.orchestrator.DatabaseManager") as mock_db_cls,
            patch("src.ticker_converter.data_ingestion.orchestrator.NYSEDataFetcher") as mock_nyse_cls,
            patch("src.ticker_converter.data_ingestion.orchestrator.CurrencyDataFetcher") as mock_currency_cls,
        ):

            orchestrator = DataIngestionOrchestrator()

            # Verify default instances are created
            mock_db_cls.assert_called_once_with()
            mock_nyse_cls.assert_called_once_with()
            mock_currency_cls.assert_called_once_with()

            assert orchestrator.db_manager is not None
            assert orchestrator.nyse_fetcher is not None
            assert orchestrator.currency_fetcher is not None
            assert orchestrator.logger.name == "src.ticker_converter.data_ingestion.orchestrator"

    def test_init_with_provided_components(self) -> None:
        """Test initialization with provided component instances."""
        mock_db = Mock()
        mock_nyse = Mock()
        mock_currency = Mock()

        orchestrator = DataIngestionOrchestrator(
            db_manager=mock_db, nyse_fetcher=mock_nyse, currency_fetcher=mock_currency
        )

        assert orchestrator.db_manager is mock_db
        assert orchestrator.nyse_fetcher is mock_nyse
        assert orchestrator.currency_fetcher is mock_currency

    def test_init_with_mixed_components(self) -> None:
        """Test initialization with some provided and some default components."""
        mock_db = Mock()

        with (
            patch("src.ticker_converter.data_ingestion.orchestrator.NYSEDataFetcher") as mock_nyse_cls,
            patch("src.ticker_converter.data_ingestion.orchestrator.CurrencyDataFetcher") as mock_currency_cls,
        ):

            orchestrator = DataIngestionOrchestrator(db_manager=mock_db)

            assert orchestrator.db_manager is mock_db
            mock_nyse_cls.assert_called_once_with()
            mock_currency_cls.assert_called_once_with()


class TestDataIngestionOrchestratorInitialSetup:
    """Test DataIngestionOrchestrator initial setup functionality."""

    # pylint: disable=protected-access  # Testing private methods for comprehensive coverage

    # Declare attributes that will be set in setup_method
    mock_db: Mock
    mock_nyse: Mock
    mock_currency: Mock
    orchestrator: DataIngestionOrchestrator

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()
        self.orchestrator = DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def test_perform_initial_setup_success(self) -> None:
        """Test successful initial setup with all data."""
        # Mock successful data fetching
        stock_data = [
            {"symbol": "AAPL", "date": "2025-08-17", "close": 150.00},
            {"symbol": "MSFT", "date": "2025-08-17", "close": 350.00},
        ]
        currency_data = [{"date": "2025-08-17", "rate": 0.78}]

        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_stock_data.return_value = 2
        self.mock_db.insert_currency_data.return_value = 1
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"

        result = self.orchestrator.perform_initial_setup(days_back=10)

        # Verify API calls
        self.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=10)
        self.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=10)
        self.mock_db.insert_stock_data.assert_called_once_with(stock_data)
        self.mock_db.insert_currency_data.assert_called_once_with(currency_data)

        # Verify result structure
        assert "setup_started" in result
        assert "setup_completed" in result
        assert result["days_requested"] == 10
        assert result["total_records_inserted"] == 3  # Stock data (2) + Currency data (1) = 3
        assert result["stock_data"]["records_fetched"] == 2
        assert result["stock_data"]["records_inserted"] == 2
        assert result["currency_data"]["records_fetched"] == 1
        assert result["currency_data"]["records_inserted"] == 1
        assert len(result["errors"]) == 0

    def test_perform_initial_setup_stock_data_failure(self) -> None:
        """Test initial setup when stock data fetching fails."""
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None
        self.mock_currency.fetch_and_prepare_fx_data.return_value = [{"date": "2025-08-17", "rate": 0.78}]
        self.mock_db.insert_currency_data.return_value = 1

        result = self.orchestrator.perform_initial_setup(days_back=5)

        # Verify stock data error is recorded
        assert any("Failed to fetch stock data" in error for error in result["errors"])
        assert result["total_records_inserted"] == 1  # Only currency data

        # Verify currency data still processed
        self.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=5)
        self.mock_db.insert_currency_data.assert_called_once()

    def test_perform_initial_setup_currency_data_failure(self) -> None:
        """Test initial setup when currency data fetching fails."""
        stock_data = [{"symbol": "AAPL", "date": "2025-08-17", "close": 150.00}]
        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = None
        self.mock_db.insert_stock_data.return_value = 1
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]

        result = self.orchestrator.perform_initial_setup(days_back=7)

        # Verify currency data error is recorded
        assert any("Failed to fetch currency data" in error for error in result["errors"])
        assert result["total_records_inserted"] == 1  # Only stock data

        # Verify stock data still processed
        self.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=7)
        self.mock_db.insert_stock_data.assert_called_once_with(stock_data)

    def test_perform_initial_setup_complete_failure(self) -> None:
        """Test initial setup when both data sources fail."""
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None
        self.mock_currency.fetch_and_prepare_fx_data.return_value = None

        result = self.orchestrator.perform_initial_setup(days_back=3)

        # Verify currency data error is recorded (stock error gets overwritten by currency result)
        assert len(result["errors"]) == 1
        assert any("Failed to fetch currency data" in error for error in result["errors"])
        assert result["total_records_inserted"] == 0

    def test_perform_initial_setup_unexpected_exception(self) -> None:
        """Test initial setup handling data processing exceptions."""
        self.mock_nyse.fetch_and_prepare_all_data.side_effect = ValueError("API connection failed")

        result = self.orchestrator.perform_initial_setup(days_back=5)

        # Verify exception is handled and recorded as data processing error
        assert any("Data processing error" in error for error in result["errors"])
        assert any("API connection failed" in error for error in result["errors"])
        assert result["total_records_inserted"] == 0

    def test_create_base_result(self) -> None:
        """Test creation of base result dictionary."""
        with patch("src.ticker_converter.data_ingestion.orchestrator.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2025-08-17T10:30:00"

            result = self.orchestrator._create_base_result(15)

            assert result["setup_started"] == "2025-08-17T10:30:00"
            assert result["days_requested"] == 15
            assert not result["stock_data"]
            assert not result["currency_data"]
            assert result["total_records_inserted"] == 0
            assert not result["errors"]

    def test_process_stock_data_success(self) -> None:
        """Test successful stock data processing."""
        stock_data = [
            {"symbol": "AAPL", "date": "2025-08-17", "close": 150.00},
            {"symbol": "MSFT", "date": "2025-08-17", "close": 350.00},
        ]
        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_db.insert_stock_data.return_value = 2
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]

        result = self.orchestrator._process_stock_data(days_back=5)

        assert "errors" not in result or len(result["errors"]) == 0
        assert result["stock_data"]["records_fetched"] == 2
        assert result["stock_data"]["records_inserted"] == 2
        assert result["stock_data"]["companies"] == [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        assert result["total_records_inserted"] == 2

    def test_process_stock_data_failure(self) -> None:
        """Test stock data processing failure."""
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None

        result = self.orchestrator._process_stock_data(days_back=5)

        assert len(result["errors"]) == 1
        assert "Failed to fetch stock data" in result["errors"][0]
        assert result["total_records_inserted"] == 0

    def test_process_currency_data_success(self) -> None:
        """Test successful currency data processing."""
        currency_data = [{"date": "2025-08-17", "rate": 0.78}]
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_currency_data.return_value = 1
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"

        result = self.orchestrator._process_currency_data(days_back=5)

        assert "errors" not in result or len(result["errors"]) == 0
        assert result["currency_data"]["records_fetched"] == 1
        assert result["currency_data"]["records_inserted"] == 1
        assert result["currency_data"]["currency_pair"] == "USD/GBP"
        assert result["total_records_inserted"] == 1

    def test_process_currency_data_failure(self) -> None:
        """Test currency data processing failure."""
        self.mock_currency.fetch_and_prepare_fx_data.return_value = None

        result = self.orchestrator._process_currency_data(days_back=5)

        assert len(result["errors"]) == 1
        assert "Failed to fetch currency data" in result["errors"][0]


class TestDataIngestionOrchestratorDailyUpdate:
    """Test DataIngestionOrchestrator daily update functionality."""

    # Declare attributes that will be set in setup_method
    mock_db: Mock
    mock_nyse: Mock
    mock_currency: Mock
    orchestrator: DataIngestionOrchestrator

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()
        self.orchestrator = DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def test_perform_daily_update_success(self) -> None:
        """Test successful daily update with all data."""
        # Mock successful data fetching
        stock_data = [
            {"symbol": "AAPL", "date": "2025-08-17", "close": 151.00},
            {"symbol": "MSFT", "date": "2025-08-17", "close": 351.00},
            {"symbol": "GOOGL", "date": "2025-08-17", "close": 135.00},
        ]
        currency_data = [{"date": "2025-08-17", "rate": 0.785}]

        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_stock_data.return_value = 3
        self.mock_db.insert_currency_data.return_value = 1

        result = self.orchestrator.perform_daily_update()

        # Verify API calls with 3-day lookback
        self.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=3)
        self.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=3)
        self.mock_db.insert_stock_data.assert_called_once_with(stock_data)
        self.mock_db.insert_currency_data.assert_called_once_with(currency_data)

        # Verify result structure
        assert "update_started" in result
        assert "update_completed" in result
        assert result["success"] is True
        assert result["total_records_inserted"] == 4
        assert result["stock_updates"]["records_fetched"] == 3
        assert result["stock_updates"]["records_inserted"] == 3
        assert result["stock_updates"]["companies_updated"] == 3  # AAPL, MSFT, GOOGL
        assert result["currency_updates"]["records_fetched"] == 1
        assert result["currency_updates"]["records_inserted"] == 1
        assert len(result["errors"]) == 0

    def test_perform_daily_update_no_stock_data(self) -> None:
        """Test daily update when no stock data is available."""
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None
        currency_data = [{"date": "2025-08-17", "rate": 0.785}]
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_currency_data.return_value = 1

        result = self.orchestrator.perform_daily_update()

        # Verify currency data still processed
        assert result["total_records_inserted"] == 1
        assert "stock_updates" not in result or not result["stock_updates"]
        assert result["currency_updates"]["records_inserted"] == 1
        assert result["success"] is True

    def test_perform_daily_update_no_currency_data(self) -> None:
        """Test daily update when no currency data is available."""
        stock_data = [{"symbol": "AAPL", "date": "2025-08-17", "close": 151.00}]
        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = None
        self.mock_db.insert_stock_data.return_value = 1

        result = self.orchestrator.perform_daily_update()

        # Verify stock data still processed
        assert result["total_records_inserted"] == 1
        assert result["stock_updates"]["records_inserted"] == 1
        assert "currency_updates" not in result or not result["currency_updates"]
        assert result["success"] is True

    def test_perform_daily_update_no_data_available(self) -> None:
        """Test daily update when no data is available from either source."""
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None
        self.mock_currency.fetch_and_prepare_fx_data.return_value = None

        result = self.orchestrator.perform_daily_update()

        # Verify result shows no updates but no errors
        assert result["total_records_inserted"] == 0
        assert "stock_updates" not in result or not result["stock_updates"]
        assert "currency_updates" not in result or not result["currency_updates"]
        assert result["success"] is True
        assert len(result["errors"]) == 0

    def test_perform_daily_update_exception_handling(self) -> None:
        """Test daily update exception handling."""
        self.mock_nyse.fetch_and_prepare_all_data.side_effect = ValueError("Network timeout")

        result = self.orchestrator.perform_daily_update()

        # Verify exception is handled properly
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Daily update failed: Network timeout" in result["errors"][0]

    def test_perform_daily_update_type_error_handling(self) -> None:
        """Test daily update handling different exception types."""
        self.mock_nyse.fetch_and_prepare_all_data.side_effect = TypeError("Invalid type")

        result = self.orchestrator.perform_daily_update()

        assert result["success"] is False
        assert any("Daily update failed: Invalid type" in error for error in result["errors"])

    def test_perform_daily_update_runtime_error_handling(self) -> None:
        """Test daily update handling runtime errors."""
        self.mock_db.insert_stock_data.side_effect = RuntimeError("Database connection lost")
        stock_data = [{"symbol": "AAPL", "date": "2025-08-17", "close": 151.00}]
        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data

        result = self.orchestrator.perform_daily_update()

        assert result["success"] is False
        assert any("Database connection lost" in error for error in result["errors"])


class TestDataIngestionOrchestratorFullIngestion:
    """Test DataIngestionOrchestrator full ingestion workflow."""

    # Declare attributes that will be set in setup_method
    mock_db: Mock
    mock_nyse: Mock
    mock_currency: Mock
    orchestrator: DataIngestionOrchestrator

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()
        self.orchestrator = DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def test_run_full_ingestion_empty_database(self) -> None:
        """Test full ingestion when database is empty."""
        self.mock_db.is_database_empty.return_value = True
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        # Mock initial setup result
        setup_result = {
            "setup_completed": "2025-08-17T10:30:00",
            "total_records_inserted": 10,
            "success": True,
            "errors": [],
        }

        with patch.object(self.orchestrator, "perform_initial_setup", return_value=setup_result) as mock_setup:
            result = self.orchestrator.run_full_ingestion()

            # Verify initial setup was called
            mock_setup.assert_called_once_with(days_back=10)
            self.mock_db.is_database_empty.assert_called_once()
            self.mock_db.health_check.assert_called_once()

            # Verify result structure
            assert result["was_empty"] is True
            assert result["operation_performed"] == "initial_setup"
            assert result["success"] is True
            assert result["results"] == setup_result
            assert "ingestion_started" in result
            assert "ingestion_completed" in result

    def test_run_full_ingestion_existing_data(self) -> None:
        """Test full ingestion when database has existing data."""
        self.mock_db.is_database_empty.return_value = False
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        # Mock daily update result
        update_result = {
            "update_completed": "2025-08-17T10:35:00",
            "total_records_inserted": 5,
            "success": True,
            "errors": [],
        }

        with patch.object(self.orchestrator, "perform_daily_update", return_value=update_result) as mock_update:
            result = self.orchestrator.run_full_ingestion()

            # Verify daily update was called
            mock_update.assert_called_once()
            self.mock_db.is_database_empty.assert_called_once()
            self.mock_db.health_check.assert_called_once()

            # Verify result structure
            assert result["was_empty"] is False
            assert result["operation_performed"] == "daily_update"
            assert result["success"] is True
            assert result["results"] == update_result

    def test_run_full_ingestion_setup_failure(self) -> None:
        """Test full ingestion when initial setup fails."""
        self.mock_db.is_database_empty.return_value = True
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        setup_result = {
            "total_records_inserted": 0,
            "success": False,
            "errors": ["Failed to fetch data"],
        }

        with patch.object(self.orchestrator, "perform_initial_setup", return_value=setup_result):
            result = self.orchestrator.run_full_ingestion()

            assert result["success"] is False
            assert result["operation_performed"] == "initial_setup"

    def test_run_full_ingestion_update_failure(self) -> None:
        """Test full ingestion when daily update fails."""
        self.mock_db.is_database_empty.return_value = False
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        update_result = {
            "total_records_inserted": 0,
            "success": False,
            "errors": ["API rate limit exceeded"],
        }

        with patch.object(self.orchestrator, "perform_daily_update", return_value=update_result):
            result = self.orchestrator.run_full_ingestion()

            assert result["success"] is False
            assert result["operation_performed"] == "daily_update"

    def test_run_full_ingestion_exception_handling(self) -> None:
        """Test full ingestion exception handling within try block."""
        # Set up mocks so we get past the initial calls
        self.mock_db.is_database_empty.return_value = True
        self.mock_db.health_check.return_value = {"status": "healthy"}

        # Create a mock that fails during initial setup
        with patch.object(
            self.orchestrator,
            "perform_initial_setup",
            side_effect=RuntimeError("Setup failed"),
        ):
            result = self.orchestrator.run_full_ingestion()

            assert result["success"] is False
            assert "error" in result
            assert "Setup failed" in result["error"]

    def test_run_full_ingestion_database_connection_failure(self) -> None:
        """Test full ingestion handles database connection failures (bug fix verification)."""
        # Test the fixed bug - database connection failure should now be caught
        self.mock_db.is_database_empty.side_effect = RuntimeError("Database connection failed")

        result = self.orchestrator.run_full_ingestion()

        # Verify the exception is now properly caught and handled
        assert result["success"] is False
        assert "error" in result
        assert "Database connection failed" in result["error"]
        assert result["database_status"] is None  # Should remain None due to early failure
        assert result["was_empty"] is None  # Should remain None due to early failure
        assert result["operation_performed"] is None  # Should remain None due to early failure

    def test_run_full_ingestion_health_check_included(self) -> None:
        """Test that health check results are included in ingestion results."""
        health_status = {"status": "healthy", "connection": True, "tables": 5}
        self.mock_db.is_database_empty.return_value = False
        self.mock_db.health_check.return_value = health_status

        update_result = {"success": True, "total_records_inserted": 3}
        with patch.object(self.orchestrator, "perform_daily_update", return_value=update_result):
            result = self.orchestrator.run_full_ingestion()

            assert result["database_status"] == health_status


class TestDataIngestionOrchestratorStatus:
    """Test DataIngestionOrchestrator status functionality."""

    # Declare attributes that will be set in setup_method
    mock_db: Mock
    mock_nyse: Mock
    mock_currency: Mock
    orchestrator: DataIngestionOrchestrator

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()
        self.orchestrator = DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def test_get_ingestion_status_success(self) -> None:
        """Test successful status retrieval."""
        # Mock database health check
        db_health = {"status": "healthy", "connection": True, "tables": 3}
        self.mock_db.health_check.return_value = db_health

        # Mock stock data freshness
        stock_freshness = {
            "AAPL": date(2025, 8, 17),
            "MSFT": date(2025, 8, 17),
            "GOOGL": date(2025, 8, 16),
        }
        self.mock_nyse.check_data_freshness.return_value = stock_freshness

        # Mock currency data freshness
        currency_freshness = (date(2025, 8, 17), 0.785)
        self.mock_currency.get_latest_available_rate.return_value = currency_freshness

        # Mock magnificent seven symbols
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"

        # Mock missing data check
        self.mock_db.get_missing_dates_for_symbol.side_effect = [
            [],  # AAPL - no missing dates
            ["2025-08-16"],  # MSFT - 1 missing date
            [],  # AMZN - no missing dates
            [],  # GOOGL - no missing dates
            [],  # META - no missing dates
            [],  # NVDA - no missing dates
            [],  # TSLA - no missing dates
        ]

        result = self.orchestrator.get_ingestion_status()

        # Verify API calls
        self.mock_db.health_check.assert_called_once()
        self.mock_nyse.check_data_freshness.assert_called_once()
        self.mock_currency.get_latest_available_rate.assert_called_once()

        # Verify result structure
        assert "status_checked" in result
        assert result["database_health"] == db_health
        assert result["stock_data_freshness"]["AAPL"] == "2025-08-17"
        assert result["stock_data_freshness"]["MSFT"] == "2025-08-17"
        assert result["stock_data_freshness"]["GOOGL"] == "2025-08-16"
        assert result["currency_data_freshness"]["date"] == "2025-08-17"
        assert result["currency_data_freshness"]["rate"] == 0.785
        assert result["missing_recent_data"]["MSFT"] == 1
        assert result["companies_tracked"] == [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        assert result["currency_pair"] == "USD/GBP"

    def test_get_ingestion_status_no_currency_data(self) -> None:
        """Test status retrieval when no currency data is available."""
        self.mock_db.health_check.return_value = {"status": "healthy"}
        self.mock_nyse.check_data_freshness.return_value = {"AAPL": None}
        self.mock_currency.get_latest_available_rate.return_value = None
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"
        self.mock_db.get_missing_dates_for_symbol.return_value = []

        result = self.orchestrator.get_ingestion_status()

        assert result["currency_data_freshness"] is None
        assert result["stock_data_freshness"]["AAPL"] is None

    def test_get_ingestion_status_empty_currency_data(self) -> None:
        """Test status retrieval when currency data is empty tuple."""
        self.mock_db.health_check.return_value = {"status": "healthy"}
        self.mock_nyse.check_data_freshness.return_value = {"AAPL": None}
        self.mock_currency.get_latest_available_rate.return_value = ()
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"
        self.mock_db.get_missing_dates_for_symbol.return_value = []

        result = self.orchestrator.get_ingestion_status()

        # When currency_freshness is empty tuple, currency_data_freshness becomes None due to the conditional
        assert result["currency_data_freshness"] is None

    def test_get_ingestion_status_partial_currency_data(self) -> None:
        """Test status retrieval when currency data has only one element."""
        self.mock_db.health_check.return_value = {"status": "healthy"}
        self.mock_nyse.check_data_freshness.return_value = {"AAPL": None}
        self.mock_currency.get_latest_available_rate.return_value = (date(2025, 8, 17),)  # Only date, no rate
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"
        self.mock_db.get_missing_dates_for_symbol.return_value = []

        result = self.orchestrator.get_ingestion_status()

        assert result["currency_data_freshness"]["date"] == "2025-08-17"
        assert result["currency_data_freshness"]["rate"] is None

    def test_get_ingestion_status_exception_handling(self) -> None:
        """Test status retrieval exception handling."""
        self.mock_db.health_check.side_effect = ValueError("Database error")

        result = self.orchestrator.get_ingestion_status()

        assert "error" in result
        assert "Database error" in result["error"]
        assert result["success"] is False
        assert "status_checked" in result

    def test_get_ingestion_status_type_error_handling(self) -> None:
        """Test status retrieval handling different exception types."""
        self.mock_nyse.check_data_freshness.side_effect = TypeError("Invalid format")

        result = self.orchestrator.get_ingestion_status()

        assert "error" in result
        assert "Invalid format" in result["error"]
        assert result["success"] is False

    def test_get_ingestion_status_with_missing_data(self) -> None:
        """Test status retrieval when there are missing dates for multiple symbols."""
        self.mock_db.health_check.return_value = {"status": "healthy"}
        self.mock_nyse.check_data_freshness.return_value = {}
        self.mock_currency.get_latest_available_rate.return_value = None
        self.mock_nyse.MAGNIFICENT_SEVEN = ["AAPL", "MSFT", "GOOGL"]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"

        # Mock missing data for multiple symbols
        self.mock_db.get_missing_dates_for_symbol.side_effect = [
            ["2025-08-16", "2025-08-15"],  # AAPL - 2 missing dates
            [],  # MSFT - no missing dates
            ["2025-08-16"],  # GOOGL - 1 missing date
        ]

        result = self.orchestrator.get_ingestion_status()

        assert result["missing_recent_data"]["AAPL"] == 2
        assert "MSFT" not in result["missing_recent_data"]  # No missing data
        assert result["missing_recent_data"]["GOOGL"] == 1


class TestDataIngestionOrchestratorIntegration:
    """Test DataIngestionOrchestrator integration scenarios."""

    # Declare attributes that will be set in setup_method
    mock_db: Mock
    mock_nyse: Mock
    mock_currency: Mock
    orchestrator: DataIngestionOrchestrator

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_nyse = Mock()
        self.mock_currency = Mock()
        self.orchestrator = DataIngestionOrchestrator(
            db_manager=self.mock_db,
            nyse_fetcher=self.mock_nyse,
            currency_fetcher=self.mock_currency,
        )

    def test_end_to_end_initial_setup_workflow(self) -> None:
        """Test complete end-to-end initial setup workflow."""
        # Setup mocks for complete workflow
        self.mock_db.is_database_empty.return_value = True
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        stock_data = [
            {"symbol": "AAPL", "date": "2025-08-17", "close": 150.00},
            {"symbol": "MSFT", "date": "2025-08-17", "close": 350.00},
        ]
        currency_data = [{"date": "2025-08-17", "rate": 0.785}]

        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_stock_data.return_value = 2
        self.mock_db.insert_currency_data.return_value = 1
        self.mock_nyse.MAGNIFICENT_SEVEN = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "NVDA",
            "TSLA",
        ]
        self.mock_currency.FROM_CURRENCY = "USD"
        self.mock_currency.TO_CURRENCY = "GBP"

        # Execute full ingestion
        result = self.orchestrator.run_full_ingestion()

        # Verify complete workflow
        # Note: initial_setup returns "success" field, so full_ingestion should succeed
        assert result["success"] is True  # Successful workflow when all data is fetched
        assert result["operation_performed"] == "initial_setup"
        assert result["results"]["total_records_inserted"] == 3  # Stock data (2) + Currency data (1) = 3
        assert len(result["results"]["errors"]) == 0

        # Verify all components were called correctly
        self.mock_db.is_database_empty.assert_called_once()
        self.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=10)
        self.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=10)
        self.mock_db.insert_stock_data.assert_called_once_with(stock_data)
        self.mock_db.insert_currency_data.assert_called_once_with(currency_data)

    def test_end_to_end_daily_update_workflow(self) -> None:
        """Test complete end-to-end daily update workflow."""
        # Setup mocks for daily update workflow
        self.mock_db.is_database_empty.return_value = False
        self.mock_db.health_check.return_value = {
            "status": "healthy",
            "connection": True,
        }

        stock_data = [{"symbol": "AAPL", "date": "2025-08-17", "close": 151.50}]
        currency_data = [{"date": "2025-08-17", "rate": 0.790}]

        self.mock_nyse.fetch_and_prepare_all_data.return_value = stock_data
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_stock_data.return_value = 1
        self.mock_db.insert_currency_data.return_value = 1

        # Execute full ingestion
        result = self.orchestrator.run_full_ingestion()

        # Verify complete workflow
        assert result["success"] is True
        assert result["operation_performed"] == "daily_update"
        assert result["results"]["total_records_inserted"] == 2

        # Verify 3-day lookback for daily updates
        self.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=3)
        self.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=3)

    def test_resilient_error_handling_across_components(self) -> None:
        """Test that orchestrator handles errors gracefully across all components."""
        # Test various failure scenarios
        self.mock_db.is_database_empty.return_value = True
        self.mock_db.health_check.return_value = {"status": "healthy"}

        # Mock NYSE failure but currency success
        self.mock_nyse.fetch_and_prepare_all_data.return_value = None
        currency_data = [{"date": "2025-08-17", "rate": 0.785}]
        self.mock_currency.fetch_and_prepare_fx_data.return_value = currency_data
        self.mock_db.insert_currency_data.return_value = 1

        result = self.orchestrator.run_full_ingestion()

        # Verify partial success is handled correctly
        assert result["operation_performed"] == "initial_setup"
        assert result["results"]["total_records_inserted"] == 1  # Only currency data
        assert any("Failed to fetch stock data" in error for error in result["results"]["errors"])

        # Verify currency data was still processed
        self.mock_db.insert_currency_data.assert_called_once_with(currency_data)

    def test_logging_integration(self) -> None:
        """Test that logging is properly integrated throughout the orchestrator."""
        # This test verifies that the logger is set up and would be called
        # In a real scenario, you might want to test actual log output
        assert self.orchestrator.logger is not None
        assert self.orchestrator.logger.name == "src.ticker_converter.data_ingestion.orchestrator"

        # Test that logger is used in methods (would require log capture in real implementation)
        with patch.object(self.orchestrator.logger, "info") as mock_log_info:
            self.mock_db.is_database_empty.return_value = True
            self.mock_db.health_check.return_value = {"status": "healthy"}
            self.mock_nyse.fetch_and_prepare_all_data.return_value = []
            self.mock_currency.fetch_and_prepare_fx_data.return_value = []

            self.orchestrator.run_full_ingestion()

            # Verify logging calls were made
            assert mock_log_info.call_count > 0
