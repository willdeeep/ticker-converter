# Testing Safety Guide - API Usage Protection

## Overview

This document outlines the safety mechanisms in place to prevent accidental consumption of Alpha Vantage API quota during testing.

## Safety Mechanisms

### 1. Automatic Mock API Key

**Location**: `tests/conftest.py` - `pytest_configure()`

When running unit tests, the system automatically:
- Detects if `INTEGRATION_TEST=true` is set
- If NOT set, forces `ALPHA_VANTAGE_API_KEY` to a mock value
- Displays safety messages during test runs

```bash
🔒 Safety: API key set to mock value for unit tests
```

### 2. Integration Test Gating

**Location**: `tests/integration/test_api_integration.py`

Integration tests that make real API calls are gated with:
```python
integration_test = pytest.mark.skipif(
    not INTEGRATION_ENABLED or not REAL_API_KEY,
    reason="Integration tests require INTEGRATION_TEST=true and valid API key",
)
```

### 3. HTTP Request Mocking

**Location**: `tests/test_forex_crypto.py` and other unit tests

All unit tests use `@responses.activate` or `unittest.mock.patch` to mock HTTP requests:
```python
@responses.activate
def test_api_function():
    responses.add(responses.GET, "https://www.alphavantage.co/query", json=mock_data)
    # Test code here - no real API calls made
```

### 4. Pytest Configuration

**Location**: `pytest.ini`

Default environment variables ensure safe testing:
```ini
env =
    ALPHA_VANTAGE_API_KEY=test_mock_key_do_not_use_for_real_calls
    INTEGRATION_TEST=false
```

## Safe Test Execution

### Running Unit Tests (Safe - No API Calls)

```bash
# These commands will NEVER make real API calls
make test
python -m pytest tests/
python -m pytest tests/unit/
```

**Output**: Shows safety message confirming mock API key usage.

### Running Integration Tests (Uses Real API)

⚠️ **WARNING**: These commands consume your Alpha Vantage API quota!

```bash
# Method 1: Environment variable
INTEGRATION_TEST=true ALPHA_VANTAGE_API_KEY=your_real_key python -m pytest tests/integration/

# Method 2: Export variables
export INTEGRATION_TEST=true
export ALPHA_VANTAGE_API_KEY=your_real_key
python -m pytest tests/integration/
```

**Output**: Shows warning about real API usage and quota consumption.

## Test Categories

### Unit Tests (API-Safe)
- `tests/unit/` - All tests in this directory are mocked
- `tests/test_forex_crypto.py` - Uses `@responses.activate`
- Never make real HTTP requests
- Safe to run unlimited times

### Integration Tests (API-Consuming)
- `tests/integration/` - May make real API calls when enabled
- Require explicit `INTEGRATION_TEST=true` flag
- Should be run sparingly to preserve API quota

## Verification Commands

### Check Current Safety Status

```bash
# Check if integration tests are enabled
echo $INTEGRATION_TEST

# Check current API key (should be mock for unit tests)
echo $ALPHA_VANTAGE_API_KEY
```

### Test Safety Check

```bash
# This should show the safety message
python -m pytest tests/unit/test_core.py::TestFinancialDataPipeline::test_pipeline_initialization_with_api_key -v
```

Expected output:
```
🔒 Safety: API key set to mock value for unit tests
```

## Adding New Tests

### For Unit Tests (Recommended)

Always mock external API calls:

```python
from unittest.mock import patch

@patch('src.ticker_converter.api_client.AlphaVantageClient')
def test_your_function(mock_client):
    # Your test code here
    # No real API calls will be made
```

### For Integration Tests (Use Sparingly)

Mark with the integration decorator:

```python
from tests.integration.test_api_integration import integration_test

@integration_test
def test_real_api_call():
    # This test will only run with INTEGRATION_TEST=true
    # and will consume real API quota
```

## Troubleshooting

### "Real API calls detected" Error

If you see unexpected API usage:

1. Check environment variables: `env | grep ALPHA_VANTAGE`
2. Ensure `INTEGRATION_TEST` is not set: `echo $INTEGRATION_TEST`
3. Run only unit tests: `python -m pytest tests/unit/`

### Mock API Key Not Working

If the safety mechanism isn't working:

1. Check `tests/conftest.py` for the `pytest_configure` function
2. Ensure you're running pytest from the project root
3. Verify pytest.ini contains the safety environment variables

## API Quota Conservation

### Free Tier Limits
- Alpha Vantage free tier: 25 requests per day
- Each integration test may use 1-3 requests
- Be extremely conservative with integration test runs

### Best Practices
1. **Develop with unit tests only** (unlimited)
2. **Run integration tests sparingly** (quota-limited)
3. **Use mock data for development** 
4. **Only test real API before deployment**

## Emergency Stop

If tests are consuming API quota accidentally:

```bash
# Kill all Python processes
pkill -f python

# Unset environment variables
unset ALPHA_VANTAGE_API_KEY
unset INTEGRATION_TEST

# Verify safety
python -m pytest tests/unit/test_core.py -v
```

This should show the safety message confirming mock usage.
