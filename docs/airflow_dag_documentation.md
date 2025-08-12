# Airflow DAG Documentation: SQL-Centric ETL Pipeline

## Overview

This document describes the simplified Airflow DAG implementation for the ticker-converter project, using SQL operators exclusively for data transformations and leveraging PostgreSQL for all analytical operations.

## DAG Architecture

### Design Principles
- **SQL-First Approach**: All transformations performed using `PostgresOperator`
- **External SQL Files**: SQL logic stored in separate `.sql` files for version control
- **Minimal Python**: Python operators only for API data ingestion
- **Linear Pipeline**: Simple task dependencies without complex branching
- **Idempotent Operations**: All tasks can be safely re-run

### DAG Overview: `nyse_stock_etl`

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# DAG Configuration
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'nyse_stock_etl',
    default_args=default_args,
    description='NYSE Stock Data ETL Pipeline with SQL Transformations',
    schedule_interval='0 18 * * 1-5',  # 6 PM EST, weekdays only
    max_active_runs=1,
    catchup=False,
    tags=['finance', 'nyse', 'sql-etl']
)
```

## Task Definitions

### 1. Data Ingestion Tasks (Python)

#### Task: `fetch_stock_data`
```python
def fetch_nyse_stock_data(**context):
    """
    Fetch daily OHLCV data for NYSE stocks from Alpha Vantage API.
    Minimal Python logic - only API calls and basic data formatting.
    """
    from src.data_ingestion.nyse_fetcher import NYSEFetcher

    # Magnificent Seven stocks
    symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

    fetcher = NYSEFetcher()
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    for symbol in symbols:
        # Fetch data from API
        stock_data = fetcher.get_daily_data(symbol)

        # Insert raw data directly into staging table
        insert_sql = """
            INSERT INTO staging_stock_data (symbol, date, open_usd, high_usd, low_usd, close_usd, volume, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (symbol, date) DO UPDATE SET
                open_usd = EXCLUDED.open_usd,
                high_usd = EXCLUDED.high_usd,
                low_usd = EXCLUDED.low_usd,
                close_usd = EXCLUDED.close_usd,
                volume = EXCLUDED.volume,
                updated_at = NOW()
        """

        for data_point in stock_data:
            postgres_hook.run(insert_sql, parameters=(
                symbol,
                data_point.date,
                data_point.open,
                data_point.high,
                data_point.low,
                data_point.close,
                data_point.volume
            ))

fetch_stock_data = PythonOperator(
    task_id='fetch_stock_data',
    python_callable=fetch_nyse_stock_data,
    dag=dag
)
```

#### Task: `fetch_currency_rates`
```python
def fetch_usd_gbp_rates(**context):
    """
    Fetch USD/GBP exchange rates from currency API.
    """
    from src.data_ingestion.currency_fetcher import CurrencyFetcher

    fetcher = CurrencyFetcher()
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    # Fetch USD/GBP rate for yesterday (market data is T-1)
    execution_date = context['execution_date']
    target_date = execution_date - timedelta(days=1)

    rate_data = fetcher.get_exchange_rate('USD', 'GBP', target_date)

    # Insert into staging table
    insert_sql = """
        INSERT INTO staging_currency_rates (from_currency, to_currency, rate, date, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (from_currency, to_currency, date) DO UPDATE SET
            rate = EXCLUDED.rate,
            updated_at = NOW()
    """

    postgres_hook.run(insert_sql, parameters=(
        'USD', 'GBP', rate_data.rate, target_date
    ))

fetch_currency_rates = PythonOperator(
    task_id='fetch_currency_rates',
    python_callable=fetch_usd_gbp_rates,
    dag=dag
)
```

### 2. SQL Transformation Tasks

#### Task: `load_dimensions`
```python
load_dimensions = PostgresOperator(
    task_id='load_dimensions',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_dimensions.sql',
    dag=dag
)
```

**SQL File: `sql/etl/load_dimensions.sql`**
```sql
-- Load dimension tables from staging data
BEGIN;

-- Load dim_dates (ensure date exists)
INSERT INTO dim_dates (date, year, month, quarter, is_trading_day)
SELECT DISTINCT 
    date,
    EXTRACT(YEAR FROM date) as year,
    EXTRACT(MONTH FROM date) as month,
    EXTRACT(QUARTER FROM date) as quarter,
    CASE 
        WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN FALSE  -- Weekend
        ELSE TRUE 
    END as is_trading_day
FROM staging_stock_data
WHERE date NOT IN (SELECT date FROM dim_dates)
ON CONFLICT (date) DO NOTHING;

-- Load dim_stocks (ensure stocks exist)
INSERT INTO dim_stocks (symbol, company_name, sector, exchange)
SELECT DISTINCT 
    symbol,
    CASE 
        WHEN symbol = 'AAPL' THEN 'Apple Inc.'
        WHEN symbol = 'MSFT' THEN 'Microsoft Corporation'
        WHEN symbol = 'AMZN' THEN 'Amazon.com Inc.'
        WHEN symbol = 'GOOGL' THEN 'Alphabet Inc.'
        WHEN symbol = 'META' THEN 'Meta Platforms Inc.'
        WHEN symbol = 'NVDA' THEN 'NVIDIA Corporation'
        WHEN symbol = 'TSLA' THEN 'Tesla Inc.'
        ELSE symbol
    END as company_name,
    CASE 
        WHEN symbol IN ('AAPL', 'MSFT', 'GOOGL', 'META') THEN 'Technology'
        WHEN symbol = 'AMZN' THEN 'E-commerce'
        WHEN symbol = 'TSLA' THEN 'Automotive'
        WHEN symbol = 'NVDA' THEN 'Semiconductors'
        ELSE 'Unknown'
    END as sector,
    'NYSE' as exchange
FROM staging_stock_data
WHERE symbol NOT IN (SELECT symbol FROM dim_stocks)
ON CONFLICT (symbol) DO NOTHING;

-- Load dim_currencies
INSERT INTO dim_currencies (code, name, country)
VALUES 
    ('USD', 'US Dollar', 'United States'),
    ('GBP', 'British Pound', 'United Kingdom')
ON CONFLICT (code) DO NOTHING;

COMMIT;
```

#### Task: `transform_to_warehouse`
```python
transform_to_warehouse = PostgresOperator(
    task_id='transform_to_warehouse',
    postgres_conn_id='postgres_default',
    sql='sql/etl/daily_transform.sql',
    dag=dag
)
```

**SQL File: `sql/etl/daily_transform.sql`**
```sql
-- Transform staging data into star schema fact tables
BEGIN;

-- Transform stock prices to fact table
INSERT INTO fact_stock_prices (date_id, stock_id, open_usd, high_usd, low_usd, close_usd, volume)
SELECT 
    d.date_id,
    s.stock_id,
    st.open_usd,
    st.high_usd,
    st.low_usd,
    st.close_usd,
    st.volume
FROM staging_stock_data st
JOIN dim_dates d ON st.date = d.date
JOIN dim_stocks s ON st.symbol = s.symbol
WHERE st.date = '{{ ds }}'  -- Airflow template for execution date
ON CONFLICT (date_id, stock_id) DO UPDATE SET
    open_usd = EXCLUDED.open_usd,
    high_usd = EXCLUDED.high_usd,
    low_usd = EXCLUDED.low_usd,
    close_usd = EXCLUDED.close_usd,
    volume = EXCLUDED.volume;

-- Transform currency rates to fact table
INSERT INTO fact_currency_rates (date_id, from_currency_id, to_currency_id, exchange_rate)
SELECT 
    d.date_id,
    c1.currency_id as from_currency_id,
    c2.currency_id as to_currency_id,
    sc.rate
FROM staging_currency_rates sc
JOIN dim_dates d ON sc.date = d.date
JOIN dim_currencies c1 ON sc.from_currency = c1.code
JOIN dim_currencies c2 ON sc.to_currency = c2.code
WHERE sc.date = '{{ ds }}'
ON CONFLICT (date_id, from_currency_id, to_currency_id) DO UPDATE SET
    exchange_rate = EXCLUDED.exchange_rate;

COMMIT;
```

#### Task: `data_quality_check`
```python
data_quality_check = PostgresOperator(
    task_id='data_quality_check',
    postgres_conn_id='postgres_default',
    sql='sql/etl/data_quality_checks.sql',
    dag=dag
)
```

**SQL File: `sql/etl/data_quality_checks.sql`**
```sql
-- Data quality validation queries
-- These will fail the task if data quality issues are found

-- Check 1: Ensure all expected stocks have data for the execution date
DO $$ 
DECLARE
    expected_stocks INTEGER := 7;  -- AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA
    actual_stocks INTEGER;
BEGIN
    SELECT COUNT(DISTINCT s.symbol)
    INTO actual_stocks
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE d.date = '{{ ds }}';

    IF actual_stocks < expected_stocks THEN
        RAISE EXCEPTION 'Data quality check failed: Expected % stocks, found % for date %', 
            expected_stocks, actual_stocks, '{{ ds }}';
    END IF;

    RAISE NOTICE 'Data quality check passed: % stocks found for date %', actual_stocks, '{{ ds }}';
END $$;

-- Check 2: Validate OHLC data consistency
DO $$
DECLARE
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO invalid_count
    FROM fact_stock_prices p
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE d.date = '{{ ds }}'
      AND NOT (
          p.high_usd >= p.low_usd 
          AND p.high_usd >= p.open_usd 
          AND p.high_usd >= p.close_usd
          AND p.low_usd <= p.open_usd 
          AND p.low_usd <= p.close_usd
      );

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Data quality check failed: % invalid OHLC records found for date %', 
            invalid_count, '{{ ds }}';
    END IF;

    RAISE NOTICE 'OHLC consistency check passed for date %', '{{ ds }}';
END $$;

-- Check 3: Ensure currency rate exists
DO $$
DECLARE
    rate_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO rate_count
    FROM fact_currency_rates cr
    JOIN dim_dates d ON cr.date_id = d.date_id
    JOIN dim_currencies c1 ON cr.from_currency_id = c1.currency_id
    JOIN dim_currencies c2 ON cr.to_currency_id = c2.currency_id
    WHERE d.date = '{{ ds }}'
      AND c1.code = 'USD'
      AND c2.code = 'GBP';

    IF rate_count = 0 THEN
        RAISE EXCEPTION 'Data quality check failed: No USD/GBP rate found for date %', '{{ ds }}';
    END IF;

    RAISE NOTICE 'Currency rate check passed for date %', '{{ ds }}';
END $$;
```

#### Task: `cleanup_staging`
```python
cleanup_staging = PostgresOperator(
    task_id='cleanup_staging',
    postgres_conn_id='postgres_default',
    sql="""
        -- Clean up staging tables older than 7 days
        DELETE FROM staging_stock_data 
        WHERE created_at < NOW() - INTERVAL '7 days';

        DELETE FROM staging_currency_rates 
        WHERE created_at < NOW() - INTERVAL '7 days';

        -- Log cleanup action
        INSERT INTO etl_log (dag_id, task_id, message, log_time)
        VALUES ('nyse_stock_etl', 'cleanup_staging', 'Staging tables cleaned', NOW());
    """,
    dag=dag
)
```

## Task Dependencies

### Linear Pipeline Flow
```python
# Define task dependencies
fetch_stock_data >> load_dimensions
fetch_currency_rates >> load_dimensions
load_dimensions >> transform_to_warehouse
transform_to_warehouse >> data_quality_check
data_quality_check >> cleanup_staging
```

### Dependency Visualization
```
┌─────────────────┐    ┌──────────────────┐
│ fetch_stock_    │    │ fetch_currency_  │
│ data            │    │ rates            │
└─────────┬───────┘    └─────────┬────────┘
          │                      │
          ▼                      ▼
          ┌─────────────────────────┐
          │ load_dimensions         │
          └─────────┬───────────────┘
                    │
                    ▼
          ┌─────────────────────────┐
          │ transform_to_warehouse  │
          └─────────┬───────────────┘
                    │
                    ▼
          ┌─────────────────────────┐
          │ data_quality_check      │
          └─────────┬───────────────┘
                    │
                    ▼
          ┌─────────────────────────┐
          │ cleanup_staging         │
          └─────────────────────────┘
```

## Configuration Requirements

### PostgreSQL Connection
```python
# Airflow Connection Configuration
conn_id = 'postgres_default'
conn_type = 'postgres'
host = 'localhost'  # or production host
schema = 'ticker_converter'
login = 'ticker_user'
password = '{{ var.value.postgres_password }}'  # Stored in Airflow Variables
port = 5432
extra = {
    "sslmode": "prefer",
    "connect_timeout": "10"
}
```

### Airflow Variables
```bash
# Set via Airflow UI or CLI
airflow variables set postgres_password "your_secure_password"
airflow variables set alpha_vantage_api_key "your_api_key"
airflow variables set currency_api_key "your_currency_api_key"
```

### Environment Variables
```bash
# In .env file or environment
DATABASE_URL=postgresql://ticker_user:password@localhost:5432/ticker_converter
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CURRENCY_API_KEY=your_currency_api_key
```

## Monitoring and Alerting

### Built-in Monitoring
```python
# Task-level monitoring
default_args = {
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data-team@company.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# SLA monitoring
sla_miss_callback = lambda context: send_alert(context)

dag = DAG(
    'nyse_stock_etl',
    default_args=default_args,
    sla_miss_callback=sla_miss_callback,
    max_active_runs=1,
)
```

### Custom Alerts
```python
def check_data_freshness(**context):
    """Custom task to check if data is fresh enough"""
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

    # Check latest data date
    result = postgres_hook.get_first("""
        SELECT MAX(d.date) as latest_date
        FROM fact_stock_prices p
        JOIN dim_dates d ON p.date_id = d.date_id
    """)

    latest_date = result[0]
    days_old = (datetime.now().date() - latest_date).days

    if days_old > 3:  # Alert if data is more than 3 days old
        raise ValueError(f"Data is {days_old} days old - investigation required")

data_freshness_check = PythonOperator(
    task_id='data_freshness_check',
    python_callable=check_data_freshness,
    dag=dag
)
```

## Scaling Considerations

### Performance Optimization
```sql
-- Optimize staging table operations
CREATE INDEX IF NOT EXISTS idx_staging_stock_data_date_symbol 
ON staging_stock_data(date, symbol);

CREATE INDEX IF NOT EXISTS idx_staging_currency_rates_date 
ON staging_currency_rates(date, from_currency, to_currency);

-- Partition fact tables by date (for large volumes)
-- This would be implemented when daily volume exceeds ~1M records
```

### Error Handling
```python
def handle_api_failure(**context):
    """Fallback function for API failures"""
    from airflow.models import Variable

    # Log failure
    logging.error(f"API fetch failed for {context['task_instance'].task_id}")

    # Check if we have recent data to use
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
    recent_data_count = postgres_hook.get_first("""
        SELECT COUNT(*) FROM staging_stock_data 
        WHERE date >= CURRENT_DATE - INTERVAL '2 days'
    """)[0]

    if recent_data_count == 0:
        # No recent data - send alert and fail
        send_critical_alert("No stock data available - manual intervention required")
        raise ValueError("Critical: No recent stock data available")
    else:
        # We have recent data - log warning and continue
        logging.warning("Using existing data due to API failure")
        return "API_FAILED_USING_EXISTING_DATA"

# Add to fetch tasks
fetch_stock_data = PythonOperator(
    task_id='fetch_stock_data',
    python_callable=fetch_nyse_stock_data,
    on_failure_callback=handle_api_failure,
    dag=dag
)
```

## Best Practices Implementation

### 1. Idempotent Operations
- All SQL operations use `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING`
- Tasks can be safely re-run without data duplication
- Date-based partitioning allows for safe backfills

### 2. External SQL Files
- SQL logic stored in version-controlled `.sql` files
- Easy to review SQL changes in pull requests
- SQL can be tested independently of Airflow

### 3. Minimal Python Logic
- Python only for API calls and basic data formatting
- No complex transformations in Python code
- Leverage PostgreSQL's analytical capabilities

### 4. Comprehensive Testing
```python
# Unit tests for Python functions
def test_fetch_nyse_stock_data():
    # Test API integration
    pass

def test_data_quality_checks():
    # Test SQL validation logic
    pass

# Integration tests for full DAG
def test_dag_integrity():
    # Test DAG structure and dependencies
    pass
```

## Deployment Guide

### 1. SQL Schema Setup
```bash
# Deploy SQL schema files
psql $DATABASE_URL -f sql/ddl/001_create_dimensions.sql
psql $DATABASE_URL -f sql/ddl/002_create_facts.sql
psql $DATABASE_URL -f sql/ddl/003_create_views.sql
psql $DATABASE_URL -f sql/ddl/004_create_indexes.sql
```

### 2. Airflow DAG Deployment
```bash
# Copy DAG file to Airflow DAGs directory
cp dags/nyse_stock_etl.py $AIRFLOW_HOME/dags/

# Copy SQL files to accessible location
cp -r sql/ $AIRFLOW_HOME/sql/

# Test DAG integrity
airflow dags test nyse_stock_etl 2024-01-01
```

### 3. Connection Configuration
```bash
# Add PostgreSQL connection
airflow connections add postgres_default \
    --conn-type postgres \
    --conn-host localhost \
    --conn-schema ticker_converter \
    --conn-login ticker_user \
    --conn-password $POSTGRES_PASSWORD \
    --conn-port 5432
```

This SQL-centric Airflow implementation provides a robust, maintainable, and scalable ETL pipeline that aligns with the project's simplification goals while leveraging industry best practices for data engineering workflows.
