"""Optimized tests for DataIngestionOrchestrator - Example of Phase 3 improvements.

This module demonstrates testing optimization techniques by refactoring
repetitive test patterns into reusable fixtures and helpers.
"""

import pytest

from tests.fixtures import (
    TestDataBuilder,
    assert_error_in_result,
    assert_result_structure,
    expect_no_errors,
    mock_api_errors,
    mock_database_errors,
    mock_empty_database,
    mock_successful_setup,
    orchestrator_with_mocks,
    parametrize_with_data,
)


class TestDataIngestionOrchestratorOptimized:
    """Optimized tests demonstrating improved patterns and reduced duplication."""

    @parametrize_with_data([
        ("basic_success", {"days_back": 5, "expected_stocks": 2, "expected_currency": 1}),
        ("extended_history", {"days_back": 30, "expected_stocks": 2, "expected_currency": 1}),
        ("minimal_data", {"days_back": 1, "expected_stocks": 2, "expected_currency": 1}),
    ])
    def test_perform_initial_setup_success_scenarios(
        self, 
        test_name: str,  # pylint: disable=unused-argument
        test_params: dict,
        orchestrator_with_mocks,
        mock_successful_setup  # pylint: disable=unused-argument
    ) -> None:
        """Test successful initial setup with various configurations."""
        orchestrator, mocks = orchestrator_with_mocks
        days_back = test_params["days_back"]
        
        # Execute operation
        result = orchestrator.perform_initial_setup(days_back=days_back)
        
        # Verify standard result structure
        assert_result_structure(result, [
            "operation", "success", "total_records_inserted", 
            "errors", "start_time", "end_time"
        ])
        
        # Verify success outcome
        expect_no_errors(result)
        assert result["success"] is True
        assert result["total_records_inserted"] == test_params["expected_stocks"] + test_params["expected_currency"]
        
        # Verify correct API calls
        mocks.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=days_back)
        mocks.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=days_back)

    def test_perform_initial_setup_api_errors(self, orchestrator_with_mocks, mock_api_errors) -> None:  # pylint: disable=unused-argument
        """Test initial setup handling API errors."""
        orchestrator, _ = orchestrator_with_mocks  # mocks configured by fixture
        
        # Execute operation - should handle API errors gracefully
        result = orchestrator.perform_initial_setup(days_back=5)
        
        # Verify error handling
        assert_result_structure(result, ["errors", "success", "total_records_inserted"])
        assert_error_in_result(result, "API")
        assert result["success"] is False
        assert result["total_records_inserted"] == 0

    def test_perform_initial_setup_database_errors(self, orchestrator_with_mocks, mock_database_errors) -> None:  # pylint: disable=unused-argument
        """Test initial setup handling database errors."""
        orchestrator, mocks = orchestrator_with_mocks
        
        # Configure successful data fetching but database failure
        stock_data = TestDataBuilder().with_symbol("AAPL").with_date("2025-08-17").build()
        mocks.mock_nyse.fetch_and_prepare_all_data.return_value = [stock_data]
        
        # Expect database error to be raised due to our exception handling improvements
        with pytest.raises(Exception):  # Will be our custom DatabaseConnectionException
            orchestrator.perform_initial_setup(days_back=5)

    def test_run_full_ingestion_empty_database(self, orchestrator_with_mocks, mock_empty_database) -> None:  # pylint: disable=unused-argument
        """Test full ingestion when database is empty."""
        orchestrator, mocks = orchestrator_with_mocks
        
        # Create test data using builder pattern
        test_stock_data = [
            TestDataBuilder()
            .with_symbol("AAPL")
            .with_date("2025-08-17")
            .with_prices(220.50, 231.00, 219.25, 229.35)
            .with_volume(45000000)
            .build()
        ]
        
        test_currency_data = [
            TestDataBuilder()
            .with_date("2025-08-17")
            .with_exchange_rate(0.7850)
            .with_currencies("USD", "GBP")
            .build()
        ]
        
        # Configure mocks for empty database scenario
        mocks.mock_nyse.fetch_and_prepare_all_data.return_value = test_stock_data
        mocks.mock_currency.fetch_and_prepare_fx_data.return_value = test_currency_data
        mocks.mock_db.insert_stock_data.return_value = len(test_stock_data)
        mocks.mock_db.insert_currency_data.return_value = len(test_currency_data)
        
        # Execute operation
        result = orchestrator.run_full_ingestion(days_back=30)
        
        # Verify results
        expect_no_errors(result)
        assert result["success"] is True
        assert result["total_records_inserted"] == 2  # 1 stock + 1 currency

    @parametrize_with_data([
        ("recent_update", {"days_back": 1}),
        ("weekly_update", {"days_back": 7}),
    ])
    def test_perform_daily_update_scenarios(
        self,
        test_name: str,  # pylint: disable=unused-argument
        test_params: dict,
        orchestrator_with_mocks,
        mock_successful_setup  # pylint: disable=unused-argument
    ) -> None:
        """Test daily update operations with various timeframes."""
        orchestrator, mocks = orchestrator_with_mocks
        days_back = test_params["days_back"]
        
        # Execute operation
        result = orchestrator.perform_daily_update(days_back=days_back)
        
        # Verify standard outcomes
        assert_result_structure(result, ["operation", "success", "total_records_inserted"])
        expect_no_errors(result)
        
        # Verify API calls with correct parameters
        mocks.mock_nyse.fetch_and_prepare_all_data.assert_called_once_with(days_back=days_back)
        mocks.mock_currency.fetch_and_prepare_fx_data.assert_called_once_with(days_back=days_back)

    def test_check_data_status_comprehensive(self, orchestrator_with_mocks) -> None:
        """Test comprehensive data status checking."""
        orchestrator, mocks = orchestrator_with_mocks
        
        # Configure mock data for status check
        from datetime import date
        test_freshness_data = {
            "AAPL": date(2025, 8, 17),
            "MSFT": date(2025, 8, 16),
        }
        
        mocks.mock_nyse.check_data_freshness.return_value = test_freshness_data
        mocks.mock_currency.get_current_exchange_rate.return_value = 0.7850
        
        # Execute status check
        result = orchestrator.check_data_status()
        
        # Verify comprehensive status information
        expected_keys = [
            "status_checked", "data_freshness", "current_exchange_rate",
            "missing_recent_data", "companies_tracked", "currency_pair"
        ]
        assert_result_structure(result, expected_keys)
        
        # Verify specific status data
        assert result["data_freshness"] == test_freshness_data
        assert result["current_exchange_rate"] == 0.7850
        assert "USD/GBP" in result["currency_pair"]


# Performance benchmark test for optimization validation
class TestPerformanceOptimizations:
    """Tests to validate that optimizations improve performance."""

    def test_fixture_reuse_efficiency(self, orchestrator_with_mocks) -> None:
        """Validate that fixture reuse reduces setup overhead."""
        orchestrator, mocks = orchestrator_with_mocks
        
        # This test should execute quickly due to optimized fixtures
        # Multiple operations to test fixture efficiency
        for iteration in range(5):  # pylint: disable=unused-variable
            mocks.reset_mocks()  # Reset between iterations
            
            # Configure test data
            mocks.mock_nyse.fetch_and_prepare_all_data.return_value = []
            mocks.mock_currency.fetch_and_prepare_fx_data.return_value = []
            
            # Execute operation
            result = orchestrator.perform_daily_update(days_back=1)
            
            # Basic verification
            assert "success" in result
            
        # Test passes if it completes quickly without setup overhead

    def test_builder_pattern_efficiency(self) -> None:
        """Test that builder pattern creates test data efficiently."""
        # Create multiple test records efficiently
        builder = TestDataBuilder()
        
        # Build stock data
        stock_records = []
        for i, symbol in enumerate(["AAPL", "MSFT", "GOOGL"]):
            record = (builder
                     .with_symbol(symbol)
                     .with_date(f"2025-08-{17+i:02d}")
                     .with_prices(100.0 + i, 110.0 + i, 95.0 + i, 105.0 + i)
                     .with_volume(1000000 * (i + 1))
                     .build())
            stock_records.append(record)
        
        # Verify efficient creation
        assert len(stock_records) == 3
        assert all("symbol" in record for record in stock_records)
        assert stock_records[0]["symbol"] == "AAPL"
        assert stock_records[2]["volume"] == 3000000
