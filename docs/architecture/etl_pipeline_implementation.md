# ETL Pipeline Implementation Guide

## Executive Summary

This document provides detailed implementation guidance for the ticker-converter's SQL-centric ETL pipeline. While the [Architecture Overview](./overview.md) covers strategic decisions and high-level architecture, this guide focuses on the practical implementation details, data flow mechanics, and operational procedures for running the ETL pipeline.

**Implementation Focus**: Step-by-step pipeline execution, data transformation logic, SQL-based processing, and operational monitoring for the production ETL system.

**Pipeline Value Proposition**: By centralizing data transformations in PostgreSQL and orchestrating workflows with Apache Airflow 3.0.4, the system delivers high-performance financial analytics with minimal Python complexity and maximum maintainability.

## Data Pipeline Overview

### Business Problem Addressed
Financial applications require **reliable, real-time access to processed market data** with complex analytics (daily returns, currency conversions, performance rankings) that traditional approaches struggle to deliver efficiently due to:
- Performance bottlenecks in application-layer data processing
- Maintenance overhead from mixed Python/SQL transformation logic
- Scalability limitations of Python-heavy ETL frameworks
- Operational complexity from managing multiple processing systems

### Solution Architecture
Our data pipeline addresses these challenges through a **three-layer approach**:

1. **Ingestion Layer (Python)**: Lightweight API clients fetch data from external sources
2. **Transformation Layer (SQL)**: All business logic implemented in PostgreSQL for optimal performance  
3. **Serving Layer (FastAPI)**: Direct SQL execution provides sub-second analytical responses

## End-to-End Data Flow

```
┌─────────────────┐    ┌─────────────────┐
│  Alpha Vantage  │    │   Currency      │
│      API        │    │  Exchange API   │
│   (Stock Data)  │    │  (USD/GBP)     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │ Daily OHLCV         │ Exchange Rates
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────┐
│           Python Ingestion Layer            │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │  NYSE Fetcher   │  │ Currency Fetcher │   │
│  │   (nyse_        │  │  (currency_     │   │
│  │   fetcher.py)   │  │   fetcher.py)   │   │
│  └─────────────────┘  └─────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │ Raw JSON Data
                  ▼
┌─────────────────────────────────────────────┐
│            PostgreSQL Database              │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Raw Tables    │  │  Staging Area   │   │
│  │ • raw_stock_    │  │ • Clean & Load  │   │
│  │   data          │  │ • Validate      │   │
│  │ • raw_currency_ │  │ • Transform     │   │
│  │   data          │  │                 │   │
│  └─────────────────┘  └─────────────────┘   │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │   Dimensions    │  │     Facts       │   │
│  │ • dim_stocks    │  │ • fact_stock_   │   │
│  │ • dim_dates     │  │   prices        │   │
│  │ • dim_currency  │  │ • fact_currency_│   │
│  │                 │  │   rates         │   │
│  └─────────────────┘  └─────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────────┐ │
│  │              Views Layer                │ │
│  │ • v_stock_performance (daily returns)  │ │
│  │ • v_stocks_gbp (currency conversion)   │ │  
│  │ • v_top_performers (ranking analysis)  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │ Direct SQL Queries
                  ▼
┌─────────────────────────────────────────────┐
│               FastAPI Layer                 │
│  GET /api/stocks/top-performers             │
│  GET /api/stocks/performance-details        │
│  GET /api/stocks/{symbol}/gbp               │
│  GET /api/stocks/price-range                │
└─────────────────────────────────────────────┘
```

## Data Ingestion Architecture

### Alpha Vantage Integration
**Purpose**: Primary source for NYSE stock market data  
**Implementation**: `src/ticker_converter/data_ingestion/nyse_fetcher.py`

```python
class NYSEFetcher:
    """Fetches daily OHLCV data for Magnificent Seven stocks."""

    def fetch_daily_data(self, symbol: str, days: int = 30) -> List[MarketDataPoint]:
        """
        Fetch historical daily data with intelligent error handling.
        
        Features:
        - Rate limiting compliance (5 calls/minute for free tier)
        - Exponential backoff for transient errors
        - Data validation using Pydantic models
        - Caching to minimize API usage during development
        """
```

**Data Quality Measures**:
- **Validation**: Pydantic models ensure data type correctness and business rule compliance
- **Completeness**: Missing data detection and reporting
- **Freshness**: Timestamp validation to ensure recent data
- **Consistency**: Symbol verification against expected Magnificent Seven list

### Currency Exchange Integration  
**Purpose**: USD/GBP conversion rates for international analytics
**Implementation**: `src/ticker_converter/data_ingestion/currency_fetcher.py`

```python
class CurrencyFetcher:
    """Fetches USD/GBP exchange rates from financial APIs."""

    def fetch_exchange_rates(self, days: int = 30) -> List[CurrencyRate]:
        """
        Retrieve historical exchange rates with failover support.
        
        Features:
        - Multiple API provider support (primary/secondary)
        - Automatic failover for service reliability
        - Rate validation and anomaly detection
        - Historical rate backfill capabilities
        """
```

## SQL Transformation Architecture

### Philosophy: Database-Native Processing
**Decision Rationale**: All business logic implemented in SQL to leverage PostgreSQL's optimization capabilities and reduce Python complexity.

### Transformation Stages

#### Stage 1: Raw Data Ingestion
```sql
-- Raw staging tables for incoming API data
CREATE TABLE raw_stock_data (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10,4) NOT NULL,
    high_price DECIMAL(10,4) NOT NULL, 
    low_price DECIMAL(10,4) NOT NULL,
    close_price DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    source VARCHAR(50) DEFAULT 'alpha_vantage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Stage 2: Dimensional Loading
**File**: `sql/etl/load_dimensions.sql`
```sql
-- Populate dimension tables from raw data
INSERT INTO dim_stocks (symbol, company_name, sector, exchange)
SELECT DISTINCT 
    symbol,
    CASE symbol 
        WHEN 'AAPL' THEN 'Apple Inc.'
        WHEN 'MSFT' THEN 'Microsoft Corporation'
        WHEN 'GOOGL' THEN 'Alphabet Inc.'
        -- ... mapping for all Magnificent Seven
    END as company_name,
    'Technology' as sector,  -- Simplified sector classification
    'NASDAQ' as exchange
FROM raw_stock_data
WHERE symbol NOT IN (SELECT symbol FROM dim_stocks);

-- Auto-populate date dimension for analytical queries
INSERT INTO dim_dates (date, year, month, quarter, is_trading_day)
SELECT DISTINCT
    DATE(timestamp) as date,
    EXTRACT(YEAR FROM timestamp) as year,
    EXTRACT(MONTH FROM timestamp) as month,
    EXTRACT(QUARTER FROM timestamp) as quarter,
    CASE EXTRACT(DOW FROM timestamp)
        WHEN 0 THEN FALSE  -- Sunday
        WHEN 6 THEN FALSE  -- Saturday  
        ELSE TRUE
    END as is_trading_day
FROM raw_stock_data
WHERE DATE(timestamp) NOT IN (SELECT date FROM dim_dates);
```

#### Stage 3: Fact Table Population  
**File**: `sql/etl/daily_transform.sql`
```sql
-- Load fact tables with business logic calculations
INSERT INTO fact_stock_prices (
    stock_id, date_id, open_usd, high_usd, low_usd, close_usd, volume,
    daily_return_pct, price_change_usd
)
SELECT 
    ds.stock_id,
    dd.date_id,
    rsd.open_price,
    rsd.high_price,
    rsd.low_price,
    rsd.close_price,
    rsd.volume,
    -- Calculate daily return using window functions
    ROUND(
        ((rsd.close_price - LAG(rsd.close_price) OVER (
            PARTITION BY rsd.symbol ORDER BY rsd.timestamp
        )) / LAG(rsd.close_price) OVER (
            PARTITION BY rsd.symbol ORDER BY rsd.timestamp
        )) * 100, 4
    ) as daily_return_pct,
    rsd.close_price - LAG(rsd.close_price) OVER (
        PARTITION BY rsd.symbol ORDER BY rsd.timestamp  
    ) as price_change_usd
FROM raw_stock_data rsd
JOIN dim_stocks ds ON rsd.symbol = ds.symbol
JOIN dim_dates dd ON DATE(rsd.timestamp) = dd.date
WHERE DATE(rsd.timestamp) >= CURRENT_DATE - INTERVAL '1 day';
```

#### Stage 4: Analytical View Creation
**File**: `sql/ddl/003_create_views.sql`
```sql
-- High-performance analytical views for API endpoints
CREATE OR REPLACE VIEW v_stock_performance AS
SELECT 
    s.symbol,
    s.company_name,
    d.date,
    p.close_usd,
    p.daily_return_pct,
    p.price_change_usd,
    p.volume,
    -- Ranking analytics
    RANK() OVER (PARTITION BY d.date ORDER BY p.daily_return_pct DESC) as daily_rank,
    -- Moving averages using window functions
    AVG(p.close_usd) OVER (
        PARTITION BY s.symbol 
        ORDER BY d.date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma_7_day,
    AVG(p.close_usd) OVER (
        PARTITION BY s.symbol 
        ORDER BY d.date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW  
    ) as ma_30_day
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.is_trading_day = TRUE;

-- Currency conversion view for international users
CREATE OR REPLACE VIEW v_stocks_gbp AS
SELECT 
    sp.symbol,
    sp.company_name,
    sp.date,
    sp.close_usd,
    cr.exchange_rate,
    ROUND(sp.close_usd / cr.exchange_rate, 4) as close_gbp,
    ROUND(sp.price_change_usd / cr.exchange_rate, 4) as price_change_gbp
FROM v_stock_performance sp
JOIN fact_currency_rates cr ON sp.date = (
    SELECT date FROM dim_dates WHERE date_id = cr.date_id
)
WHERE cr.from_currency = 'USD' AND cr.to_currency = 'GBP';
```

## Airflow Orchestration Architecture

### DAG Design: `daily_etl_dag.py`
**Philosophy**: SQL-operator centric workflow with minimal Python for orchestration only

```python
from airflow.decorators import dag, task
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

@dag(
    dag_id='daily_market_data_pipeline',
    description='SQL-centric ETL for NYSE stocks and currency data',
    schedule='0 18 * * 1-5',  # 6 PM EST, weekdays only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['finance', 'etl', 'sql-first']
)
def market_data_pipeline():
    """Modern Airflow 3.0.4 DAG with @dag decorator."""

    @task(task_id='extract_stock_data')
    def fetch_stock_data():
        """Python task: API data ingestion only."""
        from ticker_converter.data_ingestion.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        return orchestrator.run_stock_data_ingestion()

    @task(task_id='extract_currency_rates')  
    def fetch_currency_data():
        """Python task: Currency API ingestion only."""
        from ticker_converter.data_ingestion.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        return orchestrator.run_currency_data_ingestion()
        
    # SQL-only transformation tasks
    load_dimensions = PostgresOperator(
        task_id='load_dimensions',
        postgres_conn_id='postgres_default',
        sql='sql/etl/load_dimensions.sql'
    )

    daily_transform = PostgresOperator(
        task_id='daily_transform', 
        postgres_conn_id='postgres_default',
        sql='sql/etl/daily_transform.sql'
    )

    data_quality_checks = PostgresOperator(
        task_id='data_quality_checks',
        postgres_conn_id='postgres_default', 
        sql='sql/etl/data_quality_checks.sql'
    )

    refresh_views = PostgresOperator(
        task_id='refresh_views',
        postgres_conn_id='postgres_default',
        sql='sql/etl/refresh_analytical_views.sql'
    )

    # Task dependencies - linear pipeline for simplicity
    [fetch_stock_data(), fetch_currency_data()] >> load_dimensions
    load_dimensions >> daily_transform >> data_quality_checks >> refresh_views

# Instantiate the DAG
dag_instance = market_data_pipeline()
```

### Data Quality Framework
**File**: `sql/etl/data_quality_checks.sql`
```sql
-- Comprehensive data quality validation
WITH quality_metrics AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT stock_id) as unique_stocks,
        MIN(date_id) as min_date,
        MAX(date_id) as max_date,
        COUNT(CASE WHEN daily_return_pct IS NULL THEN 1 END) as null_returns,
        COUNT(CASE WHEN volume = 0 THEN 1 END) as zero_volume_records
    FROM fact_stock_prices 
    WHERE date_id = (
        SELECT date_id FROM dim_dates WHERE date = CURRENT_DATE - INTERVAL '1 day'
    )
)
SELECT 
    CASE 
        WHEN unique_stocks < 7 THEN 'FAIL: Missing stock data'
        WHEN total_records < 7 THEN 'FAIL: Insufficient records'
        WHEN null_returns > 1 THEN 'WARN: High null return rate'
        WHEN zero_volume_records > 0 THEN 'WARN: Zero volume detected'
        ELSE 'PASS: Data quality acceptable'
    END as quality_status,
    total_records,
    unique_stocks,
    null_returns,
    zero_volume_records
FROM quality_metrics;
```

## FastAPI Serving Architecture

### Direct SQL Execution Pattern
**Philosophy**: Bypass ORM overhead by executing SQL directly for optimal performance

```python
# api/main.py
from fastapi import FastAPI, Depends
from api.database import get_database_connection
import asyncpg

app = FastAPI(title="Financial Market Data API", version="1.1.0")

@app.get("/api/stocks/top-performers")
async def get_top_performers(
    limit: int = 5,
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get top performing stocks by daily return."""

    query = """
        SELECT symbol, company_name, daily_return_pct, close_usd, date
        FROM v_stock_performance
        WHERE date = (SELECT MAX(date) FROM dim_dates WHERE is_trading_day = TRUE)
        ORDER BY daily_return_pct DESC
        LIMIT $1;
    """

    results = await db.fetch(query, limit)
    return [dict(record) for record in results]

@app.get("/api/stocks/performance-details")
async def get_performance_details(
    symbol: str,
    days: int = 30,
    db: asyncpg.Connection = Depends(get_database_connection)
):
    """Get detailed performance metrics for a specific stock."""

    query = """
        SELECT 
            symbol, company_name, date, close_usd, daily_return_pct,
            ma_7_day, ma_30_day, daily_rank, volume
        FROM v_stock_performance
        WHERE symbol = $1 
          AND date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date DESC;
    """

    results = await db.fetch(query, symbol, days)
    return [dict(record) for record in results]
```

## Performance Optimization Strategies

### Database Performance
**Indexing Strategy**:
```sql
-- Optimized indexes for analytical queries
CREATE INDEX idx_fact_stock_prices_symbol_date 
ON fact_stock_prices(stock_id, date_id);

CREATE INDEX idx_fact_stock_prices_date_return 
ON fact_stock_prices(date_id, daily_return_pct DESC);

CREATE INDEX idx_dim_dates_trading_day 
ON dim_dates(date) WHERE is_trading_day = TRUE;
```

**Query Optimization**:
- **Window Functions**: Leverage PostgreSQL's optimized window function implementation
- **Materialized Views**: Pre-calculate expensive aggregations for frequently accessed data
- **Partial Indexes**: Index only trading days and active stocks for better performance
- **Connection Pooling**: Manage database connections efficiently across Airflow and FastAPI

### API Performance
**Async Architecture**:
- **asyncpg**: High-performance async PostgreSQL driver for FastAPI
- **Connection Pooling**: Shared connection pool across API requests
- **Result Streaming**: Efficient handling of large result sets
- **Response Caching**: Application-level caching for frequently accessed endpoints

### ETL Performance  
**Bulk Operations**:
- **COPY Commands**: Use PostgreSQL's COPY for fast bulk data loading
- **Upsert Pattern**: ON CONFLICT DO UPDATE for idempotent operations
- **Parallel Processing**: Independent Airflow tasks execute concurrently
- **Incremental Updates**: Process only new/changed data in daily runs

## Future Enhancement Roadmap

### Real-Time Processing (6-12 months)
**Streaming Architecture**:
- Apache Kafka integration for real-time market data feeds
- Change Data Capture (CDC) for immediate downstream updates
- WebSocket API endpoints for live client applications
- Real-time alerting for significant market movements

### Advanced Analytics (1-2 years)
**Machine Learning Integration**:
- Price prediction models using historical patterns
- Risk analytics (VaR, portfolio optimization)
- Anomaly detection for unusual market behavior
- Technical indicator calculations (RSI, MACD, Bollinger Bands)

### Platform Scalability (2+ years)
**Infrastructure Evolution**:
- Kubernetes deployment for dynamic scaling
- Multi-region deployment for global market coverage
- Data lake integration for regulatory compliance
- Microservices architecture for component independence

## Troubleshooting and Monitoring

### Data Pipeline Monitoring
**Airflow Integration**:
- Task execution time monitoring and alerting
- Data quality check failures trigger notifications
- Automatic retry logic for transient API failures
- Comprehensive logging for debugging and audit trails

**Database Monitoring**:
- Query performance monitoring with slow query alerts
- Connection pool utilization tracking
- Data freshness monitoring (last successful ETL timestamp)
- Storage growth monitoring and automated cleanup

### Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| API Rate Limiting | 429 HTTP errors | Implement exponential backoff, cache responses |
| Missing Trading Days | Gaps in data | Validate is_trading_day flag, handle holidays |
| Currency Rate Delays | Stale conversion rates | Implement fallback to previous day's rate |
| View Performance | Slow API responses | Add materialized views, optimize indexes |

## Related Documentation

- [Database Design](database_design.md) - Detailed schema design and optimization
- [Airflow Setup](airflow_setup.md) - Apache Airflow 3.0.4 configuration guide  
- [API Design](api_design.md) - FastAPI implementation and endpoint specifications
- [Local Setup](../deployment/local_setup.md) - Development environment configuration

---

**Last Updated**: August 2025 | **Version**: 1.1.0 | **Pipeline Review**: Quarterly
