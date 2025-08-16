# `/tests/` Directory

**Git Status**: Tracked  
**Use Case**: Test suite organization and quality assurance

This directory contains all testing infrastructure organized by test type and scope.

## Directory Structure
```
tests/
├── README.md                      # This file
├── TESTING_SAFETY.md             # Testing safety guidelines
├── conftest.py                   # Pytest configuration and fixtures
├── __init__.py                   # Package initialization
├── fixtures/                     # Test data and mock objects
├── unit/                         # Unit tests (mirrors src/ structure)
│   ├── api/                      # Tests for FastAPI endpoints
│   ├── api_clients/              # Tests for external API clients
│   ├── data_ingestion/           # Tests for data processing
│   ├── data_models/              # Tests for Pydantic models
│   └── sql/                      # Tests for SQL operations
├── integration/                  # Integration and system tests
├── quality/                      # Code quality validation scripts
│   ├── run_mypy.py              # Type checking script
│   └── quality_check.py         # Comprehensive quality validation
├── test_api_endpoints.py        # Legacy API tests (to be reorganized)
├── test_cli.py                  # CLI functionality tests
├── test_database_manager_utils.py # Database utility tests
└── test_market_data_validation.py # Market data validation tests
```

## Organization Principles

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

## Testing Standards

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
