"""Response models for API endpoints."""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class StockPerformance(BaseModel):
    """Stock performance data for API responses."""

    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    price_usd: float = Field(..., description="Closing price in USD")
    price_gbp: float | None = Field(None, description="Closing price in GBP")
    daily_return: float | None = Field(None, description="Daily return percentage")
    volume: int = Field(..., description="Trading volume")
    trade_date: date = Field(..., description="Trading date")
    performance_rank: int | None = Field(None, description="Performance ranking")


class CurrencyConversion(BaseModel):
    """Currency conversion data for stocks."""

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    price_usd: float = Field(..., description="Price in USD")
    usd_to_gbp_rate: float = Field(..., description="USD to GBP exchange rate")
    price_gbp: float = Field(..., description="Price in GBP")
    rate_date: date = Field(..., description="Exchange rate date")


class DailySummary(BaseModel):
    """Daily summary statistics for all stocks."""

    summary_date: date = Field(..., description="Summary date")
    stocks_count: int = Field(..., description="Number of stocks")
    avg_closing_price_usd: float = Field(..., description="Average closing price USD")
    min_closing_price_usd: float = Field(..., description="Minimum closing price USD")
    max_closing_price_usd: float = Field(..., description="Maximum closing price USD")
    avg_daily_return_pct: float | None = Field(None, description="Average daily return %")
    min_daily_return_pct: float | None = Field(None, description="Minimum daily return %")
    max_daily_return_pct: float | None = Field(None, description="Maximum daily return %")
    total_volume: int = Field(..., description="Total trading volume")
    avg_volume: int = Field(..., description="Average trading volume")
    avg_closing_price_gbp: float | None = Field(None, description="Average closing price GBP")
    usd_to_gbp_rate: float | None = Field(None, description="USD to GBP rate")


class StockSummary(BaseModel):
    """Summary information for a single stock."""

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    latest_price_usd: float = Field(..., description="Latest price in USD")
    latest_price_gbp: float | None = Field(None, description="Latest price in GBP")
    latest_return: float | None = Field(None, description="Latest daily return %")
    avg_volume_30d: int = Field(..., description="30-day average volume")
    price_change_30d: float | None = Field(None, description="30-day price change %")
    last_updated: date = Field(..., description="Last update date")


class TopPerformerStock(BaseModel):
    """Top performing stock data for Magnificent Seven companies."""

    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    price_usd: float = Field(..., description="Current closing price in USD")
    price_gbp: float | None = Field(None, description="Current closing price in GBP")
    daily_return: float | None = Field(None, description="Daily return percentage")
    volume: int = Field(..., description="Trading volume")
    trade_date: date = Field(..., description="Trading date")
    performance_rank: int | None = Field(None, description="Performance ranking (1-3)")


class StockPerformanceDetails(BaseModel):
    """Detailed performance metrics for Magnificent Seven companies."""

    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    price_usd: float = Field(..., description="Current closing price in USD")
    price_gbp: float | None = Field(None, description="Current closing price in GBP")
    daily_return: float | None = Field(None, description="Daily return percentage")
    volume: int = Field(..., description="Current trading volume")
    trade_date: date = Field(..., description="Trading date")
    avg_price_30d_usd: float | None = Field(None, description="30-day average price in USD")
    avg_volume_30d: int | None = Field(None, description="30-day average volume")
    price_change_30d_pct: float | None = Field(None, description="30-day price change percentage")
    volatility_30d: float | None = Field(None, description="30-day volatility (standard deviation)")
    performance_rank: int | None = Field(None, description="Performance ranking")


class StockDataWithCurrency(BaseModel):
    """Stock data with side-by-side USD and GBP pricing based on daily exchange rates."""

    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    trade_date: date = Field(..., description="Trading date")
    price_usd: float = Field(..., description="Closing price in USD")
    price_gbp: float | None = Field(None, description="Closing price in GBP")
    usd_to_gbp_rate: float | None = Field(None, description="USD to GBP exchange rate used")
    volume: int = Field(..., description="Trading volume")
    daily_return: float | None = Field(None, description="Daily return percentage")
    market_cap_usd: float | None = Field(None, description="Market capitalization in USD")
    market_cap_gbp: float | None = Field(None, description="Market capitalization in GBP")

    @field_validator("price_usd")
    @classmethod
    def validate_price_usd(cls, v: float) -> float:
        """Validate that USD price is positive."""
        if v <= 0:
            raise ValueError("price_usd must be positive")
        return v

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Validate that volume is non-negative."""
        if v < 0:
            raise ValueError("volume must be non-negative")
        return v

    @field_validator("price_gbp")
    @classmethod
    def validate_price_gbp(cls, v: float | None) -> float | None:
        """Validate that GBP price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("price_gbp must be positive if provided")
        return v

    @field_validator("usd_to_gbp_rate")
    @classmethod
    def validate_exchange_rate(cls, v: float | None) -> float | None:
        """Validate that exchange rate is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("usd_to_gbp_rate must be positive if provided")
        return v
