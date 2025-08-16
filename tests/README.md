# Tests Directory

This directory contains all test files for the ticker-converter project.

## Structure

# Tests Directory

## Purpose
Contains all tests with organized sub-directories for test types (unit, integration), pytest configuration, test fixtures, and mock data. Ensures comprehensive testing coverage while keeping tests well-organized and maintainable.

## Directory Structure

### `/tests/` (Root)
- **Use Case**: Test package initialization and top-level test files
- **Git Status**: Tracked
- **Contents**: `conftest.py`, test configuration files, cross-cutting test modules

### `/tests/unit/`
- **Use Case**: Unit tests organized by source code modules
- **Git Status**: Tracked
- **Organization**: Mirrors `/src/` structure for easy navigation
- **Sub-directories**:
  - `api/`: Tests for FastAPI endpoints and models
  - `api_clients/`: Tests for external API client classes
  - `data_ingestion/`: Tests for data fetching and processing
  - `data_models/`: Tests for Pydantic models and validation
  - `sql/`: Tests for SQL query validation
  - Additional modules as needed

### `/tests/quality/`
- **Use Case**: Code quality validation scripts (mypy, pylint, etc.)
- **Git Status**: Tracked
- **Contents**: Standardized quality check scripts for consistent validation
- **TODO**: Integrate these quality checks into main test CLI for unified execution

### `/tests/integration/`
- **Use Case**: Integration tests that test multiple components together
- **Git Status**: Tracked
- **Contents**: End-to-end workflows, API integration, database operations

### `/tests/fixtures/`
- **Use Case**: Test data fixtures and mock objects
- **Git Status**: Tracked
- **Contents**: 
  - `sample_responses.py`: Mock API responses
  - Mock data files and variables
  - Reusable test fixtures

### Configuration Files
- **`conftest.py`**: Pytest configuration and shared fixtures
- **`pytest.ini`**: Pytest settings and markers (in project root)
- **Test configuration**: Environment setup for testing

## Organization Principles

1. **Mirror Source Structure**: Unit tests should mirror the `/src/` directory structure
2. **No Hardcoded Data**: All test data should come from fixtures or mock files
3. **Isolation**: Each test should be independent and not affect others
4. **Comprehensive Coverage**: Aim for high test coverage across all modules
5. **Fast Execution**: Unit tests should run quickly, integration tests can be slower

## Usage Guidelines

- **New Unit Tests**: Add to appropriate subdirectory matching source code location
- **New Integration Tests**: Add to `/tests/integration/` with descriptive names
- **Mock Data**: Store in `/tests/fixtures/` to avoid hardcoding in test files
- **Configuration**: Use `conftest.py` for shared fixtures and test setup
- **Markers**: Use pytest markers to categorize tests (unit, integration, slow, etc.)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ticker_converter --cov-report=html

# Run specific test types
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Run with markers
pytest -m unit                  # Run tests marked as unit
pytest -m integration          # Run tests marked as integration

# Run with verbose output
pytest -v

# Run specific module tests
pytest tests/unit/api_clients/  # Test specific module
```

## Current Structure
```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Pytest configuration and fixtures
├── README.md                       # This file
├── TESTING_SAFETY.md              # Testing safety guidelines
├── unit/                           # Unit tests by module
│   ├── api/                       # FastAPI endpoint tests
│   ├── api_clients/               # External API client tests
│   ├── data_ingestion/            # Data processing tests
│   ├── data_models/               # Model validation tests
│   ├── etl_modules/               # ETL operation tests
│   └── sql/                       # SQL query tests
├── integration/                    # Integration tests
│   ├── test_api_integration.py    # API workflow tests
│   └── test_database_integration.py # Database operation tests
└── fixtures/                       # Test data and mocks
    ├── __init__.py
    └── sample_responses.py         # Mock API responses
```

## Testing Standards

- **Type Coverage**: All public functions should have tests
- **Error Scenarios**: Test both success and failure cases
- **Edge Cases**: Test boundary conditions and edge cases
- **Performance**: Include performance tests for critical paths
- **Documentation**: Clear test names and docstrings explaining test purpose

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
