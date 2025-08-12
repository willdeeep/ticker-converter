# Local Development Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the ticker-converter application on your local machine. The ticker-converter is a SQL-centric ETL pipeline for NYSE stock market data analysis featuring FastAPI, PostgreSQL, and optional Apache Airflow orchestration.

## What You'll Build

By following this guide, you'll have a fully functional local environment that can:
- **Fetch stock data** for the Magnificent Seven companies (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA)
- **Convert USD prices to GBP** using real exchange rates
- **Run SQL-based analytics** for performance analysis
- **Serve data via REST API** with interactive documentation
- **Orchestrate ETL pipelines** using Apache Airflow (optional)

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.11 or higher
- **Git**: For cloning the repository
- **Terminal/Command Prompt**: Basic command line knowledge helpful

### API Keys (Free)
- **Alpha Vantage**: Free stock data API ([get key here](https://www.alphavantage.co/support/#api-key))
- **Exchange Rate API**: Free currency conversion ([get key here](https://exchangerate-api.com/))

## Installation Guide

### Step 1: Clone the Repository

```bash
# Clone the project
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter
```

### Step 2: Python Environment Setup

#### For Windows Users:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11+
```

#### For macOS/Linux Users:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+
```

### Step 3: Install Dependencies

```bash
# Install core application dependencies
pip install -e .

# Install development tools (optional but recommended)
pip install -e ".[dev]"

# Install all features including Airflow (optional)
pip install -e ".[all]"
```

### Step 4: Database Setup

You have two options for setting up PostgreSQL:

#### Option A: Local PostgreSQL Installation (Recommended)

**For Windows:**
1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the setup wizard
3. Remember your password for the `postgres` user
4. Ensure PostgreSQL service is running

```powershell
# Open Command Prompt as Administrator and create database
psql -U postgres
CREATE DATABASE ticker_converter;
CREATE USER ticker_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO ticker_user;
\q
```

**For macOS:**
```bash
# Install PostgreSQL using Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database and user
createdb ticker_converter
psql ticker_converter
CREATE USER ticker_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO ticker_user;
\q
```

**For Linux (Ubuntu/Debian):**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE ticker_converter;
CREATE USER ticker_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO ticker_user;
\q
```

#### Option B: Docker PostgreSQL (Alternative)

If you prefer using Docker:

```bash
# Run PostgreSQL in Docker container
docker run --name ticker-postgres \
  -e POSTGRES_DB=ticker_converter \
  -e POSTGRES_USER=ticker_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:14

# Wait for container to start
# Windows: timeout 10
# macOS/Linux: sleep 10
```

### Step 5: Environment Configuration

```bash
# Copy the environment template
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://ticker_user:your_password@localhost:5432/ticker_converter

# API Keys (get these free from the services)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CURRENCY_API_KEY=your_exchangerate_api_key

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# Optional: Airflow Configuration (if using Airflow)
AIRFLOW_HOME=/path/to/your/airflow
```

### Step 6: Database Schema Setup

Initialize the database with the required tables and views:

```bash
# Create all database objects using the included scripts
python -m ticker_converter.cli setup-database

# Or run SQL scripts manually
psql $DATABASE_URL -f airflow/sql/ddl/001_create_dimensions.sql
psql $DATABASE_URL -f airflow/sql/ddl/002_create_facts.sql
psql $DATABASE_URL -f airflow/sql/ddl/003_create_views.sql
psql $DATABASE_URL -f airflow/sql/ddl/004_create_indexes.sql
```

### Step 7: Verify Installation

```bash
# Test database connection
python -c "
from src.ticker_converter.database.connection import get_database_connection
print('Database connection successful!')
"

# Test API dependencies
python -c "
from src.ticker_converter.api_clients.alpha_vantage import AlphaVantageClient
print('API client dependencies loaded!')
"
```

## Quick Start Guide

### 1. Fetch Some Sample Data

```bash
# Fetch stock data for Apple
python -m ticker_converter.cli fetch-stock --symbol AAPL --days 7

# Fetch currency exchange rates
python -m ticker_converter.cli fetch-currency --days 7

# Check what data was loaded
python -m ticker_converter.cli data-status
```

### 2. Start the API Server

```bash
# Start the FastAPI development server
python tools/deployment/run_api.py

# Or use uvicorn directly
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Sample API Call**: http://localhost:8000/api/v1/stocks/AAPL/prices?limit=5

### 3. Explore the API

Try these sample API calls:

```bash
# Get Apple stock prices
curl "http://localhost:8000/api/v1/stocks/AAPL/prices?limit=5"

# Get prices converted to GBP
curl "http://localhost:8000/api/v1/stocks/AAPL/prices/gbp?limit=5"

# Get top performing stocks
curl "http://localhost:8000/api/v1/analytics/top-performers?period=daily"

# Get market summary
curl "http://localhost:8000/api/v1/analytics/market-summary"
```

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

## Optional: Apache Airflow Setup

If you want to set up the complete ETL orchestration:

### 1. Install Airflow
```bash
# Install Airflow with PostgreSQL provider
pip install apache-airflow[postgres]==2.8.1

# Set Airflow home directory
export AIRFLOW_HOME=$(pwd)/airflow_home
```

### 2. Initialize Airflow
```bash
# Initialize Airflow metadata database
airflow db init

# Create an admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@ticker-converter.local \
    --password admin123
```

### 3. Configure Airflow
```bash
# Copy DAGs to Airflow directory
cp -r airflow/dags/* $AIRFLOW_HOME/dags/

# Set up database connection in Airflow
airflow connections add postgres_default \
    --conn-type postgres \
    --conn-host localhost \
    --conn-schema ticker_converter \
    --conn-login ticker_user \
    --conn-password your_password \
    --conn-port 5432
```

### 4. Start Airflow Services
```bash
# Terminal 1: Start the web server
airflow webserver --port 8080

# Terminal 2: Start the scheduler
airflow scheduler
```

Access Airflow UI at http://localhost:8080 (admin/admin123)

## Development Workflow

### Daily Development Tasks

```bash
# Activate environment (run this each time you start working)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Start the API server
python tools/deployment/run_api.py

# Run tests
python -m pytest tests/

# Check code quality
python -m pylint src/
python -m black src/
```

### Common Operations

```bash
# Fetch data for all Magnificent Seven stocks
python -m ticker_converter.cli fetch-all --days 30

# Run data quality checks
python tools/data/examine_data.py

# Clean up old data
python tools/data/cleanup_data.py --days 90

# Create sample data for testing
python tools/data/create_dummy_data.py --symbols AAPL,MSFT --days 10
```

### Database Management

```bash
# Check database status
python -c "
from src.ticker_converter.database.connection import get_database_connection
from src.ticker_converter.data_ingestion.database_manager import DatabaseManager
dm = DatabaseManager()
print('Database status:', dm.get_database_status())
"

# View recent data
psql $DATABASE_URL -c "
SELECT s.symbol, d.date, p.close_usd 
FROM fact_stock_prices p 
JOIN dim_stocks s ON p.stock_id = s.stock_id 
JOIN dim_dates d ON p.date_id = d.date_id 
ORDER BY d.date DESC, s.symbol 
LIMIT 10;
"

# Check data freshness
psql $DATABASE_URL -c "
SELECT 
    s.symbol,
    MAX(d.date) as latest_date,
    COUNT(*) as total_records
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
GROUP BY s.symbol
ORDER BY s.symbol;
"
```

## Testing Your Setup

### 1. Run the Test Suite
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### 2. Manual Testing
```bash
# Test API endpoints
python tools/dev/test_connections.py

# Test data pipeline
python tools/dev/demo_capabilities.py

# Test Airflow DAGs (if installed)
airflow dags test daily_etl_dag 2025-08-12
```

### 3. Validate Data Quality
```bash
# Check data integrity
python -c "
from src.ticker_converter.data_ingestion.database_manager import DatabaseManager
dm = DatabaseManager()
results = dm.run_data_quality_checks()
for check, result in results.items():
    print(f'{check}: {\"PASS\" if result else \"FAIL\"}')'
"
```

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
# Windows: 
services.msc  # Look for PostgreSQL service

# macOS:
brew services list | grep postgres

# Linux:
sudo systemctl status postgresql

# Test connection manually
psql postgresql://ticker_user:your_password@localhost:5432/ticker_converter -c "SELECT 1;"
```

#### API Issues
```bash
# Check API server logs
python tools/deployment/run_api.py --debug

# Test specific endpoints
curl -v http://localhost:8000/health

# Check for port conflicts
# Windows:
netstat -an | findstr :8000

# macOS/Linux:
lsof -i :8000
```

#### Environment Issues
```bash
# Verify environment variables
python -c "
import os
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
print('ALPHA_VANTAGE_API_KEY:', os.getenv('ALPHA_VANTAGE_API_KEY')[:10] + '...' if os.getenv('ALPHA_VANTAGE_API_KEY') else 'Not set')
"

# Check Python environment
python -c "
import sys
print('Python version:', sys.version)
print('Virtual env:', sys.prefix)
"
```

#### Data Issues
```bash
# Check if tables exist
psql $DATABASE_URL -c "\dt"

# Check if data exists
psql $DATABASE_URL -c "
SELECT 
    'dim_stocks' as table_name, COUNT(*) as rows FROM dim_stocks
UNION ALL
SELECT 
    'fact_stock_prices' as table_name, COUNT(*) as rows FROM fact_stock_prices
UNION ALL
SELECT 
    'fact_currency_rates' as table_name, COUNT(*) as rows FROM fact_currency_rates;
"

# Reset database if needed
python -c "
from src.ticker_converter.data_ingestion.database_manager import DatabaseManager
dm = DatabaseManager()
dm.reset_database()  # WARNING: This deletes all data
"
```

## Performance Tips

### Database Optimization
```sql
-- Update table statistics regularly
ANALYZE fact_stock_prices;
ANALYZE fact_currency_rates;

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM v_stock_performance WHERE symbol = 'AAPL';

-- Monitor database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### API Performance
```bash
# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/stocks/AAPL/prices"

# Create curl-format.txt:
echo "time_namelookup:  %{time_namelookup}
time_connect:     %{time_connect}
time_appconnect:  %{time_appconnect}
time_pretransfer: %{time_pretransfer}
time_redirect:    %{time_redirect}
time_starttransfer: %{time_starttransfer}
time_total:       %{time_total}" > curl-format.txt
```

## Next Steps

Once your local environment is running:

1. **Explore the API**: Visit http://localhost:8000/docs for interactive documentation
2. **Set up Airflow**: Follow the optional Airflow setup for complete ETL orchestration
3. **Customize the pipeline**: Modify DAGs in `airflow/dags/` for your specific needs
4. **Add more stocks**: Extend the symbol list in the configuration
5. **Build dashboards**: Use the API endpoints to create custom visualizations

## Getting Help

### Resources
- **Project Documentation**: Check `docs/` directory for detailed guides
- **API Documentation**: http://localhost:8000/docs when running locally
- **Database Schema**: See `airflow/sql/ddl/` for table definitions
- **Example Queries**: Check `airflow/sql/queries/` for analytics examples

### Common Commands Reference
```bash
# Environment Management
source .venv/bin/activate                    # Activate environment
pip install -e ".[dev]"                     # Install with dev dependencies

# Data Management  
python -m ticker_converter.cli fetch-all    # Fetch all stock data
python tools/data/examine_data.py           # Examine stored data
python tools/data/cleanup_data.py           # Clean old data

# Server Management
python tools/deployment/run_api.py          # Start API server
airflow webserver --port 8080               # Start Airflow web UI
airflow scheduler                            # Start Airflow scheduler

# Testing
python -m pytest tests/                     # Run test suite
python tools/dev/test_connections.py        # Test connections
python tools/dev/demo_capabilities.py       # Demo functionality
```

Your local ticker-converter environment is now ready for development!
