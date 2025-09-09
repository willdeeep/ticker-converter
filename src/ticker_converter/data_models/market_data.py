"""Market data models using Pydantic for validation and type safety.

This module provides comprehensive data models for financial market data with:
- Strict validation rules for financial data integrity
- Business logic validation for market data relationships
- Type safety with Python 3.11 features
- Comprehensive error handling and meaningful error messages
- Support for serialization/deserialization with external APIs
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MarketDataPoint(BaseModel):
    """Single market data point with comprehensive validation.

    Represents a single trading day's data for a stock with strict validation
    to ensure data integrity and compliance with financial market standards.

    Attributes:
        timestamp: Trading day timestamp (automatically normalized to UTC)
        symbol: Stock symbol (1-10 characters, alphanumeric only)
        open: Opening price (must be positive)
        high: Highest price during trading (>= low, open, close)
        low: Lowest price during trading (<= high, open, close)
        close: Closing price (between low and high)
        volume: Trading volume (non-negative integer)

    Example:
        >>> data_point = MarketDataPoint(
        ...     timestamp=datetime(2025, 8, 14),
        ...     symbol="AAPL",
        ...     open=150.00,
        ...     high=155.50,
        ...     low=149.75,
        ...     close=154.25,
        ...     volume=1500000
        ... )
    """

    model_config = ConfigDict(
        # Modern Pydantic v2 configuration
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        json_encoders={
            datetime: datetime.isoformat,
            Decimal: float,
        },
    )

    timestamp: datetime = Field(
        ...,
        description="Trading day timestamp (UTC)",
        examples=[datetime(2025, 8, 14, tzinfo=UTC)],
    )
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z0-9.-]+$",
        description="Stock symbol (uppercase alphanumeric)",
        examples=["AAPL", "GOOGL", "MSFT"],
    )
    open: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Opening price in USD",
        examples=[150.00],
    )
    high: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Highest price during trading",
        examples=[155.50],
    )
    low: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Lowest price during trading",
        examples=[149.75],
    )
    close: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Closing price",
        examples=[154.25],
    )
    volume: int = Field(
        ...,
        ge=0,
        le=10_000_000_000,  # 10 billion max volume
        description="Trading volume (number of shares)",
        examples=[1500000],
    )

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, v: datetime) -> datetime:
        """Normalize timestamp to UTC and validate reasonable date range."""
        # Ensure UTC timezone
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        elif v.tzinfo != UTC:
            v = v.astimezone(UTC)

        # Validate reasonable date range (not too far in past/future)
        now = datetime.now(UTC)
        if v.year < 1980:
            raise ValueError("Timestamp cannot be before 1980")
        if v > now:
            raise ValueError("Timestamp cannot be in the future")

        return v

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol."""
        v = v.upper().strip()

        # Check for common invalid patterns
        if v in ["", "NULL", "NONE", "N/A"]:
            raise ValueError("Invalid symbol")

        # Validate format
        if not v.replace(".", "").replace("-", "").isalnum():
            raise ValueError("Symbol must be alphanumeric with optional dots/hyphens")

        return v

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_price_precision(cls, v: Decimal) -> Decimal:
        """Validate price precision and reasonable ranges."""
        # Check for reasonable price range (0.01 to 100,000)
        if v < Decimal("0.01"):
            raise ValueError("Price must be at least $0.01")
        if v > Decimal("100000.00"):
            raise ValueError("Price cannot exceed $100,000")

        return v

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "MarketDataPoint":
        """Validate price relationships and business rules."""
        # Basic OHLC validation
        if self.high < self.low:
            raise ValueError(f"High price ({self.high}) cannot be less than low price ({self.low})")

        # High must be >= all other prices
        if self.high < self.open:
            raise ValueError(f"High price ({self.high}) cannot be less than open price ({self.open})")
        if self.high < self.close:
            raise ValueError(f"High price ({self.high}) cannot be less than close price ({self.close})")

        # Low must be <= all other prices
        if self.low > self.open:
            raise ValueError(f"Low price ({self.low}) cannot be greater than open price ({self.open})")
        if self.low > self.close:
            raise ValueError(f"Low price ({self.low}) cannot be greater than close price ({self.close})")

        # Additional business rules
        price_range = self.high - self.low
        avg_price = (self.high + self.low) / 2

        # Check for suspicious price movements (>50% daily range)
        if price_range > (avg_price * Decimal("0.5")):
            # This is a warning, not an error, for extremely volatile days
            pass  # Could log a warning here in production

        # Check for zero-volume with price movement
        if self.volume == 0 and self.open != self.close:
            raise ValueError("Cannot have price movement with zero volume")

        return self

    def daily_return_percentage(self) -> Decimal | None:
        """Calculate daily return percentage.

        Returns:
            Daily return as percentage, or None if open price is zero
        """
        if self.open == 0:
            return None
        return ((self.close - self.open) / self.open) * 100

    def price_volatility(self) -> Decimal:
        """Calculate intraday price volatility.

        Returns:
            Volatility as percentage of average price
        """
        avg_price = (self.high + self.low) / 2
        if avg_price == 0:
            return Decimal("0")
        return ((self.high - self.low) / avg_price) * 100

    def is_gap_up(self, threshold: Decimal = Decimal("2.0")) -> bool:
        """Check if stock gapped up at open (open > previous close by threshold %).

        Args:
            threshold: Gap percentage threshold

        Note:
            This method requires previous day's close price for full functionality.
            Current implementation checks if open is significantly higher than low.
        """
        # Simplified implementation - in practice would compare to previous close
        gap_percentage = ((self.open - self.low) / self.low) * 100
        return gap_percentage > threshold

    def is_gap_down(self, threshold: Decimal = Decimal("2.0")) -> bool:
        """Check if stock gapped down at open (open < previous close by threshold %).

        Args:
            threshold: Gap percentage threshold
        """
        # Simplified implementation - in practice would compare to previous close
        gap_percentage = ((self.high - self.open) / self.open) * 100
        return gap_percentage > threshold


class RawMarketData(BaseModel):
    """Raw market data from API sources with comprehensive validation.

    Container for multiple market data points from external APIs with
    metadata and validation to ensure data consistency and quality.

    Attributes:
        data_points: List of market data points (must be non-empty)
        source: Data source identifier (e.g., 'alpha_vantage', 'yahoo')
        symbol: Primary symbol for this dataset (must match all data points)
        data_type: Type of data ('daily', 'intraday', 'weekly', 'monthly')
        retrieved_at: UTC timestamp when data was retrieved
        api_call_metadata: Optional metadata about the API call

    Example:
        >>> raw_data = RawMarketData(
        ...     data_points=[data_point1, data_point2],
        ...     source="alpha_vantage",
        ...     symbol="AAPL",
        ...     data_type="daily"
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",  # Prevent extra fields
    )

    data_points: list[MarketDataPoint] = Field(
        ...,
        min_length=1,
        max_length=10000,  # Reasonable limit for batch processing
        description="List of market data points",
    )
    source: Literal["alpha_vantage", "yahoo", "polygon", "iex", "manual"] = Field(
        ..., description="Data source identifier"
    )
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z0-9.-]+$",
        description="Primary symbol for this dataset",
    )
    data_type: Literal["daily", "intraday", "weekly", "monthly"] = Field(..., description="Type of market data")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when data was retrieved",
    )
    api_call_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata about the API call (rate limits, etc.)",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.upper().strip()

    @field_validator("data_points")
    @classmethod
    def validate_data_points_order(cls, v: list[MarketDataPoint]) -> list[MarketDataPoint]:
        """Validate data points are in chronological order."""
        if len(v) <= 1:
            return v

        # Sort by timestamp to ensure chronological order
        sorted_points = sorted(v, key=lambda x: x.timestamp)

        # Check for duplicates
        timestamps = [point.timestamp for point in sorted_points]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("Duplicate timestamps found in data points")

        return sorted_points

    @model_validator(mode="after")
    def validate_symbol_consistency(self) -> "RawMarketData":
        """Validate all data points have consistent symbol."""
        expected_symbol = self.symbol

        for i, point in enumerate(self.data_points):
            if point.symbol != expected_symbol:
                raise ValueError(f"Data point {i} has symbol '{point.symbol}' " f"but expected '{expected_symbol}'")

        return self

    @model_validator(mode="after")
    def validate_data_quality(self) -> "RawMarketData":
        """Perform additional data quality checks."""
        if not self.data_points:
            return self

        # Check for reasonable time gaps in daily data
        if self.data_type == "daily" and len(self.data_points) > 1:
            # Sort points by timestamp
            sorted_points = sorted(self.data_points, key=lambda x: x.timestamp)

            for i in range(1, len(sorted_points)):
                time_diff = sorted_points[i].timestamp - sorted_points[i - 1].timestamp
                days_diff = time_diff.days

                # Allow for weekends and holidays, but flag suspicious gaps
                if days_diff > 10:  # More than 10 days gap
                    # This could be a warning rather than an error
                    pass  # Log warning in production

        # Check for outliers in volume
        if len(self.data_points) > 2:
            volumes = [point.volume for point in self.data_points]
            avg_volume = sum(volumes) / len(volumes)

            for point in self.data_points:
                # Flag extreme volume outliers (100x average)
                if avg_volume > 0 and point.volume > (avg_volume * 100):
                    # This could be a warning rather than an error
                    pass  # Log warning in production

        return self

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame with enhanced functionality.

        Returns:
            DataFrame with Date index and OHLCV columns, plus calculated fields
        """
        if not self.data_points:
            return pd.DataFrame()

        data = []
        for point in self.data_points:
            data.append(
                {
                    "Date": point.timestamp,
                    "Symbol": point.symbol,
                    "Open": float(point.open),
                    "High": float(point.high),
                    "Low": float(point.low),
                    "Close": float(point.close),
                    "Volume": point.volume,
                    "Daily_Return_Pct": float(point.daily_return_percentage() or 0),
                    "Volatility_Pct": float(point.price_volatility()),
                    "Source": self.source,
                    "Data_Type": self.data_type,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)  # Ensure chronological order

        return df

    def get_latest_point(self) -> MarketDataPoint | None:
        """Get the most recent data point.

        Returns:
            Latest market data point or None if no data
        """
        if not self.data_points:
            return None
        return max(self.data_points, key=lambda x: x.timestamp)

    def get_date_range(self) -> tuple[datetime, datetime] | None:
        """Get the date range of the data.

        Returns:
            Tuple of (earliest, latest) timestamps or None if no data
        """
        if not self.data_points:
            return None

        timestamps = [point.timestamp for point in self.data_points]
        return (min(timestamps), max(timestamps))

    def calculate_summary_stats(self) -> dict[str, Any]:
        """Calculate summary statistics for the dataset.

        Returns:
            Dictionary with summary statistics
        """
        if not self.data_points:
            return {}

        prices = [float(point.close) for point in self.data_points]
        volumes = [point.volume for point in self.data_points]

        date_range = self.get_date_range()

        return {
            "symbol": self.symbol,
            "source": self.source,
            "data_type": self.data_type,
            "point_count": len(self.data_points),
            "date_range": {
                "start": date_range[0].isoformat() if date_range else None,
                "end": date_range[1].isoformat() if date_range else None,
            },
            "price_stats": {
                "min_close": min(prices),
                "max_close": max(prices),
                "avg_close": sum(prices) / len(prices),
                "latest_close": prices[-1] if prices else None,
            },
            "volume_stats": {
                "min_volume": min(volumes),
                "max_volume": max(volumes),
                "avg_volume": sum(volumes) / len(volumes),
                "total_volume": sum(volumes),
            },
            # pylint: disable=no-member  # Pydantic field access
            "retrieved_at": self.retrieved_at.isoformat(),
        }


class CurrencyRate(BaseModel):
    """Currency exchange rate data with comprehensive validation.

    Represents currency exchange rates with validation for financial accuracy
    and support for historical rate tracking and conversion calculations.

    Attributes:
        timestamp: Rate timestamp (UTC)
        from_currency: Source currency code (ISO 4217)
        to_currency: Target currency code (ISO 4217)
        rate: Exchange rate (from_currency to to_currency)
        bid_rate: Optional bid rate for spread calculation
        ask_rate: Optional ask rate for spread calculation
        source: Data source identifier
        retrieved_at: UTC timestamp when rate was retrieved

    Example:
        >>> rate = CurrencyRate(
        ...     timestamp=datetime(2025, 8, 14),
        ...     from_currency="USD",
        ...     to_currency="GBP",
        ...     rate=0.7850,
        ...     source="alpha_vantage"
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_encoders={
            datetime: datetime.isoformat,
            Decimal: float,
        },
    )

    timestamp: datetime = Field(
        ...,
        description="Rate timestamp (UTC)",
        examples=[datetime(2025, 8, 14, tzinfo=UTC)],
    )
    from_currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="Source currency code (ISO 4217)",
        examples=["USD", "EUR", "GBP"],
    )
    to_currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="Target currency code (ISO 4217)",
        examples=["GBP", "USD", "EUR"],
    )
    rate: Decimal = Field(
        ...,
        gt=0,
        max_digits=12,
        decimal_places=6,
        description="Exchange rate (from_currency to to_currency)",
        examples=[0.785000],
    )
    bid_rate: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=6,
        description="Bid rate for spread calculation",
    )
    ask_rate: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=6,
        description="Ask rate for spread calculation",
    )
    source: Literal["alpha_vantage", "yahoo", "xe", "fixer", "manual"] = Field(
        ..., description="Data source identifier"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when rate was retrieved",
    )

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, v: datetime) -> datetime:
        """Normalize timestamp to UTC and validate date range."""
        # Ensure UTC timezone
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        elif v.tzinfo != UTC:
            v = v.astimezone(UTC)

        # Validate reasonable date range
        now = datetime.now(UTC)
        if v.year < 1990:  # Modern currency data starts around 1990
            raise ValueError("Currency rate timestamp cannot be before 1990")
        if v > now:
            raise ValueError("Currency rate timestamp cannot be in the future")

        return v

    @field_validator("from_currency", "to_currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate and normalize currency codes."""
        v = v.upper().strip()

        # Check format
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency code must be exactly 3 alphabetic characters")

        # Validate against known currencies (basic set)
        valid_currencies = {
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CHF",
            "CAD",
            "AUD",
            "NZD",
            "CNY",
            "INR",
            "BRL",
            "MXN",
            "ZAR",
            "SGD",
            "HKD",
            "NOK",
            "SEK",
            "DKK",
            "PLN",
            "CZK",
            "HUF",
            "RUB",
            "TRY",
            "KRW",
        }
        if v not in valid_currencies:
            # Log warning but do not fail - allows for new/exotic currencies
            pass  # In production: logger.warning("Unknown currency code: %s", v)

        return v

    @field_validator("rate", "bid_rate", "ask_rate")
    @classmethod
    def validate_exchange_rate(cls, v: Decimal | None) -> Decimal | None:
        """Validate exchange rate values."""
        if v is None:
            return v

        # Check for reasonable exchange rate range
        if v < Decimal("0.000001"):  # Very small rates (e.g., JPY pairs)
            raise ValueError("Exchange rate too small (minimum 0.000001)")
        if v > Decimal("1000000"):  # Very large rates (hyperinflation scenarios)
            raise ValueError("Exchange rate too large (maximum 1,000,000)")

        return v

    @model_validator(mode="after")
    def validate_currency_pair(self) -> "CurrencyRate":
        """Validate currency pair and rate relationships."""
        # Cannot convert currency to itself
        if self.from_currency == self.to_currency:
            raise ValueError("Cannot convert currency to itself")

        # Validate bid/ask spread if both are provided
        if self.bid_rate is not None and self.ask_rate is not None:
            if self.bid_rate >= self.ask_rate:
                raise ValueError("Bid rate must be less than ask rate")

            # Check if main rate is within bid/ask spread
            if not self.bid_rate <= self.rate <= self.ask_rate:
                raise ValueError("Exchange rate must be between bid and ask rates")

            # Check for reasonable spread (should be < 10% for major pairs)
            spread_pct = ((self.ask_rate - self.bid_rate) / self.rate) * 100
            if spread_pct > 10:
                # Warning for wide spreads, but do not fail
                pass  # Log warning in production

        return self

    def inverse_rate(self) -> "CurrencyRate":
        """Calculate the inverse exchange rate.

        Returns:
            New CurrencyRate object with inverted currencies and rate
        """
        # Calculate inverse with proper precision handling
        inverse_rate_value = (Decimal("1") / self.rate).quantize(Decimal("0.000001"))

        inverse_bid = None
        inverse_ask = None
        if self.ask_rate is not None:
            inverse_bid = (Decimal("1") / self.ask_rate).quantize(Decimal("0.000001"))
        if self.bid_rate is not None:
            inverse_ask = (Decimal("1") / self.bid_rate).quantize(Decimal("0.000001"))

        return CurrencyRate(
            timestamp=self.timestamp,
            from_currency=self.to_currency,
            to_currency=self.from_currency,
            rate=inverse_rate_value,
            bid_rate=inverse_bid,
            ask_rate=inverse_ask,
            source=self.source,
            retrieved_at=self.retrieved_at,
        )

    def convert_amount(self, amount: Decimal, use_bid_ask: bool = False) -> Decimal:
        """Convert an amount using this exchange rate.

        Args:
            amount: Amount in from_currency to convert
            use_bid_ask: If True and bid_rate available, use bid_rate (conservative)

        Returns:
            Amount in to_currency
        """
        if use_bid_ask and self.bid_rate is not None:
            # Use bid rate for conservative conversion
            return amount * self.bid_rate
        return amount * self.rate

    def spread_percentage(self) -> Decimal | None:
        """Calculate bid-ask spread as percentage.

        Returns:
            Spread percentage or None if bid/ask not available
        """
        if self.bid_rate is None or self.ask_rate is None:
            return None
        return ((self.ask_rate - self.bid_rate) / self.rate) * 100

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if the rate is stale (too old).

        Args:
            max_age_hours: Maximum age in hours before considering stale

        Returns:
            True if rate is older than max_age_hours
        """
        now = datetime.now(UTC)
        age = now - self.timestamp
        return age.total_seconds() > (max_age_hours * 3600)

    def get_currency_pair_name(self) -> str:
        """Get standardized currency pair name.

        Returns:
            Currency pair in format "USDGBP"
        """
        return f"{self.from_currency}{self.to_currency}"


# Type aliases for better code readability
MarketDataCollection = list[MarketDataPoint]
CurrencyRateCollection = list[CurrencyRate]
