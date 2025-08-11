"""Response models for API endpoints."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class StockPerformance(BaseModel):
    """Stock performance data for API responses."""
    
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    price_usd: float = Field(..., description="Closing price in USD")
    price_gbp: Optional[float] = Field(None, description="Closing price in GBP")
    daily_return: Optional[float] = Field(None, description="Daily return percentage")
    volume: int = Field(..., description="Trading volume")
    trade_date: date = Field(..., description="Trading date")
    performance_rank: Optional[int] = Field(None, description="Performance ranking")


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
    avg_daily_return_pct: Optional[float] = Field(None, description="Average daily return %")
    min_daily_return_pct: Optional[float] = Field(None, description="Minimum daily return %")
    max_daily_return_pct: Optional[float] = Field(None, description="Maximum daily return %")
    total_volume: int = Field(..., description="Total trading volume")
    avg_volume: int = Field(..., description="Average trading volume")
    avg_closing_price_gbp: Optional[float] = Field(None, description="Average closing price GBP")
    usd_to_gbp_rate: Optional[float] = Field(None, description="USD to GBP rate")


class StockSummary(BaseModel):
    """Summary information for a single stock."""
    
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    latest_price_usd: float = Field(..., description="Latest price in USD")
    latest_price_gbp: Optional[float] = Field(None, description="Latest price in GBP")
    latest_return: Optional[float] = Field(None, description="Latest daily return %")
    avg_volume_30d: int = Field(..., description="30-day average volume")
    price_change_30d: Optional[float] = Field(None, description="30-day price change %")
    last_updated: date = Field(..., description="Last update date")
