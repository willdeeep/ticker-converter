"""Market data models using Pydantic for validation."""

from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator


class VolatilityFlag(str, Enum):
    """Volatility classification for market data."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class MarketDataPoint(BaseModel):
    """Single market data point with validation."""

    timestamp: datetime = Field(..., description="Data timestamp")
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="Highest price")
    low: float = Field(..., gt=0, description="Lowest price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    @field_validator("high")
    @classmethod
    def validate_high_price(cls, v, info):
        """Validate that high price is reasonable compared to other prices."""
        if info.data:
            low = info.data.get("low")
            if low is not None and v < low:
                raise ValueError("High price cannot be less than low price")
        return v

    @model_validator(mode="after")
    def validate_price_relationships(self):
        """Validate price relationships after all fields are set."""
        # Check high >= low
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")

        # Check close is within high/low range
        if not (self.low <= self.close <= self.high):
            raise ValueError("Close price must be between low and high prices")

        return self

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class RawMarketData(BaseModel):
    """Raw market data from API sources."""

    data_points: list[MarketDataPoint] = Field(..., min_length=1)
    source: str = Field(..., description="Data source (e.g., 'alpha_vantage')")
    symbol: str = Field(..., description="Primary symbol for this dataset")
    data_type: str = Field(..., description="Type of data (daily, intraday, etc.)")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("data_points")
    @classmethod
    def validate_consistent_symbol(cls, v, info):
        """Ensure all data points have the same symbol."""
        if info.data and "symbol" in info.data:
            expected_symbol = info.data["symbol"]
            for point in v:
                if point.symbol != expected_symbol:
                    raise ValueError(
                        f"All data points must have symbol {expected_symbol}"
                    )
        return v

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        data = []
        for point in self.data_points:
            data.append(
                {
                    "Date": point.timestamp,
                    "Symbol": point.symbol,
                    "Open": point.open,
                    "High": point.high,
                    "Low": point.low,
                    "Close": point.close,
                    "Volume": point.volume,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("Date", inplace=True)
        return df


class CleanedMarketData(BaseModel):
    """Cleaned and validated market data."""

    raw_data: RawMarketData = Field(..., description="Original raw data")
    cleaned_dataframe: Optional[bytes] = Field(None, description="Serialized DataFrame")
    cleaning_applied: list[str] = Field(
        default_factory=list, description="Applied cleaning operations"
    )
    outliers_removed: int = Field(default=0, description="Number of outliers removed")
    missing_values_filled: int = Field(
        default=0, description="Number of missing values filled"
    )
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class FeatureEngineeredData(BaseModel):
    """Market data with engineered features."""

    cleaned_data: CleanedMarketData = Field(..., description="Cleaned source data")
    features_dataframe: Optional[bytes] = Field(
        None, description="Serialized DataFrame with features"
    )

    # Moving averages configuration
    ma_periods: list[int] = Field(default=[7, 30], description="Moving average periods")

    # Volatility configuration
    volatility_threshold_low: float = Field(
        default=0.02, description="Low volatility threshold"
    )
    volatility_threshold_moderate: float = Field(
        default=0.05, description="Moderate volatility threshold"
    )
    volatility_threshold_high: float = Field(
        default=0.10, description="High volatility threshold"
    )

    # Feature metadata
    features_created: list[str] = Field(
        default_factory=list, description="List of created features"
    )
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ValidationResult(BaseModel):
    """Result of data validation checks."""

    is_valid: bool = Field(..., description="Whether data passed validation")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def add_error(self, message: str) -> None:
        """Add a validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)
