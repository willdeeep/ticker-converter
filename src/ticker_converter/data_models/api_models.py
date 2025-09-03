"""API-specific data models with enhanced validation and type safety.

This module provides models specifically designed for API requests and responses
with comprehensive validation, error handling, and type safety for Python 3.11.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Generic type for API responses
T = TypeVar("T")


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class APIStatus(str, Enum):
    """API response status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    page: int = Field(default=1, ge=1, le=1000, description="Page number (1-based)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of items per page")
    sort_by: str | None = Field(default=None, max_length=50, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order (asc/desc)")

    def get_offset(self) -> int:
        """Calculate database offset from page and page_size."""
        return (self.page - 1) * self.page_size


class PaginationInfo(BaseModel):
    """Pagination information for API responses."""

    model_config = ConfigDict(validate_assignment=True)

    current_page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    @model_validator(mode="after")
    def validate_pagination_consistency(self) -> "PaginationInfo":
        """Validate pagination values are consistent."""
        expected_total_pages = (self.total_items + self.page_size - 1) // self.page_size
        if self.total_pages != expected_total_pages:
            raise ValueError("Total pages doesn't match calculation from total_items and page_size")

        expected_has_next = self.current_page < self.total_pages
        if self.has_next != expected_has_next:
            raise ValueError("has_next value is inconsistent with pagination state")

        expected_has_previous = self.current_page > 1
        if self.has_previous != expected_has_previous:
            raise ValueError("has_previous value is inconsistent with pagination state")

        return self


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper with comprehensive metadata."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    status: APIStatus = Field(..., description="Response status")
    data: T | None = Field(default=None, description="Response data")
    message: str | None = Field(default=None, description="Status message")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    pagination: PaginationInfo | None = Field(default=None, description="Pagination info")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp (UTC)",
    )
    request_id: str | None = Field(default=None, description="Request tracking ID")

    @model_validator(mode="after")
    def validate_response_consistency(self) -> "APIResponse[T]":
        """Validate response status is consistent with data and errors."""
        if self.status == APIStatus.ERROR:
            if not self.errors:
                raise ValueError("Error status requires at least one error message")
            if self.data is not None:
                # Some APIs return partial data even on error, so this might be a warning
                warnings_list = list(self.warnings) if self.warnings else []
                warnings_list.append("Data present despite error status")
                object.__setattr__(self, "warnings", warnings_list)

        elif self.status == APIStatus.SUCCESS:
            if self.errors:
                # If there are errors, status should not be success
                raise ValueError("Success status cannot have error messages")

        return self


class StockQueryParams(BaseModel):
    """Parameters for stock data queries."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    symbols: list[str] = Field(..., min_length=1, max_length=50, description="Stock symbols to query")
    start_date: date | None = Field(default=None, description="Start date for data range")
    end_date: date | None = Field(default=None, description="End date for data range")
    include_currency_conversion: bool = Field(default=True, description="Include USD to GBP conversion")

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: list[str]) -> list[str]:
        """Validate and normalize stock symbols."""
        normalized = []
        for symbol in v:
            symbol = symbol.upper().strip()
            if not symbol:
                raise ValueError("Empty symbol not allowed")
            if not symbol.replace(".", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid symbol format: {symbol}")
            normalized.append(symbol)

        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in normalized:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)

        return unique_symbols

    @model_validator(mode="after")
    def validate_date_range(self) -> "StockQueryParams":
        """Validate date range parameters."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")

            # Check for reasonable date range (not too far in past or future)
            today = date.today()
            if self.end_date > today:
                raise ValueError("end_date cannot be in the future")
            # pylint: disable=no-member  # Pydantic field access
            if self.start_date.year < 1980:
                raise ValueError("start_date cannot be before 1980")

        elif self.start_date:
            # pylint: disable=no-member  # Pydantic field access
            if self.start_date.year < 1980:
                raise ValueError("start_date cannot be before 1980")

        return self


class EnhancedStockPerformance(BaseModel):
    """Enhanced stock performance data with additional metrics."""

    model_config = ConfigDict(
        validate_assignment=True,
        json_encoders={
            Decimal: float,
            date: date.isoformat,
        },
    )

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")

    # Price data with Decimal precision
    price_usd: Decimal = Field(..., gt=0, description="Closing price in USD")
    price_gbp: Decimal | None = Field(None, gt=0, description="Closing price in GBP")

    # Performance metrics
    daily_return_pct: Decimal | None = Field(
        None,
        ge=-100,
        le=1000,  # Allow for extreme cases
        description="Daily return percentage",
    )
    volume: int = Field(..., ge=0, description="Trading volume")
    trade_date: date = Field(..., description="Trading date")

    # Enhanced metrics
    market_cap_usd: Decimal | None = Field(None, gt=0, description="Market capitalization USD")
    pe_ratio: Decimal | None = Field(None, gt=0, description="Price-to-earnings ratio")
    performance_rank: int | None = Field(None, ge=1, le=10, description="Performance ranking (1=best)")

    # Technical indicators
    rsi: Decimal | None = Field(None, ge=0, le=100, description="Relative Strength Index")
    moving_avg_20d: Decimal | None = Field(None, gt=0, description="20-day moving average")
    volatility_30d: Decimal | None = Field(None, ge=0, description="30-day volatility percentage")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        v = v.upper().strip()
        if not v.replace(".", "").replace("-", "").isalnum():
            raise ValueError("Invalid symbol format")
        return v

    @field_validator("trade_date")
    @classmethod
    def validate_trade_date(cls, v: date) -> date:
        """Validate trade date is not in the future."""
        if v > date.today():
            raise ValueError("Trade date cannot be in the future")
        return v


class CurrencyConversionDetails(BaseModel):
    """Enhanced currency conversion data."""

    model_config = ConfigDict(
        validate_assignment=True,
        json_encoders={
            Decimal: float,
            date: date.isoformat,
        },
    )

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")

    # USD data
    price_usd: Decimal = Field(..., gt=0, description="Price in USD")

    # GBP conversion
    usd_to_gbp_rate: Decimal = Field(..., gt=0, description="USD to GBP exchange rate")
    price_gbp: Decimal = Field(..., gt=0, description="Price in GBP")
    rate_date: date = Field(..., description="Exchange rate date")

    # Rate metadata
    rate_source: str = Field(..., description="Exchange rate data source")
    rate_age_hours: int = Field(..., ge=0, description="Age of exchange rate in hours")
    is_rate_stale: bool = Field(..., description="Whether rate is considered stale")

    @model_validator(mode="after")
    def validate_conversion_accuracy(self) -> "CurrencyConversionDetails":
        """Validate currency conversion accuracy."""
        expected_gbp = self.price_usd * self.usd_to_gbp_rate

        # Allow for small rounding differences (0.01%)
        tolerance = expected_gbp * Decimal("0.0001")
        if abs(self.price_gbp - expected_gbp) > tolerance:
            raise ValueError(
                f"GBP price ({self.price_gbp}) doesn't match conversion " f"({expected_gbp}) within tolerance"
            )

        return self


class APIErrorDetail(BaseModel):
    """Detailed API error information."""

    model_config = ConfigDict(validate_assignment=True)

    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(default=None, description="Field that caused the error")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")

    @field_validator("error_code")
    @classmethod
    def validate_error_code(cls, v: str) -> str:
        """Validate error code format."""
        v = v.upper().strip()
        if not v.replace("_", "").isalnum():
            raise ValueError("Error code must be alphanumeric with underscores")
        return v


class HealthCheckResponse(BaseModel):
    """API health check response."""

    model_config = ConfigDict(validate_assignment=True)

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Health check timestamp",
    )
    version: str = Field(..., description="API version")

    # Service health details
    database: Literal["connected", "disconnected", "error"] = Field(..., description="Database connection status")
    external_apis: dict[str, bool] = Field(default_factory=dict, description="External API availability")

    # Performance metrics
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    uptime_seconds: int = Field(..., ge=0, description="Service uptime in seconds")

    # Optional details
    details: dict[str, Any] = Field(default_factory=dict, description="Additional health check details")
