# FastAPI with Direct SQL Setup

## Overview

This document describes the FastAPI implementation for the ticker-converter project, featuring direct SQL query execution against PostgreSQL. This approach eliminates complex ORM layers and provides maximum performance for analytical queries.

## Architecture Principles

### Direct SQL Approach
- **Raw SQL Queries**: Execute SQL directly against PostgreSQL using asyncpg
- **No ORM**: Avoid SQLAlchemy complexity for analytical workloads
- **Connection Pooling**: Efficient database connection management
- **Async Operations**: Non-blocking database operations for high concurrency
- **Type Safety**: Pydantic models for request/response validation

### API Design Philosophy
- **RESTful Endpoints**: Clear, predictable URL structure
- **Query Parameters**: Flexible filtering and pagination
- **JSON Responses**: Consistent data format
- **Error Handling**: Comprehensive error responses
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## Project Structure

```
src/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application setup
│   ├── database.py             # Database connection and pool management
│   ├── dependencies.py         # Dependency injection for database
│   ├── models/                 # Pydantic response models
│   │   ├── __init__.py
│   │   ├── stock.py            # Stock-related models
│   │   ├── currency.py         # Currency-related models
│   │   └── analytics.py        # Analytics response models
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── stocks.py           # Stock price endpoints
│   │   ├── currency.py         # Currency rate endpoints
│   │   ├── analytics.py        # Analytics endpoints
│   │   └── health.py           # Health check endpoints
│   └── sql/                    # SQL query files
│       ├── stocks/
│       │   ├── get_stock_prices.sql
│       │   ├── get_stock_performance.sql
│       │   └── get_price_history.sql
│       ├── currency/
│       │   ├── get_exchange_rates.sql
│       │   └── get_converted_prices.sql
│       └── analytics/
│           ├── top_performers.sql
│           ├── market_summary.sql
│           └── correlation_analysis.sql
```

## Core Implementation

### 1. FastAPI Application Setup

**File: `src/api/main.py`**
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import asyncio
import logging
from contextlib import asynccontextmanager

from .database import DatabaseManager
from .routers import stocks, currency, analytics, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database manager
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global db_manager

    # Startup
    logger.info("Starting ticker-converter API")
    db_manager = DatabaseManager()
    await db_manager.connect()
    logger.info("Database connection pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down ticker-converter API")
    await db_manager.disconnect()
    logger.info("Database connections closed")

# Create FastAPI application
app = FastAPI(
    title="Ticker Converter API",
    description="SQL-powered stock data and currency conversion API for Magnificent Seven stocks",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["Stocks"])
app.include_router(currency.router, prefix="/api/v1/currency", tags=["Currency"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Ticker Converter API",
        "version": "2.0.0",
        "description": "SQL-powered stock data and currency conversion API",
        "stocks": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "stocks": "/api/v1/stocks",
            "currency": "/api/v1/currency",
            "analytics": "/api/v1/analytics"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail="Internal server error. Please try again later."
    )
```

### 2. Database Connection Management

**File: `src/api/database.py`**
```python
import asyncpg
import asyncio
from typing import Optional, List, Dict, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL connection pool and query execution"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.sql_cache: Dict[str, str] = {}
        self.sql_directory = Path(__file__).parent / "sql"

    async def connect(self) -> None:
        """Initialize database connection pool"""
        try:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://ticker_user:password@localhost:5432/ticker_converter"
            )

            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=30
            )

            logger.info("Database connection pool created successfully")

        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    def load_sql(self, sql_file: str) -> str:
        """Load and cache SQL queries from files"""
        if sql_file not in self.sql_cache:
            sql_path = self.sql_directory / sql_file
            try:
                with open(sql_path, 'r') as f:
                    self.sql_cache[sql_file] = f.read()
                logger.debug(f"Loaded SQL from {sql_file}")
            except FileNotFoundError:
                logger.error(f"SQL file not found: {sql_file}")
                raise FileNotFoundError(f"SQL file not found: {sql_file}")
        
        return self.sql_cache[sql_file]

    async def fetch_all(self, sql_file: str, **params) -> List[Dict[str, Any]]:
        """Execute query and return all results"""
        sql = self.load_sql(sql_file)
        
        async with self.pool.acquire() as connection:
            try:
                result = await connection.fetch(sql, **params)
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"SQL: {sql}")
                logger.error(f"Params: {params}")
                raise

    async def fetch_one(self, sql_file: str, **params) -> Optional[Dict[str, Any]]:
        """Execute query and return single result"""
        sql = self.load_sql(sql_file)
        
        async with self.pool.acquire() as connection:
            try:
                result = await connection.fetchrow(sql, **params)
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"SQL: {sql}")
                logger.error(f"Params: {params}")
                raise

    async def execute(self, sql_file: str, **params) -> str:
        """Execute query without returning results"""
        sql = self.load_sql(sql_file)
        
        async with self.pool.acquire() as connection:
            try:
                result = await connection.execute(sql, **params)
                logger.info(f"Query executed: {result}")
                return result
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"SQL: {sql}")
                logger.error(f"Params: {params}")
                raise

# Global database manager instance
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    """Dependency injection for database manager"""
    return db_manager
```

### 3. Pydantic Response Models

**File: `src/api/models/stock.py`**
```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal

class StockPrice(BaseModel):
    """Individual stock price record"""
    symbol: str = Field(..., description="Stock symbol")
    date: date = Field(..., description="Trading date")
    open_usd: Decimal = Field(..., description="Opening price in USD")
    high_usd: Decimal = Field(..., description="High price in USD")
    low_usd: Decimal = Field(..., description="Low price in USD")
    close_usd: Decimal = Field(..., description="Closing price in USD")
    volume: int = Field(..., description="Trading volume")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class StockPriceWithCurrency(StockPrice):
    """Stock price with currency conversion"""
    close_gbp: Optional[Decimal] = Field(None, description="Closing price in GBP")
    exchange_rate: Optional[Decimal] = Field(None, description="USD/GBP exchange rate")

class StockPerformance(BaseModel):
    """Stock performance metrics"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector")
    current_price: Decimal = Field(..., description="Current price in USD")
    daily_change: Decimal = Field(..., description="Daily price change")
    daily_change_percent: Decimal = Field(..., description="Daily change percentage")
    weekly_change_percent: Optional[Decimal] = Field(None, description="Weekly change percentage")
    monthly_change_percent: Optional[Decimal] = Field(None, description="Monthly change percentage")
    volume: int = Field(..., description="Current volume")
    avg_volume_30d: Optional[int] = Field(None, description="30-day average volume")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class StockPriceHistory(BaseModel):
    """Historical stock price data"""
    symbol: str = Field(..., description="Stock symbol")
    prices: List[StockPrice] = Field(..., description="Historical prices")
    total_records: int = Field(..., description="Total number of records")
    date_range: dict = Field(..., description="Date range of data")

class StockListResponse(BaseModel):
    """Response for stock list endpoints"""
    stocks: List[str] = Field(..., description="Available stock symbols")
    total_count: int = Field(..., description="Total number of stocks")
    last_updated: datetime = Field(..., description="Last data update time")
```

**File: `src/api/models/analytics.py`**
```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional, Dict
from decimal import Decimal

class TopPerformer(BaseModel):
    """Top performing stock"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector")
    performance_metric: Decimal = Field(..., description="Performance metric (e.g., % change)")
    current_price: Decimal = Field(..., description="Current price")
    volume: int = Field(..., description="Trading volume")
    rank: int = Field(..., description="Performance rank")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class MarketSummary(BaseModel):
    """Market summary statistics"""
    date: date = Field(..., description="Summary date")
    total_stocks: int = Field(..., description="Number of stocks tracked")
    market_trend: str = Field(..., description="Overall market trend")
    avg_daily_change: Decimal = Field(..., description="Average daily change percentage")
    total_volume: int = Field(..., description="Total trading volume")
    gainers: int = Field(..., description="Number of gaining stocks")
    losers: int = Field(..., description="Number of losing stocks")
    top_performer: str = Field(..., description="Best performing stock")
    worst_performer: str = Field(..., description="Worst performing stock")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class CorrelationData(BaseModel):
    """Stock correlation analysis"""
    symbol1: str = Field(..., description="First stock symbol")
    symbol2: str = Field(..., description="Second stock symbol")
    correlation_coefficient: Decimal = Field(..., description="Correlation coefficient")
    period_days: int = Field(..., description="Analysis period in days")
    significance: str = Field(..., description="Statistical significance level")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class AnalyticsResponse(BaseModel):
    """Generic analytics response wrapper"""
    query_date: datetime = Field(..., description="Query execution time")
    data_date: date = Field(..., description="Latest data date")
    total_records: int = Field(..., description="Number of records returned")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
```

### 4. API Route Handlers

**File: `src/api/routers/stocks.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime
from ..database import DatabaseManager, get_database
from ..models.stock import StockPrice, StockPriceWithCurrency, StockPerformance, StockPriceHistory, StockListResponse
import time

router = APIRouter()

# Magnificent Seven stocks constant
MAGNIFICENT_SEVEN = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]

@router.get("/", response_model=StockListResponse)
async def get_available_stocks(db: DatabaseManager = Depends(get_database)):
    """Get list of available stocks"""
    try:
        result = await db.fetch_one("stocks/get_available_stocks.sql")
        
        return StockListResponse(
            stocks=MAGNIFICENT_SEVEN,
            total_count=len(MAGNIFICENT_SEVEN),
            last_updated=result["last_updated"] if result else datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stocks: {str(e)}")

@router.get("/{symbol}/prices", response_model=List[StockPrice])
async def get_stock_prices(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: DatabaseManager = Depends(get_database)
):
    """Get historical stock prices for a specific symbol"""

    # Validate symbol
    if symbol.upper() not in MAGNIFICENT_SEVEN:
        raise HTTPException(
            status_code=404, 
            detail=f"Stock {symbol} not found. Available stocks: {', '.join(MAGNIFICENT_SEVEN)}"
        )

    try:
        prices = await db.fetch_all(
            "stocks/get_stock_prices.sql",
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [StockPrice(**price) for price in prices]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock prices: {str(e)}")

@router.get("/{symbol}/prices/gbp", response_model=List[StockPriceWithCurrency])
async def get_stock_prices_gbp(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: DatabaseManager = Depends(get_database)
):
    """Get stock prices with GBP conversion"""

    if symbol.upper() not in MAGNIFICENT_SEVEN:
        raise HTTPException(
            status_code=404, 
            detail=f"Stock {symbol} not found. Available stocks: {', '.join(MAGNIFICENT_SEVEN)}"
        )

    try:
        prices = await db.fetch_all(
            "stocks/get_stock_prices_gbp.sql",
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [StockPriceWithCurrency(**price) for price in prices]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock prices with currency: {str(e)}")

@router.get("/{symbol}/performance", response_model=StockPerformance)
async def get_stock_performance(
    symbol: str,
    db: DatabaseManager = Depends(get_database)
):
    """Get current stock performance metrics"""

    if symbol.upper() not in MAGNIFICENT_SEVEN:
        raise HTTPException(
            status_code=404, 
            detail=f"Stock {symbol} not found. Available stocks: {', '.join(MAGNIFICENT_SEVEN)}"
        )

    try:
        performance = await db.fetch_one(
            "stocks/get_stock_performance.sql",
            symbol=symbol.upper()
        )
        
        if not performance:
            raise HTTPException(status_code=404, detail=f"No performance data found for {symbol}")
        
        return StockPerformance(**performance)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock performance: {str(e)}")

@router.get("/{symbol}/history", response_model=StockPriceHistory)
async def get_stock_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    db: DatabaseManager = Depends(get_database)
):
    """Get comprehensive stock price history"""

    if symbol.upper() not in MAGNIFICENT_SEVEN:
        raise HTTPException(
            status_code=404, 
            detail=f"Stock {symbol} not found. Available stocks: {', '.join(MAGNIFICENT_SEVEN)}"
        )

    try:
        history_data = await db.fetch_all(
            "stocks/get_price_history.sql",
            symbol=symbol.upper(),
            days=days
        )
        
        if not history_data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        # Get date range
        dates = [item["date"] for item in history_data]
        date_range = {
            "start_date": min(dates),
            "end_date": max(dates)
        }
        
        return StockPriceHistory(
            symbol=symbol.upper(),
            prices=[StockPrice(**item) for item in history_data],
            total_records=len(history_data),
            date_range=date_range
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock history: {str(e)}")
```

**File: `src/api/routers/analytics.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime
from ..database import DatabaseManager, get_database
from ..models.analytics import TopPerformer, MarketSummary, CorrelationData, AnalyticsResponse
import time

router = APIRouter()

@router.get("/top-performers", response_model=List[TopPerformer])
async def get_top_performers(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$", description="Performance period"),
    limit: int = Query(7, ge=1, le=20, description="Number of top performers"),
    db: DatabaseManager = Depends(get_database)
):
    """Get top performing stocks for specified period"""

    try:
        start_time = time.time()
        
        performers = await db.fetch_all(
            "analytics/top_performers.sql",
            period=period,
            limit=limit
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return [TopPerformer(**performer) for performer in performers]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top performers: {str(e)}")

@router.get("/market-summary", response_model=MarketSummary)
async def get_market_summary(
    summary_date: Optional[date] = Query(None, description="Date for summary (defaults to latest)"),
    db: DatabaseManager = Depends(get_database)
):
    """Get market summary for specified date"""

    try:
        summary = await db.fetch_one(
            "analytics/market_summary.sql",
            summary_date=summary_date
        )
        
        if not summary:
            raise HTTPException(status_code=404, detail="No market summary data found")
        
        return MarketSummary(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market summary: {str(e)}")

@router.get("/correlation", response_model=List[CorrelationData])
async def get_stock_correlations(
    symbol1: Optional[str] = Query(None, description="First stock symbol (optional)"),
    symbol2: Optional[str] = Query(None, description="Second stock symbol (optional)"),
    period_days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    min_correlation: float = Query(0.0, ge=-1.0, le=1.0, description="Minimum correlation threshold"),
    db: DatabaseManager = Depends(get_database)
):
    """Get stock correlation analysis"""

    try:
        correlations = await db.fetch_all(
            "analytics/correlation_analysis.sql",
            symbol1=symbol1.upper() if symbol1 else None,
            symbol2=symbol2.upper() if symbol2 else None,
            period_days=period_days,
            min_correlation=min_correlation
        )
        
        return [CorrelationData(**corr) for corr in correlations]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch correlations: {str(e)}")

@router.get("/sector-performance", response_model=List[dict])
async def get_sector_performance(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$", description="Performance period"),
    db: DatabaseManager = Depends(get_database)
):
    """Get sector-wise performance analysis"""

    try:
        sectors = await db.fetch_all(
            "analytics/sector_performance.sql",
            period=period
        )
        
        return sectors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sector performance: {str(e)}")
```

### 5. SQL Query Files

**File: `src/api/sql/stocks/get_stock_prices.sql`**
```sql
-- Get stock prices with optional date filtering
SELECT 
    s.symbol,
    d.date,
    p.open_usd,
    p.high_usd,
    p.low_usd,
    p.close_usd,
    p.volume
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE s.symbol = $1
  AND ($2::date IS NULL OR d.date >= $2::date)
  AND ($3::date IS NULL OR d.date <= $3::date)
ORDER BY d.date DESC
LIMIT $4;
```

**File: `src/api/sql/stocks/get_stock_prices_gbp.sql`**
```sql
-- Get stock prices with GBP conversion
SELECT 
    s.symbol,
    d.date,
    p.open_usd,
    p.high_usd,
    p.low_usd,
    p.close_usd,
    p.volume,
    ROUND(p.close_usd * COALESCE(cr.exchange_rate, 0.8), 4) as close_gbp,
    cr.exchange_rate
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
LEFT JOIN fact_currency_rates cr ON d.date_id = cr.date_id
    AND cr.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
    AND cr.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP')
WHERE s.symbol = $1
  AND ($2::date IS NULL OR d.date >= $2::date)
  AND ($3::date IS NULL OR d.date <= $3::date)
ORDER BY d.date DESC
LIMIT $4;
```

**File: `src/api/sql/analytics/top_performers.sql`**
```sql
-- Get top performing stocks by period
WITH performance_data AS (
    SELECT 
        s.symbol,
        s.company_name,
        s.sector,
        p_current.close_usd as current_price,
        p_current.volume,
        CASE 
            WHEN $1 = 'daily' THEN 
                ROUND(((p_current.close_usd - p_prev.close_usd) / p_prev.close_usd * 100), 2)
            WHEN $1 = 'weekly' THEN
                ROUND(((p_current.close_usd - p_week.close_usd) / p_week.close_usd * 100), 2)
            WHEN $1 = 'monthly' THEN
                ROUND(((p_current.close_usd - p_month.close_usd) / p_month.close_usd * 100), 2)
        END as performance_metric
    FROM dim_stocks s
    JOIN fact_stock_prices p_current ON s.stock_id = p_current.stock_id
    JOIN dim_dates d_current ON p_current.date_id = d_current.date_id
    LEFT JOIN fact_stock_prices p_prev ON s.stock_id = p_prev.stock_id
    LEFT JOIN dim_dates d_prev ON p_prev.date_id = d_prev.date_id 
        AND d_prev.date = d_current.date - INTERVAL '1 day'
    LEFT JOIN fact_stock_prices p_week ON s.stock_id = p_week.stock_id
    LEFT JOIN dim_dates d_week ON p_week.date_id = d_week.date_id 
        AND d_week.date = d_current.date - INTERVAL '7 days'
    LEFT JOIN fact_stock_prices p_month ON s.stock_id = p_month.stock_id
    LEFT JOIN dim_dates d_month ON p_month.date_id = d_month.date_id 
        AND d_month.date = d_current.date - INTERVAL '30 days'
    WHERE d_current.date = (SELECT MAX(date) FROM dim_dates WHERE date IN (SELECT DISTINCT date_id FROM fact_stock_prices))
)
SELECT 
    symbol,
    company_name,
    sector,
    performance_metric,
    current_price,
    volume,
    ROW_NUMBER() OVER (ORDER BY performance_metric DESC) as rank
FROM performance_data
WHERE performance_metric IS NOT NULL
ORDER BY performance_metric DESC
LIMIT $2;
```

### 6. Health Check and Monitoring

**File: `src/api/routers/health.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from ..database import DatabaseManager, get_database
import asyncio

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ticker-converter-api",
        "version": "2.0.0"
    }

@router.get("/database")
async def database_health(db: DatabaseManager = Depends(get_database)):
    """Database connectivity health check"""
    try:
        start_time = datetime.now()
        
        # Simple query to test database connectivity
        result = await db.fetch_one("health/database_check.sql")
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "database": "connected",
            "response_time_ms": round(response_time, 2),
            "timestamp": datetime.now().isoformat(),
            "latest_data_date": result["latest_date"] if result else None,
            "total_records": result["total_records"] if result else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/data")
async def data_health(db: DatabaseManager = Depends(get_database)):
    """Data freshness and quality health check"""
    try:
        result = await db.fetch_one("health/data_quality_check.sql")
        
        return {
            "status": "healthy",
            "data_quality": "good",
            "latest_data_date": result["latest_date"],
            "total_stocks": result["total_stocks"],
            "total_records": result["total_records"],
            "data_age_days": result["data_age_days"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "data_quality": "poor",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
```

**File: `src/api/sql/health/database_check.sql`**
```sql
-- Basic database connectivity and data check
SELECT 
    MAX(d.date) as latest_date,
    COUNT(*) as total_records
FROM fact_stock_prices p
JOIN dim_dates d ON p.date_id = d.date_id;
```

**File: `src/api/sql/health/data_quality_check.sql`**
```sql
-- Comprehensive data quality check
SELECT 
    MAX(d.date) as latest_date,
    COUNT(DISTINCT s.symbol) as total_stocks,
    COUNT(*) as total_records,
    CURRENT_DATE - MAX(d.date) as data_age_days
FROM fact_stock_prices p
JOIN dim_dates d ON p.date_id = d.date_id
JOIN dim_stocks s ON p.stock_id = s.stock_id;
```

## Configuration and Deployment

### 1. Environment Variables

**File: `.env`**
```bash
# Database Configuration
DATABASE_URL=postgresql://ticker_user:password@localhost:5432/ticker_converter
DATABASE_MIN_CONNECTIONS=5
DATABASE_MAX_CONNECTIONS=20

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 2. Docker Configuration

**File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY sql/ ./sql/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Development Setup

**File: `run_dev.py`**
```python
#!/usr/bin/env python3
"""Development server runner"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    # Run development server
    uvicorn.run(
        "src.api.main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
        reload_dirs=["src"],
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
```

### 4. Production Deployment

**File: `gunicorn.conf.py`**
```python
"""Gunicorn configuration for production deployment"""

import os
import multiprocessing

# Server socket
bind = f"{os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', 8000)}"
backlog = 2048

# Worker processes
workers = int(os.getenv('API_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeouts
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'ticker-converter-api'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (for production with HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
```

## Performance Optimization

### 1. Connection Pooling
```python
# Optimized pool configuration
self.pool = await asyncpg.create_pool(
    database_url,
    min_size=5,                    # Minimum connections
    max_size=20,                   # Maximum connections
    max_queries=50000,             # Queries per connection
    max_inactive_connection_lifetime=300,  # 5 minutes
    command_timeout=30,            # 30 second query timeout
    server_settings={
        'application_name': 'ticker-converter-api',
        'tcp_keepalives_idle': '600',
        'tcp_keepalives_interval': '30',
        'tcp_keepalives_count': '3',
    }
)
```

### 2. Query Optimization
```sql
-- Use appropriate indexes
CREATE INDEX CONCURRENTLY idx_fact_stock_prices_symbol_date 
ON fact_stock_prices(stock_id, date_id DESC);

CREATE INDEX CONCURRENTLY idx_fact_stock_prices_date 
ON fact_stock_prices(date_id DESC);

-- Use query hints for complex queries
/*+ IndexScan(p idx_fact_stock_prices_symbol_date) */
SELECT ... FROM fact_stock_prices p ...
```

### 3. Caching Strategy
```python
import aioredis
from functools import wraps

# Redis caching decorator
def cache_result(expiry: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis.setex(cache_key, expiry, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

# Apply to expensive endpoints
@cache_result(expiry=600)  # 10 minutes
async def get_top_performers(...):
    ...
```

## Testing Strategy

### 1. Unit Tests
```python
import pytest
from httpx import AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_get_stock_prices():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/stocks/AAPL/prices?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10
    assert data[0]["symbol"] == "AAPL"

@pytest.mark.asyncio
async def test_invalid_stock_symbol():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/stocks/INVALID/prices")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
```

### 2. Integration Tests
```python
@pytest.mark.asyncio
async def test_database_integration():
    """Test database connectivity and basic queries"""
    db = DatabaseManager()
    await db.connect()

    try:
        result = await db.fetch_all("stocks/get_stock_prices.sql", 
                                   symbol="AAPL", start_date=None, 
                                   end_date=None, limit=1)
        assert len(result) > 0
        assert result[0]["symbol"] == "AAPL"
    finally:
        await db.disconnect()
```

## Monitoring and Observability

### 1. Metrics Collection
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 2. Structured Logging
```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    logger.info(
        "api_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=time.time() - start_time,
        user_agent=request.headers.get("user-agent"),
        remote_addr=request.client.host
    )

    return response
```

This FastAPI implementation provides a high-performance, SQL-centric API that directly executes optimized queries against PostgreSQL, eliminating the complexity of ORMs while maintaining type safety and comprehensive documentation. The architecture supports the Magnificent Seven stocks with robust error handling, monitoring, and scalability features.
