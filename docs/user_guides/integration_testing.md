# Integration Testing Framework

This document describes the comprehensive integration testing framework for the ticker-converter project.

## Overview

The integration testing framework validates external service connectivity and system integration without interfering with the main CI/CD pipeline. Tests are designed to run independently and verify real-world service availability.

## Test Structure

### Test Categories

1. **API Integration Tests** (`tests/integration/test_api_integration.py`)
   - Alpha Vantage API connectivity
   - API key validation
   - Data format compliance
   - Rate limiting respect

2. **Database Integration Tests** (`tests/integration/test_db_integration.py`)
   - PostgreSQL connectivity
   - Database permissions
   - Schema validation
   - Data quality assessment

3. **Airflow Integration Tests** (`tests/integration/test_airflow_integration.py`)
   - Airflow configuration validation
   - DAG testing and parsing
   - Environment variable verification
   - Service runtime checks

4. **Endpoint Integration Tests** (`tests/integration/test_endpoint_integration.py`)
   - FastAPI application startup
   - Endpoint accessibility
   - Data format validation
   - Production readiness checks

## Running Integration Tests

### Command Line Interface

Use the Makefile command to run all integration tests:

```bash
make test-int
```

This command:
- Sets up the proper test environment
- Runs all integration tests with verbose output
- Captures and displays comprehensive test results
- Validates external service connectivity

### Individual Test Files

Run specific integration test categories:

```bash
# API integration tests only
python -m pytest tests/integration/test_api_integration.py -v

# Database integration tests only  
python -m pytest tests/integration/test_db_integration.py -v

# Airflow integration tests only
python -m pytest tests/integration/test_airflow_integration.py -v

# Endpoint integration tests only
python -m pytest tests/integration/test_endpoint_integration.py -v
```

### Environment Configuration

Integration tests require environment variables for external services:

```bash
# Alpha Vantage API
export ALPHA_VANTAGE_API_KEY="your_api_key_here"

# PostgreSQL Database
export POSTGRES_HOST="localhost"
export POSTGRES_DB="ticker_converter"
export POSTGRES_USER="your_username"
export POSTGRES_PASSWORD="your_password"
export POSTGRES_PORT="5432"

# Airflow Configuration
export AIRFLOW_HOME="./airflow"
```

## Test Design Principles

### Non-Destructive Testing

- **No API Quota Consumption**: Tests use mock responses or minimal API calls
- **No Database Modification**: Read-only operations and separate test schemas
- **No Production Impact**: Tests run against development/test environments

### Service Validation

- **Connectivity Verification**: Confirms services are reachable
- **Configuration Validation**: Verifies environment variables and settings
- **Data Format Compliance**: Ensures expected data structures
- **Error Handling**: Tests graceful degradation and error responses

### Independence and Isolation

- **Self-Contained Tests**: Each test file runs independently
- **No Test Dependencies**: Tests don't depend on execution order
- **Environment Flexibility**: Tests adapt to available services
- **Graceful Skipping**: Tests skip when services unavailable

## Test Coverage

### Alpha Vantage API Integration

- **Connection Testing**: Verify API endpoint accessibility with timeout handling
- **Authentication**: Validate API key configuration and rotation
- **Response Format**: Check data structure compliance with Pydantic models
- **Rate Limiting**: Respect API usage constraints (5 calls/minute for free tier)
- **Error Handling**: Test invalid symbols, API errors, and network failures
- **Data Quality**: Validate OHLCV data completeness and accuracy

### PostgreSQL Database Integration

- **Connection Establishment**: Test async database connectivity with connection pooling
- **Permission Validation**: Verify read/write permissions for dimensional model
- **Schema Verification**: Check star schema structure (dimensions + facts + views)
- **Data Quality**: Validate referential integrity and constraint compliance
- **Performance**: Query performance validation for analytical views
- **Transaction Management**: Test ACID properties for financial data integrity

### Apache Airflow 3.0.4 Integration

- **Configuration Validation**: Check airflow.cfg settings and @dag decorator usage
- **DAG Parsing**: Verify modern @dag/@task syntax and TaskFlow API
- **Environment Variables**: Test required variable availability and validation
- **Service Status**: Check Airflow daemon status and scheduler health
- **Task Execution**: Validate SQL operators and Python task integration
- **Error Recovery**: Test retry logic and failure handling mechanisms

### FastAPI Endpoint Integration

- **Application Startup**: Test async FastAPI app initialization
- **Endpoint Accessibility**: Verify direct SQL query execution via routes
- **Data Serialization**: Check JSON response format with Pydantic validation
- **Error Handling**: Test invalid request handling and HTTP status codes
- **Performance Features**: Validate async operations and response times (<200ms)
- **API Documentation**: Verify automatic OpenAPI/Swagger documentation generation

## CI/CD Integration

### GitHub Actions Workflow

Integration tests are designed to complement the main CI/CD pipeline:

```yaml
# Example GitHub Actions integration
- name: Run Integration Tests
  run: make test-int
  env:
    ALPHA_VANTAGE_API_KEY: ${{ secrets.ALPHA_VANTAGE_API_KEY }}
    POSTGRES_HOST: ${{ secrets.POSTGRES_HOST }}
    POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
    POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
    POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  continue-on-error: true  # Don't fail build on integration test failures
```

### Local Development Workflow

Developers can run integration tests during development:

1. **Environment Setup**: Configure required environment variables
2. **Service Validation**: Run `make test-int` to verify external services
3. **Feature Development**: Use integration tests to validate new features
4. **Pre-Commit Checks**: Include integration tests in development workflow

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Error: Tests skip with "API key not configured"
   - Solution: Set required environment variables

2. **Service Unavailability**
   - Error: Connection timeouts or refused connections
   - Solution: Verify service status and network connectivity

3. **API Rate Limiting**
   - Error: HTTP 429 responses from external APIs
   - Solution: Wait for rate limit reset or use test API keys

4. **Database Connection Issues**
   - Error: Authentication or connection failures
   - Solution: Verify database credentials and network access

### Debug Mode

Run tests with additional debugging information:

```bash
# Verbose output with debugging
python -m pytest tests/integration/ -v -s --tb=long

# Debug specific test functions
python -m pytest tests/integration/test_api_integration.py::TestAlphaVantageAPIAccessibility::test_api_key_validation -v -s
```

## Maintenance

### Regular Updates

- **Service Compatibility**: Update tests for API changes
- **Environment Variables**: Add new configuration requirements
- **Test Coverage**: Expand tests for new integrations
- **Performance Benchmarks**: Update acceptable performance thresholds

### Test Validation

Periodically validate the integration test framework:

1. **Service Changes**: Update tests when external services change
2. **Environment Updates**: Verify tests work with new environments
3. **Coverage Analysis**: Ensure comprehensive integration coverage
4. **Performance Review**: Monitor test execution times

## Best Practices

### Writing Integration Tests

1. **Environment Awareness**: Check for required configuration before running
2. **Graceful Degradation**: Skip tests when services unavailable
3. **Minimal Resource Usage**: Avoid expensive operations during testing
4. **Clear Error Messages**: Provide helpful failure information
5. **Documentation**: Document test purpose and requirements

### Service Integration

1. **Configuration Management**: Use environment variables for service settings
2. **Connection Pooling**: Reuse connections when possible
3. **Timeout Handling**: Set appropriate timeouts for external services
4. **Retry Logic**: Implement retries for transient failures
5. **Security**: Protect credentials and sensitive information

## Future Enhancements

### Planned Improvements

1. **Mock Service Integration**: Add mock services for offline testing
2. **Performance Benchmarking**: Implement performance regression testing
3. **Chaos Engineering**: Add resilience testing capabilities
4. **Health Check Dashboard**: Create real-time service status monitoring
5. **Auto-Discovery**: Automatically discover and test new integrations
