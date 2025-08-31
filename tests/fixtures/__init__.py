"""Test fixtures and utilities for ticker-converter tests.

This package provides reusable fixtures, mock configurations, and test utilities
to improve test performance, maintainability, and reduce code duplication.
"""

# Import key fixtures for easy access
from .data_ingestion_fixtures import (
    MockDataIngestionComponents,
    mock_api_errors,
    mock_components,
    mock_database_errors,
    mock_empty_database,
    mock_successful_setup,
    orchestrator_with_mocks,
    sample_currency_data,
    sample_stock_data,
)
from .test_helpers import (
    MockResetManager,
    TestDataBuilder,
    assert_error_in_result,
    assert_mock_called_with_data,
    assert_result_structure,
    create_mock_with_methods,
    create_standard_result_dict,
    expect_no_errors,
    mock_datetime_now,
    parametrize_with_data,
    verify_mock_call_sequence,
)

__all__ = [
    # Data ingestion fixtures
    "MockDataIngestionComponents",
    "mock_api_errors",
    "mock_components", 
    "mock_database_errors",
    "mock_empty_database",
    "mock_successful_setup",
    "orchestrator_with_mocks",
    "sample_currency_data",
    "sample_stock_data",
    # Test helpers
    "MockResetManager",
    "TestDataBuilder",
    "assert_error_in_result",
    "assert_mock_called_with_data",
    "assert_result_structure",
    "create_mock_with_methods",
    "create_standard_result_dict",
    "expect_no_errors",
    "mock_datetime_now",
    "parametrize_with_data",
    "verify_mock_call_sequence",
]
