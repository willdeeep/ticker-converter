"""Custom exception classes for ticker-converter application.

This module provides a hierarchy of specific exception classes to replace
generic exception handling patterns throughout the application.
"""


class TickerConverterException(Exception):
    """Base exception for ticker-converter specific errors.
    
    All custom exceptions should inherit from this base class.
    """
    pass


class DataIngestionException(TickerConverterException):
    """Raised when data ingestion operations fail.
    
    Used for errors during data extraction, transformation, or loading
    that are specific to the ingestion pipeline.
    """
    pass


class DatabaseConnectionException(TickerConverterException):
    """Raised when database connection operations fail.
    
    Used for connection timeouts, authentication failures, or
    network issues when connecting to the database.
    """
    pass


class DatabaseOperationException(TickerConverterException):
    """Raised when database operations fail.
    
    Used for SQL execution errors, constraint violations, or
    other database operation failures.
    """
    pass


class APIConnectionException(TickerConverterException):
    """Raised when external API connections fail.
    
    Used for network timeouts, authentication failures, or
    connection issues with external APIs like Alpha Vantage.
    """
    pass


class APIRateLimitException(TickerConverterException):
    """Raised when API rate limits are exceeded.
    
    Used specifically for rate limiting scenarios that require
    special handling (like pipeline failure).
    """
    pass


class DataValidationException(TickerConverterException):
    """Raised when data validation fails.
    
    Used for schema validation errors, data type mismatches,
    or business rule violations.
    """
    pass


class ConfigurationException(TickerConverterException):
    """Raised when configuration validation fails.
    
    Used for missing environment variables, invalid configuration
    values, or configuration file errors.
    """
    pass


class FileOperationException(TickerConverterException):
    """Raised when file operations fail.
    
    Used for file I/O errors, permission issues, or
    file format validation failures.
    """
    pass
