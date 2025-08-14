"""Unit tests for Alpha Vantage API exceptions."""

from src.ticker_converter.api_clients.exceptions import (
    AlphaVantageAPIError,
    AlphaVantageRateLimitError,
    AlphaVantageRequestError,
    AlphaVantageConfigError,
    AlphaVantageAuthenticationError,
    AlphaVantageTimeoutError,
    AlphaVantageDataError,
)


class TestAlphaVantageExceptions:
    """Test suite for Alpha Vantage API exceptions."""

    def test_base_exception(self):
        """Test the base AlphaVantageAPIError."""
        message = "Test error message"
        error = AlphaVantageAPIError(message)
        
        assert str(error) == message
        assert isinstance(error, Exception)

    def test_base_exception_with_error_code(self):
        """Test base exception with error code."""
        message = "API Error"
        error_code = "ERR_001"
        error = AlphaVantageAPIError(message, error_code)
        
        assert str(error) == message
        assert error.error_code == error_code

    def test_rate_limit_error(self):
        """Test AlphaVantageRateLimitError."""
        message = "Rate limit exceeded"
        error = AlphaVantageRateLimitError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_rate_limit_error_with_error_code(self):
        """Test rate limit error with error code."""
        message = "Rate limit exceeded"
        error_code = "RATE_LIMIT"
        error = AlphaVantageRateLimitError(message, error_code)
        
        assert str(error) == message
        assert error.error_code == error_code

    def test_request_error(self):
        """Test AlphaVantageRequestError."""
        message = "Request failed"
        error = AlphaVantageRequestError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_config_error(self):
        """Test AlphaVantageConfigError."""
        message = "Configuration error"
        error = AlphaVantageConfigError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_authentication_error(self):
        """Test AlphaVantageAuthenticationError."""
        message = "Authentication failed"
        error = AlphaVantageAuthenticationError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_timeout_error(self):
        """Test AlphaVantageTimeoutError."""
        message = "Request timed out"
        error = AlphaVantageTimeoutError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_data_error(self):
        """Test AlphaVantageDataError."""
        message = "Data parsing failed"
        error = AlphaVantageDataError(message)
        
        assert str(error) == message
        assert isinstance(error, AlphaVantageAPIError)

    def test_exception_inheritance_chain(self):
        """Test that all exceptions properly inherit from base exception."""
        exceptions = [
            AlphaVantageRateLimitError("test"),
            AlphaVantageRequestError("test"),
            AlphaVantageConfigError("test"),
            AlphaVantageAuthenticationError("test"),
            AlphaVantageTimeoutError("test"),
            AlphaVantageDataError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AlphaVantageAPIError)
            assert isinstance(exc, Exception)

    def test_exception_error_code_preservation(self):
        """Test that error codes are preserved through inheritance."""
        error_code = "TEST_CODE"
        
        # Test each exception type with error code
        rate_limit_error = AlphaVantageRateLimitError("rate limit", error_code)
        assert rate_limit_error.error_code == error_code
        
        request_error = AlphaVantageRequestError("request failed", error_code)
        assert request_error.error_code == error_code
        
        config_error = AlphaVantageConfigError("config error", error_code)
        assert config_error.error_code == error_code
        
        auth_error = AlphaVantageAuthenticationError("auth failed", error_code)
        assert auth_error.error_code == error_code
        
        timeout_error = AlphaVantageTimeoutError("timeout", error_code)
        assert timeout_error.error_code == error_code
        
        data_error = AlphaVantageDataError("data error", error_code)
        assert data_error.error_code == error_code

    def test_exception_str_and_repr(self):
        """Test string and repr methods of exceptions."""
        message = "Test error message"
        
        # Test base exception
        base_error = AlphaVantageAPIError(message)
        assert str(base_error) == message
        assert "AlphaVantageAPIError" in repr(base_error)
        assert message in repr(base_error)
        
        # Test specific exceptions
        rate_limit_error = AlphaVantageRateLimitError(message)
        assert str(rate_limit_error) == message
        assert "AlphaVantageRateLimitError" in repr(rate_limit_error)
        
        timeout_error = AlphaVantageTimeoutError(message)
        assert str(timeout_error) == message
        assert "AlphaVantageTimeoutError" in repr(timeout_error)

    def test_exception_equality(self):
        """Test exception equality comparison."""
        message = "Test message"
        
        # Same type and message should be equal
        error1 = AlphaVantageAPIError(message)
        error2 = AlphaVantageAPIError(message)
        
        # Note: Exception instances are not equal by default in Python
        # They are only equal if they are the same object
        assert error1 is not error2
        assert str(error1) == str(error2)
        
        # Different types should not be equal
        rate_error = AlphaVantageRateLimitError(message)
        auth_error = AlphaVantageAuthenticationError(message)
        assert type(rate_error) != type(auth_error)

    def test_exception_with_none_values(self):
        """Test exceptions with None values for optional parameters."""
        # Test with None message
        error1 = AlphaVantageAPIError(None)
        assert str(error1) == "None"
        
        # Test with None error_code
        error2 = AlphaVantageAPIError("test", None)
        assert error2.error_code is None
        
        # Test specific exceptions with None error codes
        rate_error = AlphaVantageRateLimitError("test", None)
        assert rate_error.error_code is None
        
        config_error = AlphaVantageConfigError("test", None)
        assert config_error.error_code is None
        
        data_error = AlphaVantageDataError("test", None)
        assert data_error.error_code is None
