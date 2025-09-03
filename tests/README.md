# `/tests/` Directory

**Git Status**: Tracked
**Use Case**: Comprehensive test suite with 69% coverage and 245+ passing tests

This directory contains all testing infrastructure organized by test type and scope, achieving professional-grade quality standards with 100% test success rate.

## Current Test Coverage Status

### Overall Metrics (v3.1.1)
- **Test Coverage**: 69% (above 50% requirement)
- **Total Tests**: 245+ tests passing
- **Success Rate**: 100% (all tests passing)
- **Quality Score**: Pylint 10.00/10 across all test modules
- **Integration**: Full CI/CD pipeline validation

### Coverage by Module
- ✅ **CLI Module**: 97% coverage (Phase 1 Priority 1 COMPLETED)
- ✅ **Database Manager**: 99% coverage (Phase 1 Priority 2 COMPLETED)
- 🎯 **API Clients**: 85% coverage (High priority module)
- 🎯 **Data Models**: 78% coverage (Pydantic validation)
- 📊 **Next Priorities**: Orchestrator (32%), NYSE Fetcher (20%)

## Directory Structure
```
tests/
├── README.md                      # This file
├── TESTING_SAFETY.md             # Testing safety guidelines
├── conftest.py                   # Pytest configuration and fixtures
├── __init__.py                   # Package initialization
├── fixtures/                     # Test data and mock objects
│   ├── sample_responses.py       # Mock API responses for testing
│   └── test_data.py              # Reusable test datasets
├── unit/                         # Unit tests (mirrors src/ structure)
│   ├── api/                      # Tests for FastAPI endpoints
│   ├── api_clients/              # Tests for external API clients (85% coverage)
│   ├── data_ingestion/           # Tests for data processing
│   ├── data_models/              # Tests for Pydantic models (78% coverage)
│   ├── cli/                      # CLI functionality tests (97% coverage)
│   └── integrations/             # Integration module tests
├── integration/                  # Integration and system tests
│   ├── test_airflow_integration.py    # Airflow DAG validation
│   ├── test_database_integration.py   # PostgreSQL integration
│   ├── test_api_integration.py        # External API connectivity
│   └── test_end_to_end.py            # Full pipeline validation
├── quality/                      # Code quality validation scripts
│   ├── run_mypy.py              # Type checking automation
│   └── quality_check.py         # Comprehensive quality validation
└── legacy/                       # Legacy test files (to be reorganized)
    ├── test_api_endpoints.py    # Legacy API tests
    ├── test_cli.py              # Legacy CLI tests
    ├── test_database_manager_utils.py # Legacy database tests
    └── test_market_data_validation.py # Legacy validation tests
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

### Quality Requirements (v3.1.1)
1. **Coverage Target**: Maintain 69%+ coverage (current: achieved)
2. **Success Rate**: 100% test pass rate (current: achieved)
3. **Quality Score**: Pylint 10.00/10 on all test modules
4. **No Hardcoded Data**: All test data from fixtures or mocks
5. **Test Isolation**: Independent tests with proper cleanup
6. **Fast Execution**: Unit tests <10s, integration tests allowed longer
7. **CI/CD Integration**: Full GitHub Actions pipeline validation

### Test Categories and Markers
```python
# Pytest markers for test categorization
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Integration tests requiring services
@pytest.mark.slow          # Tests that take >5 seconds
@pytest.mark.api           # External API tests
@pytest.mark.database      # Database-dependent tests
@pytest.mark.airflow       # Airflow DAG tests
```

### Comprehensive Test Coverage Strategy
- **Unit Tests**: Mirror source structure for easy navigation
- **Integration Tests**: End-to-end workflow validation
- **Quality Tests**: Automated code quality validation
- **Performance Tests**: Load and response time validation
- **Security Tests**: Input validation and SQL injection prevention

## Usage Guidelines

- **New Unit Tests**: Add to appropriate subdirectory matching source code location
- **New Integration Tests**: Add to `/tests/integration/` with descriptive names
- **Mock Data**: Store in `/tests/fixtures/` to avoid hardcoding in test files
- **Configuration**: Use `conftest.py` for shared fixtures and test setup
- **Markers**: Use pytest markers to categorize tests (unit, integration, slow, etc.)

## Running Tests

### Primary Test Commands
```bash
# Complete test suite with coverage (recommended)
make test
# Output: 245+ tests, 69% coverage, HTML report in htmlcov/

# Integration tests requiring external services
make test-int
# Requires: PostgreSQL, Airflow, API connectivity

# CI/CD optimized test execution
make test-ci
# Optimized for GitHub Actions environment

# Quality validation pipeline (includes tests)
make quality
# Full 7-step pipeline: Makefile → SQL → Black → isort → Pylint → MyPy → Tests
```

### Advanced Test Execution
```bash
# Run specific test categories
pytest -m unit                     # Unit tests only
pytest -m integration             # Integration tests only
pytest -m "not slow"              # Exclude slow tests

# Run with verbose output and coverage
pytest -v --cov=src/ticker_converter --cov-report=html

# Parallel test execution (faster)
pytest -n auto                    # Automatically detect CPU count

# Run specific test modules
pytest tests/unit/api_clients/     # Test specific module
pytest tests/integration/         # All integration tests
pytest tests/unit/cli/            # CLI tests (97% coverage)

# Debug failing tests
pytest -x -v --tb=long           # Stop on first failure, verbose output
pytest --pdb                      # Drop into debugger on failure
```

### Test Configuration and Environment
```bash
# Environment variables for testing
export TEST_DATABASE_URL="sqlite:///test.db"
export ALPHA_VANTAGE_API_KEY="mock_key_for_testing"
export PYTEST_COVERAGE_THRESHOLD="69"

# Custom pytest configuration
pytest --cov-report=term-missing  # Show missing coverage lines
pytest --cov-report=xml           # Generate XML for CI/CD
pytest --durations=10             # Show 10 slowest tests
```
