"""Unit tests for Alpha Vantage API utilities."""

from unittest.mock import patch, Mock
import time
import pytest

from src.ticker_converter.api_clients.utils import (
    calculate_backoff_delay,
    should_retry_request,
    validate_symbol,
    format_api_response,
    mask_api_key,
)


class TestAPIUtils:
    """Test suite for Alpha Vantage API utilities."""

    def test_calculate_backoff_delay_default(self):
        """Test backoff delay calculation with default base delay."""
        # Test exponential backoff: base_delay * (2^attempt)
        assert calculate_backoff_delay(0) == 12  # 12 * 2^0 = 12
        assert calculate_backoff_delay(1) == 24  # 12 * 2^1 = 24
        assert calculate_backoff_delay(2) == 48  # 12 * 2^2 = 48
        assert calculate_backoff_delay(3) == 96  # 12 * 2^3 = 96

    def test_calculate_backoff_delay_custom_base(self):
        """Test backoff delay calculation with custom base delay."""
        base_delay = 5
        assert calculate_backoff_delay(0, base_delay) == 5   # 5 * 2^0 = 5
        assert calculate_backoff_delay(1, base_delay) == 10  # 5 * 2^1 = 10
        assert calculate_backoff_delay(2, base_delay) == 20  # 5 * 2^2 = 20
        assert calculate_backoff_delay(3, base_delay) == 40  # 5 * 2^3 = 40

    def test_calculate_backoff_delay_jitter(self):
        """Test that backoff delay includes jitter for randomization."""
        # Mock random to ensure consistent testing
        with patch('src.ticker_converter.api_clients.utils.random.uniform') as mock_random:
            mock_random.return_value = 0.5  # 50% of jitter range
            
            delay = calculate_backoff_delay(1)  # 24 * (1 + 0.1 * 0.5) = 24 * 1.05 = 25.2
            expected = int(24 * (1 + 0.1 * 0.5))
            assert delay == expected

    def test_calculate_backoff_delay_max_jitter(self):
        """Test backoff delay with maximum jitter."""
        with patch('src.ticker_converter.api_clients.utils.random.uniform') as mock_random:
            mock_random.return_value = 1.0  # 100% of jitter range
            
            delay = calculate_backoff_delay(2)  # 48 * (1 + 0.1 * 1.0) = 48 * 1.1 = 52.8
            expected = int(48 * (1 + 0.1 * 1.0))
            assert delay == expected

    def test_should_retry_request_status_codes(self):
        """Test retry logic for different HTTP status codes."""
        # Should retry on server errors (5xx)
        assert should_retry_request(500) is True
        assert should_retry_request(502) is True
        assert should_retry_request(503) is True
        assert should_retry_request(504) is True
        
        # Should retry on rate limiting
        assert should_retry_request(429) is True
        
        # Should not retry on client errors (4xx except 429)
        assert should_retry_request(400) is False
        assert should_retry_request(401) is False
        assert should_retry_request(403) is False
        assert should_retry_request(404) is False
        
        # Should not retry on success codes
        assert should_retry_request(200) is False
        assert should_retry_request(201) is False

    def test_should_retry_request_max_attempts(self):
        """Test retry logic respects maximum attempts."""
        # Should not retry if we've reached max attempts
        assert should_retry_request(500, 0, 3) is True   # First attempt
        assert should_retry_request(500, 1, 3) is True   # Second attempt
        assert should_retry_request(500, 2, 3) is True   # Third attempt
        assert should_retry_request(500, 3, 3) is False  # Exceeded max attempts

    def test_should_retry_request_non_retryable_status(self):
        """Test that non-retryable status codes don't retry regardless of attempts."""
        assert should_retry_request(400, 0, 3) is False
        assert should_retry_request(401, 1, 3) is False
        assert should_retry_request(404, 2, 3) is False

    def test_validate_symbol_valid_symbols(self):
        """Test validation of valid stock symbols."""
        # Valid symbols should pass without raising
        validate_symbol("AAPL")
        validate_symbol("MSFT")
        validate_symbol("GOOGL")
        validate_symbol("TSLA")
        validate_symbol("A")      # Single letter
        validate_symbol("BRK.A")  # With dot
        validate_symbol("BRK-A")  # With hyphen

    def test_validate_symbol_invalid_symbols(self):
        """Test validation of invalid stock symbols."""
        # Empty or None symbols should raise ValueError
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            validate_symbol("")
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            validate_symbol(None)
        
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            validate_symbol("   ")  # Whitespace only

    def test_validate_symbol_length_limit(self):
        """Test validation of symbol length limits."""
        # Very long symbols should be rejected
        long_symbol = "A" * 20  # 20 characters
        with pytest.raises(ValueError, match="Symbol too long"):
            validate_symbol(long_symbol)

    def test_validate_symbol_invalid_characters(self):
        """Test validation of symbols with invalid characters."""
        # Symbols with invalid characters should be rejected
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            validate_symbol("AAPL@")
        
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            validate_symbol("MSFT#")
        
        with pytest.raises(ValueError, match="Symbol contains invalid characters"):
            validate_symbol("TEST$")

    def test_format_api_response_success(self):
        """Test formatting of successful API response."""
        response_data = {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Symbol": "AAPL"
            },
            "Time Series (Daily)": {
                "2025-08-14": {
                    "1. open": "220.00",
                    "2. high": "225.00",
                    "3. low": "219.00",
                    "4. close": "224.50",
                    "5. volume": "1000000"
                }
            }
        }
        
        formatted = format_api_response(response_data)
        
        assert formatted["success"] is True
        assert formatted["data"] == response_data
        assert "timestamp" in formatted
        assert formatted["error"] is None

    def test_format_api_response_error(self):
        """Test formatting of error API response."""
        error_data = {
            "Error Message": "Invalid API call. Please retry or visit the documentation"
        }
        
        formatted = format_api_response(error_data, error="Invalid API call")
        
        assert formatted["success"] is False
        assert formatted["data"] == error_data
        assert "timestamp" in formatted
        assert formatted["error"] == "Invalid API call"

    def test_format_api_response_with_metadata(self):
        """Test formatting of API response with additional metadata."""
        response_data = {"test": "data"}
        metadata = {"symbol": "AAPL", "function": "TIME_SERIES_DAILY"}
        
        formatted = format_api_response(response_data, metadata=metadata)
        
        assert formatted["success"] is True
        assert formatted["data"] == response_data
        assert formatted["metadata"] == metadata
        assert "timestamp" in formatted

    def test_mask_api_key_short_key(self):
        """Test API key masking for short keys."""
        short_key = "abc123"
        masked = mask_api_key(short_key)
        
        assert masked == "***123"  # Show last 3 characters
        assert short_key not in masked

    def test_mask_api_key_long_key(self):
        """Test API key masking for long keys."""
        long_key = "abcdefghijklmnopqrstuvwxyz123456"
        masked = mask_api_key(long_key)
        
        assert masked == "***456"  # Show last 3 characters
        assert long_key not in masked

    def test_mask_api_key_exact_length(self):
        """Test API key masking for keys of exact minimum length."""
        key = "abc"  # Exactly 3 characters
        masked = mask_api_key(key)
        
        assert masked == "***"  # All characters masked for very short keys

    def test_mask_api_key_empty_or_none(self):
        """Test API key masking for empty or None keys."""
        assert mask_api_key("") == "***"
        assert mask_api_key(None) == "***"

    def test_mask_api_key_preserves_length_info(self):
        """Test that masked key gives hint about original length."""
        short_key = "12345"
        long_key = "1234567890abcdef"
        
        short_masked = mask_api_key(short_key)
        long_masked = mask_api_key(long_key)
        
        # Both should show last 3 characters pattern
        assert short_masked.endswith("345")
        assert long_masked.endswith("def")
        
        # Both should start with ***
        assert short_masked.startswith("***")
        assert long_masked.startswith("***")

    @patch('src.ticker_converter.api_clients.utils.time.time')
    def test_format_api_response_timestamp(self, mock_time):
        """Test that format_api_response includes accurate timestamp."""
        mock_time.return_value = 1692014400.0  # Fixed timestamp
        
        response_data = {"test": "data"}
        formatted = format_api_response(response_data)
        
        assert formatted["timestamp"] == 1692014400.0
        mock_time.assert_called_once()

    def test_calculate_backoff_delay_large_attempts(self):
        """Test backoff delay calculation for large attempt numbers."""
        # Should handle large attempt numbers without overflow
        large_attempt = 10
        delay = calculate_backoff_delay(large_attempt)
        
        # 12 * 2^10 = 12 * 1024 = 12288
        expected_base = 12 * (2 ** large_attempt)
        
        # With jitter, delay should be between base and base * 1.1
        assert delay >= expected_base
        assert delay <= int(expected_base * 1.1)

    def test_should_retry_request_edge_cases(self):
        """Test retry logic edge cases."""
        # Negative attempt numbers should not retry
        assert should_retry_request(500, -1, 3) is False
        
        # Zero max attempts should not retry
        assert should_retry_request(500, 0, 0) is False
        
        # Very large max attempts should still work
        assert should_retry_request(500, 0, 1000) is True
