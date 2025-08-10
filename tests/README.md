# Tests Directory

This directory contains all test files for the ticker-converter project.

## Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_config.py         # Configuration tests
│   ├── test_api_client.py     # API client tests
│   └── test_core.py           # Core pipeline tests
├── integration/                # Integration tests
│   ├── __init__.py
│   └── test_api_integration.py # Full API integration tests
└── fixtures/                   # Test data fixtures
    ├── __init__.py
    └── sample_responses.py     # Mock API responses
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ticker_converter

# Run specific test types
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Run with verbose output
pytest -v
```
