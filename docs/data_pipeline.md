# Simplified SQL-Centric ETL Pipeline

This document describes the simplified SQL-centric ETL pipeline for the ticker-converter project, focusing on NYSE stocks and USD/GBP conversion with Apache Airflow orchestration.

## Overview

The pipeline is designed as a **SQL-first** ETL process that demonstrates core data engineering principles without unnecessary complexity:

**Scope**: NYSE stock exchance spreads for a selection of specific companies from the previous day, daily OHLCV data, USD/GBP currency conversion
**Architecture**: Star schema dimensional model with direct SQL operations
**Orchestration**: Apache Airflow with SQL operators (not Python operators)

## Simplified Architecture

```
Alpha Vantage API → Raw Data Ingestion → SQL Transformations → Star Schema → API Queries
                        ↓                       ↓               ↓           ↓
                   Raw Tables           Dimensional Model   Fact Tables   REST API
```

## Airflow DAG Structure

### DAG: `daily_market_data_pipeline`

**Schedule**: Daily at 6:00 PM EST (after market close)
**Catchup**: False
**Max Active Runs**: 1

#### Task Dependencies

```
start_pipeline
    ↓
extract_stock_data (Alpha Vantage API calls)
    ↓
extract_currency_rates (USD/GBP conversion)
    ↓
load_raw_data (Insert into staging tables)
    ↓
transform_dimensions (Populate dim_stocks, dim_dates)
    ↓
transform_facts (Calculate and load fact_stock_prices, fact_currency_rates)
    ↓
data_quality_checks (SQL validation queries)
    ↓
refresh_views (Update analytical views)
    ↓
end_pipeline
```

#### Task Details

##### 1. Extract Tasks (Python Operators)
```python
# extract_stock_data
symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
for symbol in symbols:
    data = alpha_vantage_client.get_daily_data(symbol)
    insert_raw_stock_data(data)

# extract_currency_rates  
rates = currency_api.get_usd_gbp_rate()
insert_raw_currency_data(rates)
```

##### 2. Transform Tasks (SQL Operators)
```sql
-- load_dimensions.sql
INSERT INTO dim_stocks (symbol, company_name, sector)
SELECT DISTINCT symbol, company_name, sector 
FROM raw_stock_data 
WHERE symbol NOT IN (SELECT symbol FROM dim_stocks);

-- daily_transform.sql
INSERT INTO fact_stock_prices (stock_id, date_id, opening_price, closing_price, high_price, low_price, volume)
SELECT 
    ds.stock_id,
    dd.date_id,
    rsd.open_price,
    rsd.close_price,
    rsd.high_price,
    rsd.low_price,
    rsd.volume
FROM raw_stock_data rsd
JOIN dim_stocks ds ON rsd.symbol = ds.symbol
JOIN dim_dates dd ON DATE(rsd.timestamp) = dd.date
WHERE DATE(rsd.timestamp) = CURRENT_DATE;
```

##### 3. Quality Check Tasks (SQL Sensors)
```sql
-- data_quality_checks.sql
SELECT 
    COUNT(*) as records_loaded,
    MIN(date_id) as min_date,
    MAX(date_id) as max_date,
    COUNT(DISTINCT stock_id) as unique_stocks
FROM fact_stock_prices 
WHERE date_id = (SELECT date_id FROM dim_dates WHERE date = CURRENT_DATE);

-- Expect: records_loaded >= 5, unique_stocks = 5
```

## Simplified Data Models

### Core Python Models (Pydantic)

#### MarketDataPoint
Basic market data representation:
```python
class MarketDataPoint(BaseModel):
    timestamp: datetime
    symbol: str = Field(min_length=1, max_length=10)
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0) 
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: int = Field(ge=0)
```

#### RawMarketData
Collection container:
```python
class RawMarketData(BaseModel):
    symbol: str
    data_points: List[MarketDataPoint]
    source: str = "alpha_vantage"
    retrieved_at: datetime
```

#### CurrencyRate
Currency conversion data:
```python
class CurrencyRate(BaseModel):
    from_currency: str = "USD"
    to_currency: str = "GBP" 
    rate: Decimal = Field(gt=0)
    timestamp: datetime
```

## SQL Schema (Star Schema)

### Dimension Tables

#### dim_stocks
```sql
CREATE TABLE dim_stocks (
    stock_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### dim_dates
```sql
CREATE TABLE dim_dates (
    date_id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN
);
```

### Fact Tables

#### fact_stock_prices
```sql
CREATE TABLE fact_stock_prices (
    price_id INTEGER PRIMARY KEY,
    stock_id INTEGER REFERENCES dim_stocks(stock_id),
    date_id INTEGER REFERENCES dim_dates(date_id),
    opening_price DECIMAL(10,2),
    closing_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    volume BIGINT,
    daily_return DECIMAL(8,4),
    price_change DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### fact_currency_rates
```sql
CREATE TABLE fact_currency_rates (
    rate_id INTEGER PRIMARY KEY,
    date_id INTEGER REFERENCES dim_dates(date_id),
    from_currency VARCHAR(3) DEFAULT 'USD',
    to_currency VARCHAR(3) DEFAULT 'GBP',
    exchange_rate DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Integration

### FastAPI Endpoints (SQL-Powered)

```python
@app.get("/api/stocks/top-performers")
async def get_top_performers(limit: int = 5):
    """Execute SQL query for top daily performers."""
    query = load_sql_query("top_performers.sql")
    return execute_query(query, {"limit": limit})

@app.get("/api/stocks/{symbol}/gbp")  
async def get_stock_price_gbp(symbol: str):
    """Get stock price converted to GBP."""
    query = load_sql_query("currency_conversion.sql")
    return execute_query(query, {"symbol": symbol})

@app.get("/api/stocks/price-range")
async def filter_by_price_range(min_price: float, max_price: float):
    """Filter stocks by price range using SQL."""
    query = load_sql_query("price_ranges.sql")
    return execute_query(query, {"min_price": min_price, "max_price": max_price})
```

### SQL Query Templates

#### top_performers.sql
```sql
SELECT 
    ds.symbol,
    ds.company_name,
    fs.closing_price,
    fs.daily_return,
    fs.price_change
FROM fact_stock_prices fs
JOIN dim_stocks ds ON fs.stock_id = ds.stock_id
JOIN dim_dates dd ON fs.date_id = dd.date_id
WHERE dd.date = CURRENT_DATE
ORDER BY fs.daily_return DESC
LIMIT %(limit)s;
```

#### currency_conversion.sql
```sql
SELECT 
    ds.symbol,
    fs.closing_price as usd_price,
    fcr.exchange_rate,
    (fs.closing_price * fcr.exchange_rate) as gbp_price,
    dd.date
FROM fact_stock_prices fs
JOIN dim_stocks ds ON fs.stock_id = ds.stock_id  
JOIN dim_dates dd ON fs.date_id = dd.date_id
JOIN fact_currency_rates fcr ON dd.date_id = fcr.date_id
WHERE ds.symbol = %(symbol)s
  AND dd.date = CURRENT_DATE;
```

## Airflow DAG Implementation

### DAG Configuration
```python
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'daily_market_data_pipeline',
    default_args=default_args,
    description='Simplified SQL-centric market data ETL',
    schedule_interval='0 18 * * 1-5',  # 6 PM weekdays
    catchup=False,
    max_active_runs=1
)
```

### Key Tasks
```python
# SQL-based transformations
load_dimensions = SQLExecuteQueryOperator(
    task_id='load_dimensions',
    sql='sql/etl/load_dimensions.sql',
    dag=dag
)

daily_transform = SQLExecuteQueryOperator(
    task_id='daily_transform', 
    sql='sql/etl/daily_transform.sql',
    dag=dag
)

quality_checks = SQLCheckOperator(
    task_id='data_quality_checks',
    sql='sql/etl/data_quality_checks.sql',
    dag=dag
)
```

## Success Criteria

### Technical Requirements Met
- **SQL-First**: All transformations in SQL, not Python
- **Star Schema**: Proper dimensional modeling implemented  
- **Direct Queries**: API endpoints execute SQL directly
- **Airflow Integration**: SQL operators, not Python operators
- **Simplified Scope**: NYSE stocks only, USD/GBP only

### Performance Targets
- **Pipeline Runtime**: < 10 minutes end-to-end
- **API Response Time**: < 200ms per query
- **Data Freshness**: Updated daily by 7:00 PM EST
- **Data Quality**: 100% successful loads, no data loss

### Maintainability Goals
- **Clear Separation**: Extract (Python) vs Transform (SQL) vs Load (SQL)
- **Testable Components**: Each SQL file independently testable
- **Documentation**: Complete SQL schema and query documentation
- **Monitoring**: Quality checks on every pipeline run

This simplified approach demonstrates core ETL skills while maintaining professional standards and clear separation of concerns.
