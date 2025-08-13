# SQL-Centric Pipeline Architecture

## Overview

The ticker-converter implements a simplified SQL-first ETL pipeline for NYSE stock market data analysis. The architecture prioritizes direct SQL operations over complex Python transformations, focusing on a star schema dimensional model in PostgreSQL.

## Architecture Principles

### 1. SQL-First Approach
- **All transformations** performed in SQL, not Python
- **Direct SQL queries** in API endpoints
- **SQL operators** in Airflow DAGs
- **Minimal Python logic** for data ingestion only

### 2. Simplified Scope
- **Magnificent Seven stocks** (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA)
- **Daily OHLCV data only** (no intraday complexity)
- **USD → GBP conversion only** (single currency pair)
- **PostgreSQL as single database** (no dual database complexity)

### 3. Star Schema Design
- **Dimension tables** for reference data (stocks, dates, currencies)
- **Fact tables** for transactional data (prices, rates)
- **Views** for analytical queries with pre-calculated metrics

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Alpha Vantage  │    │   Currency API   │    │      Airflow        │
│      API        │    │   (Exchange      │    │   Orchestration     │
│                 │    │    Rates)        │    │                     │
└─────────┬───────┘    └─────────┬────────┘    └──────────┬──────────┘
          │                      │                        │
          │ Daily Stock Data     │ USD/GBP Rates          │ SQL Operators
          │                      │                        │
          ▼                      ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL Database                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Dimensions    │  │     Facts       │  │         Views           │  │
│  │                 │  │                 │  │                         │  │
│  │ • dim_stocks    │  │ • fact_stock_   │  │ • v_stock_performance   │  │
│  │ • dim_dates     │  │   prices        │  │ • v_stocks_gbp          │  │
│  │ • dim_currencies│  │ • fact_currency_│  │ • v_top_performers      │  │
│  │                 │  │   rates         │  │                         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Direct SQL Queries
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                               │
│                                                                         │
│  GET /api/stocks/top-performers    →  v_top_performers                  │
│  GET /api/stocks/price-range       →  fact_stock_prices WHERE ...       │
│  GET /api/stocks/gbp-prices        →  v_stocks_gbp                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Database Schema Design

### Dimensional Model

The star schema consists of three dimension tables and two fact tables:

#### Dimension Tables

**Purpose**: Master reference for all stock symbols in the system.
**Scope**: The Magnificent Seven stocks (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA).
```sql
CREATE TABLE dim_stocks (
    stock_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    exchange VARCHAR(50) DEFAULT 'NYSE'
);
```

**dim_dates** - Date dimension for time-based analysis
```sql
CREATE TABLE dim_dates (
    date_id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    is_trading_day BOOLEAN DEFAULT TRUE
);
```

**dim_currencies** - Currency reference data
```sql
CREATE TABLE dim_currencies (
    currency_id SERIAL PRIMARY KEY,
    code VARCHAR(3) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    country VARCHAR(100)
);
```

#### Fact Tables

**fact_stock_prices** - Daily OHLCV stock price data
```sql
CREATE TABLE fact_stock_prices (
    price_id SERIAL PRIMARY KEY,
    date_id INTEGER REFERENCES dim_dates(date_id),
    stock_id INTEGER REFERENCES dim_stocks(stock_id),
    open_usd DECIMAL(10,4) NOT NULL,
    high_usd DECIMAL(10,4) NOT NULL,
    low_usd DECIMAL(10,4) NOT NULL,
    close_usd DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL
);
```

**fact_currency_rates** - Daily USD/GBP exchange rates
```sql
CREATE TABLE fact_currency_rates (
    rate_id SERIAL PRIMARY KEY,
    date_id INTEGER REFERENCES dim_dates(date_id),
    from_currency_id INTEGER REFERENCES dim_currencies(currency_id),
    to_currency_id INTEGER REFERENCES dim_currencies(currency_id),
    exchange_rate DECIMAL(10,6) NOT NULL
);
```

#### Analytical Views

**v_stock_performance** - Daily returns with SQL window functions
```sql
CREATE VIEW v_stock_performance AS
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date) as prev_close,
    ROUND(
        ((p.close_usd - LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) 
         / LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) * 100, 
        2
    ) as daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id;
```

**v_stocks_gbp** - Stock prices converted to GBP
```sql
CREATE VIEW v_stocks_gbp AS
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    r.exchange_rate,
    ROUND(p.close_usd / r.exchange_rate, 4) as close_gbp
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN fact_currency_rates r ON d.date_id = r.date_id
WHERE r.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
  AND r.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP');
```

**v_top_performers** - Top 5 performers by daily return
```sql
CREATE VIEW v_top_performers AS
SELECT symbol, daily_return_pct, close_usd, date
FROM v_stock_performance
WHERE daily_return_pct IS NOT NULL
ORDER BY daily_return_pct DESC
LIMIT 5;
```

## ETL Pipeline Flow

### 1. Data Ingestion (Python)
- **NYSE Stock Fetcher**: Retrieves daily OHLCV data from Alpha Vantage API
- **Currency Rate Fetcher**: Retrieves USD/GBP exchange rates
- **Minimal Python**: Only for API calls and basic data formatting

### 2. Data Transformation (SQL)
- **All transformations in PostgreSQL**
- **Dimensional loading** via SQL scripts
- **Data quality checks** using SQL constraints and validation queries
- **Analytical calculations** performed in views

### 3. Data Orchestration (Airflow)
- **SQLExecuteQueryOperator** for all database operations
- **External .sql files** for transformation logic
- **@task decorators** for custom Python logic (Airflow 3.0)

### 4. Data Serving (FastAPI)
- **Direct SQL query execution**
- **No ORM complexity**
- **View-based endpoints** for performance

## Benefits of This Architecture

### Simplicity
- **Reduced Python complexity**: Focus on SQL expertise
- **Single database technology**: PostgreSQL only
- **Minimal data models**: Only essential classes

### Performance
- **Database-native operations**: Leverage PostgreSQL optimizations
- **Pre-calculated views**: Faster API response times
- **Proper indexing**: Optimized for analytical queries

### Maintainability
- **SQL-first approach**: Easier to debug and modify transformations
- **Clear separation**: Data ingestion vs. transformation vs. serving
- **Standard patterns**: Well-understood star schema design

### Scalability
- **PostgreSQL proven**: Handles analytical workloads efficiently
- **View-based architecture**: Easy to add new analytical queries
- **Dimensional model**: Supports future expansion

## File Organization

```
sql/
├── ddl/                    # Data Definition Language
│   ├── 001_create_dimensions.sql
│   ├── 002_create_facts.sql
│   ├── 003_create_views.sql
│   └── 004_create_indexes.sql
├── etl/                    # ETL SQL Scripts
│   ├── daily_transform.sql
│   ├── data_quality_checks.sql
│   └── load_dimensions.sql
└── queries/                # API Query Templates
    ├── top_performers.sql
    ├── price_ranges.sql
    └── currency_conversion.sql

src/
├── data_ingestion/         # Python API Fetchers
│   ├── nyse_fetcher.py
│   └── currency_fetcher.py
└── data_models/            # Simplified Pydantic Models
    └── market_data.py

api/
├── main.py                 # FastAPI Application
├── models.py               # API Response Models
└── queries.sql             # SQL Query Definitions

dags/
└── nyse_stock_etl.py       # Airflow DAG with SQL Operators
```
**See (Final Project Structure)[docs/FINAL_PROJECT_STRUCTURE.md] for full folder structure**

## Success Metrics

- [ ] **50%+ file count reduction** from complex ETL modules
- [ ] **All transformations in SQL**, not Python
- [ ] **API endpoints execute SQL directly** via views
- [ ] **Airflow uses SQL operators only**
- [ ] **PostgreSQL as single database solution**
- [x] **Focus on Magnificent Seven stocks** (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA)
- [ ]**Daily data only** (no intraday complexity)
