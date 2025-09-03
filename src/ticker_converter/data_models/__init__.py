"""Data models for financial market data with comprehensive validation.

This package provides type-safe, validated data models for:
- Market data (OHLCV stock data)
- Currency exchange rates
- API responses and requests
- Database entities

All models use Pydantic for validation and are designed for Python 3.11
with modern type annotations and comprehensive business rule validation.
"""

from .api_models import (
    APIResponse,
    APIStatus,
    CurrencyConversionDetails,
    EnhancedStockPerformance,
    HealthCheckResponse,
    PaginationInfo,
    PaginationParams,
    SortOrder,
    StockQueryParams,
)
from .market_data import CurrencyRate, CurrencyRateCollection, MarketDataCollection, MarketDataPoint, RawMarketData

__all__ = [
    # Core market data models
    "MarketDataPoint",
    "RawMarketData",
    "CurrencyRate",
    # Type aliases for collections
    "MarketDataCollection",
    "CurrencyRateCollection",
    # API models
    "APIResponse",
    "APIStatus",
    "EnhancedStockPerformance",
    "CurrencyConversionDetails",
    "HealthCheckResponse",
    "PaginationInfo",
    "PaginationParams",
    "SortOrder",
    "StockQueryParams",
]

# Version info for the data models package
__version__ = "2.0.0"
