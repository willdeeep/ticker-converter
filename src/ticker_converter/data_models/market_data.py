"""Market data models using Pydantic for validation."""

from datetime import datetime

import pandas as pd
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


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
    def validate_high_price(cls, v: float, info: ValidationInfo) -> float:
        """Validate that high price is reasonable compared to other prices."""
        if info.data:
            low = info.data.get("low")
            if low is not None and v < low:
                raise ValueError("High price cannot be less than low price")
        return v

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "MarketDataPoint":
        """Validate price relationships after all fields are set."""
        # Check high >= low
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")

        # Check close is within high/low range
        if not self.low <= self.close <= self.high:
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
    def validate_consistent_symbol(cls, v: list[MarketDataPoint], info: ValidationInfo) -> list[MarketDataPoint]:
        """Ensure all data points have the same symbol."""
        if info.data and "symbol" in info.data:
            expected_symbol = info.data["symbol"]
            for point in v:
                if point.symbol != expected_symbol:
                    raise ValueError(f"All data points must have symbol {expected_symbol}")
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


class CurrencyRate(BaseModel):
    """Currency exchange rate data."""

    timestamp: datetime = Field(..., description="Rate timestamp")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    rate: float = Field(..., gt=0, description="Exchange rate")
    source: str = Field(..., description="Data source")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("from_currency", "to_currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate currency codes are uppercase."""
        return v.upper()

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
