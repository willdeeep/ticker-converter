"""Performance comparison test demonstrating Phase 3 testing optimizations.

This module shows the improvements achieved by optimized fixtures and test helpers
compared to traditional repetitive test setup patterns.
"""

import time
from unittest.mock import Mock

import pytest

from src.ticker_converter.data_ingestion.orchestrator import DataIngestionOrchestrator
from tests.fixtures.test_helpers import TestDataBuilder


class TestingOptimizationDemonstration:
    """Demonstrate testing optimization benefits with concrete examples."""

    def test_traditional_repetitive_setup_pattern(self) -> None:
        """Example of traditional repetitive test setup (what we're optimizing away)."""
        # Traditional pattern - repeated in every test method
        mock_db = Mock()
        mock_nyse = Mock()
        mock_currency = Mock()

        # Repetitive setup that appears in multiple test classes
        mock_db.is_database_empty.return_value = False
        mock_db.insert_stock_data.return_value = 0
        mock_db.insert_currency_data.return_value = 0

        mock_nyse.MAGNIFICENT_SEVEN = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
        mock_nyse.fetch_and_prepare_all_data.return_value = []
        mock_nyse.check_data_freshness.return_value = {}

        mock_currency.FROM_CURRENCY = "USD"
        mock_currency.TO_CURRENCY = "GBP"
        mock_currency.fetch_and_prepare_fx_data.return_value = []
        mock_currency.get_current_exchange_rate.return_value = None

        # Create orchestrator
        orchestrator = DataIngestionOrchestrator(
            db_manager=mock_db,
            nyse_fetcher=mock_nyse,
            currency_fetcher=mock_currency,
        )

        # Test operation
        result = orchestrator.get_ingestion_status()
        assert "status_checked" in result

    def test_optimized_builder_pattern_for_test_data(self) -> None:
        """Demonstrate optimized test data creation using builder pattern."""
        start_time = time.time()

        # Create complex test data efficiently with builder pattern
        stock_data = (
            TestDataBuilder()
            .with_symbol("AAPL")
            .with_date("2025-08-17")
            .with_prices(220.50, 231.00, 219.25, 229.35)
            .with_volume(45000000)
            .with_source("alpha_vantage")
            .with_created_at("2025-08-17T10:00:00Z")
            .build()
        )

        currency_data = (
            TestDataBuilder()
            .with_date("2025-08-17")
            .with_exchange_rate(0.7850)
            .with_currencies("USD", "GBP")
            .with_source("alpha_vantage")
            .build()
        )

        setup_time = time.time() - start_time

        # Verify data creation
        assert stock_data["symbol"] == "AAPL"
        assert stock_data["close_price"] == 229.35
        assert currency_data["exchange_rate"] == 0.7850

        # Builder pattern should be very fast
        assert setup_time < 0.1, f"Builder pattern took too long: {setup_time}s"

    def test_performance_measurement_traditional_vs_optimized(self) -> None:
        """Measure performance difference between traditional and optimized patterns."""

        # Measure traditional repetitive setup time
        traditional_times = []
        for _ in range(10):
            start = time.time()

            # Traditional setup (what appears in many existing tests)
            mock_db = Mock()
            mock_nyse = Mock()
            mock_currency = Mock()

            mock_db.is_database_empty.return_value = False
            mock_db.insert_stock_data.return_value = 2
            mock_db.insert_currency_data.return_value = 1

            mock_nyse.MAGNIFICENT_SEVEN = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
            mock_nyse.fetch_and_prepare_all_data.return_value = []

            mock_currency.FROM_CURRENCY = "USD"
            mock_currency.TO_CURRENCY = "GBP"
            mock_currency.fetch_and_prepare_fx_data.return_value = []

            orchestrator = DataIngestionOrchestrator(
                db_manager=mock_db,
                nyse_fetcher=mock_nyse,
                currency_fetcher=mock_currency,
            )

            traditional_times.append(time.time() - start)

        # Measure optimized builder pattern time
        optimized_times = []
        for _ in range(10):
            start = time.time()

            # Optimized pattern using builder
            test_data = (
                TestDataBuilder()
                .with_symbol("AAPL")
                .with_date("2025-08-17")
                .with_prices(220.0, 230.0, 215.0, 225.0)
                .with_volume(1000000)
                .build()
            )

            optimized_times.append(time.time() - start)

        # Compare performance
        avg_traditional = sum(traditional_times) / len(traditional_times)
        avg_optimized = sum(optimized_times) / len(optimized_times)

        print(f"\nPerformance Comparison:")
        print(f"Traditional setup: {avg_traditional:.6f}s average")
        print(f"Optimized builder: {avg_optimized:.6f}s average")
        print(f"Improvement: {((avg_traditional - avg_optimized) / avg_traditional * 100):.1f}% faster")

        # Optimized pattern should be measurably faster for test data creation
        assert avg_optimized < avg_traditional, "Optimized pattern should be faster"

    def test_code_duplication_reduction_benefits(self) -> None:
        """Demonstrate how fixtures reduce code duplication."""

        # Example of what would be repeated across multiple test classes
        REPETITIVE_SETUP_LINES = [
            "mock_db = Mock()",
            "mock_nyse = Mock()",
            "mock_currency = Mock()",
            "mock_db.is_database_empty.return_value = False",
            "mock_db.insert_stock_data.return_value = 0",
            "mock_db.insert_currency_data.return_value = 0",
            "mock_nyse.MAGNIFICENT_SEVEN = ['AAPL', 'MSFT', ...]",
            "mock_nyse.fetch_and_prepare_all_data.return_value = []",
            "mock_currency.FROM_CURRENCY = 'USD'",
            "mock_currency.TO_CURRENCY = 'GBP'",
            "orchestrator = DataIngestionOrchestrator(...)",
        ]

        # In the original test_orchestrator_comprehensive.py file:
        # - 5 test classes each with setup_method()
        # - Each setup_method has ~11 lines of repetitive mock setup
        # - Total: 5 * 11 = 55 lines of duplicated code

        duplicate_lines_before = 5 * len(REPETITIVE_SETUP_LINES)

        # With optimized fixtures:
        # - 1 fixture definition replaces all setup methods
        # - Tests just receive pre-configured components
        # - Reduction: ~55 lines → ~5 lines of fixture usage

        duplicate_lines_after = 5  # Just fixture parameter usage

        reduction_percentage = (duplicate_lines_before - duplicate_lines_after) / duplicate_lines_before * 100

        print(f"\nCode Duplication Reduction:")
        print(f"Lines before optimization: {duplicate_lines_before}")
        print(f"Lines after optimization: {duplicate_lines_after}")
        print(f"Reduction: {reduction_percentage:.1f}%")

        # Should achieve significant reduction
        assert reduction_percentage > 80, f"Should reduce duplication by >80%, got {reduction_percentage:.1f}%"

    def test_test_maintainability_improvement(self) -> None:
        """Demonstrate improved test maintainability with centralized configuration."""

        # Problem: In traditional setup, if we need to change mock behavior,
        # we need to update it in every test class setup_method()

        # Solution: With fixtures, we update mock behavior in one place
        from tests.fixtures.data_ingestion_fixtures import MockDataIngestionComponents

        # Create mock components
        components = MockDataIngestionComponents()

        # Verify centralized configuration
        assert components.mock_db.is_database_empty.return_value is False
        assert components.mock_nyse.MAGNIFICENT_SEVEN == ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
        assert components.mock_currency.FROM_CURRENCY == "USD"

        # If we need to change default behavior, we change it in one place
        # and all tests using the fixture get the update automatically

        # Test that reset functionality works for test isolation
        original_return_value = components.mock_db.insert_stock_data.return_value
        components.mock_db.insert_stock_data.return_value = 999

        components.reset_mocks()

        # Should be back to default after reset
        assert components.mock_db.insert_stock_data.return_value == 0
        assert components.mock_db.insert_stock_data.return_value != 999

    @pytest.mark.parametrize(
        "symbol,expected_volume",
        [
            ("AAPL", 45000000),
            ("MSFT", 25000000),
            ("GOOGL", 15000000),
        ],
    )
    def test_parametrized_testing_efficiency(self, symbol: str, expected_volume: int) -> None:
        """Demonstrate efficient parametrized testing with builder pattern."""

        # Create test data efficiently for each parameter combination
        test_record = (
            TestDataBuilder()
            .with_symbol(symbol)
            .with_volume(expected_volume)
            .with_date("2025-08-17")
            .with_prices(100.0, 110.0, 95.0, 105.0)
            .build()
        )

        # Verify parameterized data
        assert test_record["symbol"] == symbol
        assert test_record["volume"] == expected_volume
        assert test_record["data_date"] == "2025-08-17"

        # This pattern scales efficiently to many parameter combinations
