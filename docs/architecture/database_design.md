# Database Management Architecture Documentation

## Overview

This document details the PostgreSQL database management system implemented following the unified CLI→Orchestrator→Manager→Service architectural pattern.

## Architecture Flow

```
Makefile Commands → CLI (cli_ingestion.py) → Orchestrator → DatabaseManager → PostgreSQL DDL/Operations
```

## Database Schema Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TICKER CONVERTER DATABASE                              │
│                              PostgreSQL Schema                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DIMENSION     │    │   DIMENSION     │    │   DIMENSION     │
│   TABLES        │    │   TABLES        │    │   TABLES        │
│                 │    │                 │    │                 │
│  ┌─────────────┐│    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│  │ dim_stocks  ││    │ │  dim_dates  │ │    │ │dim_currency │ │
│  │             ││    │ │             │ │    │ │             │ │
│  │ • stock_id  ││    │ │ • date_id   │ │    │ │ • curr_id   │ │
│  │ • symbol    ││    │ │ • date      │ │    │ │ • code      │ │
│  │ • name      ││    │ │ • trading   │ │    │ │ • name      │ │
│  │ • sector    ││    │ │   day       │ │    │ │             │ │
│  └─────────────┘│    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FACT TABLES                                        │
│                                                                                 │
│  ┌──────────────────────────┐         ┌──────────────────────────┐             │
│  │   fact_stock_prices      │         │  fact_currency_rates     │             │
│  │                          │         │                          │             │
│  │  • price_id              │         │  • rate_id               │             │
│  │  • stock_id (FK)         │         │  • from_curr_id (FK)     │             │
│  │  • date_id (FK)          │         │  • to_curr_id (FK)       │             │
│  │  • open_usd              │         │  • date_id (FK)          │             │
│  │  • high_usd              │         │  • exchange_rate         │             │
│  │  • low_usd               │         │  • created_at            │             │
│  │  • close_usd             │         │                          │             │
│  │  • volume                │         │                          │             │
│  │  • created_at            │         │                          │             │
│  └──────────────────────────┘         └──────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ANALYTICAL VIEWS                                      │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │ vw_daily_        │  │ vw_latest_       │  │ vw_stock_        │             │
│  │ performance      │  │ stock_prices     │  │ rankings         │             │
│  │                  │  │                  │  │                  │             │
│  │ • Daily returns  │  │ • Current prices │  │ • Performance    │             │
│  │ • % changes      │  │ • Latest values  │  │ • Rankings       │             │
│  │ • Volume info    │  │ • Market data    │  │ • Comparisons    │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            RAW DATA TABLES                                      │
│                         (ETL Staging Areas)                                     │
│                                                                                 │
│  ┌──────────────────────────┐         ┌──────────────────────────┐             │
│  │   raw_stock_data         │         │  raw_currency_data       │             │
│  │                          │         │                          │             │
│  │  • JSON data from APIs   │         │  • JSON data from APIs   │             │
│  │  • Unprocessed format    │         │  • Unprocessed format    │             │
│  │  • Staging for ETL       │         │  • Staging for ETL       │             │
│  └──────────────────────────┘         └──────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. DatabaseManager (`src/ticker_converter/data_ingestion/database_manager.py`)

**Purpose**: Manages PostgreSQL database connections and operations for the data ingestion pipeline.

**Key Features**:
- PostgreSQL-only implementation (SQLite removed)
- DDL-based schema management
- Comprehensive database operations
- Environment-driven configuration
- Proper error handling and logging

**Main Methods**:

#### Connection Management
- `_get_connection_string()`: Get PostgreSQL connection string from environment
- `get_connection()`: Establish PostgreSQL database connection
- `test_connection()`: Test database connectivity

#### Schema Operations
- `create_database_schema()`: Execute DDL files in sequence (001_, 002_, etc.)
- `teardown_database_schema()`: Drop all tables, views, sequences with CASCADE

#### Data Operations
- `execute_query()`: Execute SQL queries with optional result fetching
- `bulk_insert()`: Perform bulk inserts using psycopg2.extras.execute_values
- `check_stocks_table_empty()`: Check if stocks data exists
- `check_exchange_rates_table_empty()`: Check if currency data exists

#### Status Operations
- `needs_initial_setup()`: Determine if database needs initial data loading
- `get_stock_count()`: Get total number of stocks
- `get_price_record_count()`: Get total price records
- `get_exchange_rate_count()`: Get total exchange rate records

### 2. Orchestrator Integration (`src/ticker_converter/data_ingestion/orchestrator.py`)

**Enhanced Methods**:
- `perform_schema_only_setup()`: Create database schema without data loading
- `perform_smart_initial_setup()`: Intelligent data loading with local priority
- `perform_database_teardown()`: Complete database cleanup

### 3. CLI Commands (`src/ticker_converter/cli_ingestion.py`)

**Database Commands**:
- `--init`: Traditional initialization with API data
- `--smart-init`: Smart initialization (local data > dummy data > minimal API)
- `--schema-only`: Create database structure without loading data
- `--teardown`: Complete database teardown (tables, views, sequences)

**Command Functions**:
- `init_database_command()`: Historical data initialization
- `smart_init_database_command()`: Intelligent data loading
- `schema_only_command()`: Schema-only setup
- `teardown_database_command()`: Safe database cleanup

### 4. Makefile Integration

**Database Targets**:
- `make init-db`: Smart initialization (default)
- `make init-schema`: Schema-only setup
- `make teardown-db`: Complete database teardown

## Database Initialization and Teardown Procedures

### Setup Process Overview

The database initialization follows a multi-step process with intelligent data loading strategies:

```
1. Environment Check → 2. Schema Creation → 3. Data Loading → 4. Validation
       ↓                      ↓                   ↓              ↓
   Check DATABASE_URL    Execute DDL Files    Load Stock Data   Health Check
   Validate Connection   Create Tables        Load Currency     Record Counts
   Parse Configuration   Create Views         Load Exchange     Status Report
                        Create Indexes        Rate Data
```

### Initialization Commands

#### 1. Schema-Only Setup
Creates database structure without loading any data - ideal for development and testing:

```bash
# Via Makefile (recommended)
make init-schema

# Via CLI directly
python -m ticker_converter.cli_ingestion --schema-only
```

**What happens internally:**
```python
# 1. DatabaseManager validates connection
database_manager = DatabaseManager()
connection_result = database_manager.test_connection()

# 2. Execute DDL files in sequence
ddl_results = database_manager.create_database_schema()
# Executes: 001_create_dimensions.sql → 002_create_facts.sql → 
#          003_create_views.sql → 004_create_indexes.sql

# 3. Verify schema creation
tables_created = database_manager.get_schema_objects()
```

#### 2. Smart Initialization
Intelligent data loading with local file priority:

```bash
# Via Makefile (recommended)
make init-db

# Via CLI directly  
python -m ticker_converter.cli_ingestion --smart-init
```

**Data Source Priority Logic:**
```python
# 1. Check for real data files
if exists("raw_data/stocks/*.json") and exists("raw_data/exchange/*.json"):
    data_source = "real_local_data"
    load_all_available_files()
    
# 2. Fall back to dummy data (testing)
elif exists("raw_data/dummy_stocks/") and exists("raw_data/dummy_exchange/"):
    data_source = "dummy_data_one_day"
    load_single_day_sample()
    
# 3. Fetch from API (minimal to avoid rate limits)
else:
    data_source = "api_minimal"
    fetch_apple_stock_data(days=1)
    fetch_usd_gbp_exchange_data(days=1)
```

#### 3. Traditional Initialization
Fetch specific days of historical data from API:

```bash
# Fetch 30 days of historical data
python -m ticker_converter.cli_ingestion --init --days 30
```

### Teardown Process

#### Complete Database Teardown
**⚠️ WARNING: This permanently deletes all data!**

```bash
# Via Makefile (with confirmation prompt)
make teardown-db

# Via CLI directly
python -m ticker_converter.cli_ingestion --teardown
```

**Teardown Sequence:**
```python
# 1. Safety confirmation
user_input = input("Type 'yes' to confirm database teardown: ")
if user_input.lower() != 'yes':
    exit("Teardown cancelled")

# 2. Drop objects in dependency order
teardown_results = database_manager.teardown_database_schema()

# Order of operations:
# a) Drop views first (they depend on tables)
DROP VIEW IF EXISTS vw_daily_performance CASCADE;
DROP VIEW IF EXISTS vw_latest_stock_prices CASCADE;
DROP VIEW IF EXISTS vw_stock_rankings CASCADE;

# b) Drop tables with CASCADE (handles foreign keys)
DROP TABLE IF EXISTS fact_stock_prices CASCADE;
DROP TABLE IF EXISTS fact_currency_rates CASCADE;
DROP TABLE IF EXISTS raw_stock_data CASCADE;
DROP TABLE IF EXISTS raw_currency_data CASCADE;
DROP TABLE IF EXISTS dim_stocks CASCADE;
DROP TABLE IF EXISTS dim_dates CASCADE;
DROP TABLE IF EXISTS dim_currency CASCADE;

# c) Drop sequences and functions
DROP SEQUENCE IF EXISTS stock_id_seq CASCADE;
DROP SEQUENCE IF EXISTS date_id_seq CASCADE;
```

### Database Status and Health Checks

#### Check Database Status
```bash
# Via Makefile
make status

# Via CLI
python -m ticker_converter.cli_ingestion status
```

**Health Check Output:**
```
Database status: online (postgresql://localhost:5432/ticker_converter)
Stock records: 1,470
Currency records: 30
Last stock update: 2025-08-11T16:30:00
Last currency update: 2025-08-11T16:30:00
Database is ready: true
```

#### Programmatic Health Check
```python
from ticker_converter.data_ingestion.database_manager import DatabaseManager

db_manager = DatabaseManager()
health_status = db_manager.health_check()

# Returns:
{
    "status": "online",
    "database_url": "postgresql://localhost:5432/ticker_converter",
    "stock_records": 1470,
    "price_records": 10290,
    "currency_records": 30,
    "latest_stock_date": "2025-08-11T16:30:00",
    "latest_currency_date": "2025-08-11T16:30:00",
    "is_empty": false
}
```

### Environment Configuration

#### Required Environment Variables
```bash
# .env file
DATABASE_URL=postgresql://username@localhost:5432/ticker_converter

# Alternative individual settings (DATABASE_URL takes precedence)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticker_converter
POSTGRES_USER=username
POSTGRES_PASSWORD=password123
```

#### Connection String Validation
```python
# The system validates connection strings on startup
def _get_connection_string(self) -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable required")
    
    if not database_url.startswith("postgresql://"):
        raise ValueError("DATABASE_URL must be PostgreSQL connection string")
    
    return database_url
```

### Error Handling and Recovery

#### Common Setup Issues and Solutions

**1. Connection Failures**
```bash
# Error: could not connect to server
# Solution: Verify PostgreSQL is running
brew services start postgresql
# or
sudo systemctl start postgresql
```

**2. Permission Issues**
```bash
# Error: permission denied for database
# Solution: Grant proper permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO username;"
```

**3. DDL Execution Failures**
```python
# System continues with next DDL file on individual failures
# Check logs for specific errors:
tail -f logs/database_setup.log
```

**4. Partial Data Loading**
```python
# Smart initialization will report which data sources were used:
{
    "data_source": "dummy_data_one_day",
    "stock_data": {"records_inserted": 1, "source": "dummy_data_one_day"},
    "currency_data": {"records_inserted": 1, "source": "dummy_data_one_day"},
    "errors": []
}
```

### Database Schema Management

### DDL File Execution Order
1. `001_create_dimensions.sql`: Dimension tables (stocks, dates, currency)
2. `002_create_facts.sql`: Fact tables (stock prices, exchange rates)
3. `003_create_views.sql`: Analytical views
4. `004_create_indexes.sql`: Performance indexes

### Statement Parsing
- Splits DDL files by semicolon
- Removes comments and empty lines
- Executes statements individually to handle PostgreSQL limitations

### Schema Objects Created
**Tables**: `dim_stocks`, `dim_date`, `dim_currency`, `fact_stock_prices`, `fact_currency_rates`, `raw_stock_data`, `raw_currency_data`

**Views**: `vw_daily_performance`, `vw_latest_stock_prices`, `vw_stock_rankings`

**Indexes**: Performance optimized indexes for analytical queries

## Configuration

### Environment Variables (`.env` file)

```bash
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://willhuntleyclarke@localhost:5432/ticker_converter

# Alternative individual settings (DATABASE_URL takes precedence)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticker_converter
POSTGRES_USER=willhuntleyclarke
POSTGRES_PASSWORD=password123
```

## Data Loading Strategies

### 1. Smart Initialization (`--smart-init`)
**Priority Order**:
1. Real data from `raw_data/stocks/` and `raw_data/exchange/` (use all available)
2. Dummy data from test fixtures (use 1 day for testing)
3. API data (fetch minimal data to avoid rate limits)

### 2. Schema-Only Setup (`--schema-only`)
- Creates all database objects
- No data loading
- Useful for testing and development environments

### 3. Traditional Setup (`--init`)
- Fetches specified days of historical data from API
- Standard initialization approach

## Usage Examples

### Schema Setup
```bash
# Create database structure only
make init-schema
python -m ticker_converter.cli_ingestion --schema-only
```

### Smart Data Loading
```bash
# Intelligent data loading with local priority
make init-db
python -m ticker_converter.cli_ingestion --smart-init
```

### Database Cleanup
```bash
# Complete database teardown
make teardown-db
python -m ticker_converter.cli_ingestion --teardown
```

## Teardown Process

### Objects Dropped (in order)
1. **Views**: Dropped first to handle dependencies
2. **Tables**: Dropped with CASCADE to handle foreign keys
3. **Sequences**: Cleanup of auto-increment sequences
4. **Functions**: Any stored procedures (if present)

### Safety Features
- Double confirmation (Makefile warning + CLI prompt)
- Detailed logging of dropped objects
- Graceful error handling for missing objects

## Testing Results

### ✅ Schema Creation
- Successfully executed all DDL files: `001_create_dimensions.sql`, `002_create_facts.sql`, `003_create_views.sql`, `004_create_indexes.sql`
- Proper statement parsing and execution
- PostgreSQL-specific syntax handling

### ✅ Database Teardown
- Successfully dropped 10 objects:
  - 3 views: `vw_daily_performance`, `vw_latest_stock_prices`, `vw_stock_rankings`
  - 7 tables: `dim_currency`, `dim_date`, `dim_stocks`, `fact_currency_rates`, `fact_stock_prices`, `raw_currency_data`, `raw_stock_data`
- Proper CASCADE handling
- Clean database state verification

### ✅ Smart Initialization
- Local data detection working
- Fallback mechanisms functioning
- Proper error handling and reporting

## Error Handling

### Connection Issues
- Clear error messages for missing DATABASE_URL
- Validation of PostgreSQL connection strings
- Graceful handling of connection failures

### Schema Issues
- Individual DDL file error handling
- Continues execution when possible
- Detailed error reporting with file names

### Data Issues
- Graceful handling of missing local data
- Fallback to alternative data sources
- Clear reporting of data source used

## Benefits

### PostgreSQL-Only Architecture
- Removed SQLite complexity and maintenance burden
- Consistent database behavior across environments
- Better performance and feature set

### DDL-Based Schema Management
- Version-controlled schema changes
- Repeatable deployments
- Clear separation of schema and data

### Flexible Data Loading
- Supports various development and testing scenarios
- Reduces API usage during development
- Intelligent fallback mechanisms

## Database Operations and SQL Query Examples

This section demonstrates how to interact with and manipulate the database using SQL queries, organized by common use cases.

### 1. Basic Data Retrieval

#### Get Latest Stock Prices
```sql
-- Retrieve the most recent closing prices for all stocks
SELECT 
    s.symbol,
    s.company_name,
    p.close_usd,
    p.volume,
    d.date
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date = (
    SELECT MAX(date) 
    FROM dim_dates 
    WHERE is_trading_day = TRUE
)
ORDER BY s.symbol;
```

#### Get Stock Price History
```sql
-- Get 30-day price history for Apple
SELECT 
    d.date,
    p.open_usd,
    p.high_usd,
    p.low_usd,
    p.close_usd,
    p.volume
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE s.symbol = 'AAPL'
  AND d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY d.date DESC;
```

### 2. Data Insertion and Updates

#### Insert New Stock Data
```sql
-- Insert a new stock into the dimension table
INSERT INTO dim_stocks (symbol, company_name, sector, market_cap)
VALUES ('NFLX', 'Netflix Inc', 'Technology', 180000000000);

-- Insert stock price data
INSERT INTO fact_stock_prices (
    stock_id, 
    date_id, 
    open_usd, 
    high_usd, 
    low_usd, 
    close_usd, 
    volume
)
SELECT 
    s.stock_id,
    d.date_id,
    450.25,  -- open
    455.80,  -- high
    448.10,  -- low
    452.30,  -- close
    1250000  -- volume
FROM dim_stocks s
CROSS JOIN dim_dates d
WHERE s.symbol = 'NFLX'
  AND d.date = '2025-08-11';
```

#### Bulk Insert with Conflict Resolution
```sql
-- Insert multiple currency rates with ON CONFLICT handling
INSERT INTO fact_currency_rates (
    from_currency_id, 
    to_currency_id, 
    date_id, 
    exchange_rate
)
VALUES 
    ((SELECT currency_id FROM dim_currencies WHERE code = 'USD'),
     (SELECT currency_id FROM dim_currencies WHERE code = 'GBP'),
     (SELECT date_id FROM dim_dates WHERE date = '2025-08-11'),
     0.7850),
    ((SELECT currency_id FROM dim_currencies WHERE code = 'USD'),
     (SELECT currency_id FROM dim_currencies WHERE code = 'EUR'),
     (SELECT date_id FROM dim_dates WHERE date = '2025-08-11'),
     0.9200)
ON CONFLICT (from_currency_id, to_currency_id, date_id) 
DO UPDATE SET 
    exchange_rate = EXCLUDED.exchange_rate,
    updated_at = CURRENT_TIMESTAMP;
```

### 3. Data Analysis and Calculations

### 3. Data Analysis and Calculations

#### Calculate Daily Returns
```sql
-- Calculate daily return percentage for each stock
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    LAG(p.close_usd) OVER (
        PARTITION BY s.symbol 
        ORDER BY d.date
    ) as prev_close,
    ROUND(
        ((p.close_usd - LAG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date
        )) / LAG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date
        )) * 100, 
        2
    ) as daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY s.symbol, d.date;
```

#### Moving Averages
```sql
-- Calculate 5-day and 20-day moving averages
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_5_day,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_20_day,
    -- Trading signal based on moving average crossover
    CASE 
        WHEN AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) > AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) THEN 'BUY'
        ELSE 'SELL'
    END as signal
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY s.symbol, d.date;
```

### 4. Data Maintenance and Cleanup

#### Update Stock Information
```sql
-- Update company information (e.g., after stock split or company name change)
UPDATE dim_stocks 
SET 
    company_name = 'Meta Platforms Inc',
    market_cap = 850000000000,
    updated_at = CURRENT_TIMESTAMP
WHERE symbol = 'META';
```

#### Delete Old Data
```sql
-- Remove data older than 2 years (with safety check)
DO $$
DECLARE 
    cutoff_date DATE := CURRENT_DATE - INTERVAL '2 years';
    affected_rows INTEGER;
BEGIN
    -- Delete old stock prices
    DELETE FROM fact_stock_prices 
    WHERE date_id IN (
        SELECT date_id FROM dim_dates 
        WHERE date < cutoff_date
    );
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'Deleted % stock price records older than %', affected_rows, cutoff_date;
    
    -- Delete old currency rates
    DELETE FROM fact_currency_rates 
    WHERE date_id IN (
        SELECT date_id FROM dim_dates 
        WHERE date < cutoff_date
    );
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'Deleted % currency rate records older than %', affected_rows, cutoff_date;
    
    -- Clean up orphaned date records
    DELETE FROM dim_dates 
    WHERE date < cutoff_date
      AND date_id NOT IN (
          SELECT DISTINCT date_id FROM fact_stock_prices 
          UNION 
          SELECT DISTINCT date_id FROM fact_currency_rates
      );
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'Deleted % orphaned date records', affected_rows;
END $$;
```

#### Refresh Materialized Views (if using)
```sql
-- Refresh performance views after data updates
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_performance;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_stock_rankings;
```

### 5. Advanced Analytics

#### Stock Correlation Analysis
```sql
-- Calculate correlation between Apple and Microsoft returns
WITH stock_returns AS (
    SELECT 
        d.date,
        s.symbol,
        ROUND(
            ((p.close_usd - LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) / LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) * 100, 
            4
        ) as daily_return_pct
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE s.symbol IN ('AAPL', 'MSFT')
      AND d.date >= CURRENT_DATE - INTERVAL '90 days'
),
paired_returns AS (
    SELECT 
        a.date,
        a.daily_return_pct as aapl_return,
        m.daily_return_pct as msft_return
    FROM stock_returns a
    JOIN stock_returns m ON a.date = m.date
    WHERE a.symbol = 'AAPL' 
      AND m.symbol = 'MSFT'
      AND a.daily_return_pct IS NOT NULL
      AND m.daily_return_pct IS NOT NULL
)
SELECT 
    COUNT(*) as observations,
    ROUND(CORR(aapl_return, msft_return)::numeric, 4) as correlation_coefficient,
    ROUND(AVG(aapl_return)::numeric, 4) as avg_aapl_return,
    ROUND(AVG(msft_return)::numeric, 4) as avg_msft_return,
    ROUND(STDDEV(aapl_return)::numeric, 4) as aapl_volatility,
    ROUND(STDDEV(msft_return)::numeric, 4) as msft_volatility
FROM paired_returns;
```

#### Portfolio Performance Analysis
```sql
-- Calculate portfolio performance assuming equal weights
WITH portfolio_returns AS (
    SELECT 
        d.date,
        AVG(
            ((p.close_usd - LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) / LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) * 100
        ) as portfolio_return_pct
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
      AND s.symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA')
    GROUP BY d.date
),
cumulative_returns AS (
    SELECT 
        date,
        portfolio_return_pct,
        SUM(portfolio_return_pct) OVER (ORDER BY date) as cumulative_return_pct
    FROM portfolio_returns
    WHERE portfolio_return_pct IS NOT NULL
)
SELECT 
    date,
    ROUND(portfolio_return_pct, 2) as daily_return,
    ROUND(cumulative_return_pct, 2) as cumulative_return,
    CASE 
        WHEN cumulative_return_pct > 5 THEN 'Strong Positive'
        WHEN cumulative_return_pct > 0 THEN 'Positive'
        WHEN cumulative_return_pct > -5 THEN 'Negative'
        ELSE 'Strong Negative'
    END as performance_category
FROM cumulative_returns
ORDER BY date DESC;
```

### 6. Data Quality and Monitoring

#### Data Quality Checks
```sql
-- Comprehensive data quality report
WITH quality_checks AS (
    -- Check for missing data
    SELECT 
        'Missing Stock Data' as check_type,
        COUNT(*) as issues_found,
        'Expected daily data for all 7 stocks' as description
    FROM (
        SELECT d.date, COUNT(DISTINCT s.symbol) as stocks_reported
        FROM dim_dates d
        CROSS JOIN dim_stocks s
        LEFT JOIN fact_stock_prices p ON d.date_id = p.date_id AND s.stock_id = p.stock_id
        WHERE d.is_trading_day = TRUE
          AND d.date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY d.date
        HAVING COUNT(DISTINCT s.symbol) < 7
    ) missing_data
    
    UNION ALL
    
    -- Check for price anomalies
    SELECT 
        'Price Anomalies' as check_type,
        COUNT(*) as issues_found,
        'High/Low price inconsistencies' as description
    FROM fact_stock_prices p
    WHERE p.high_usd < p.low_usd 
       OR p.high_usd < p.open_usd 
       OR p.high_usd < p.close_usd
       OR p.low_usd > p.open_usd 
       OR p.low_usd > p.close_usd
    
    UNION ALL
    
    -- Check for extreme returns
    SELECT 
        'Extreme Returns' as check_type,
        COUNT(*) as issues_found,
        'Daily returns > 20%' as description
    FROM (
        SELECT 
            s.symbol,
            d.date,
            ABS((p.close_usd - LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) / LAG(p.close_usd) OVER (
                PARTITION BY s.symbol ORDER BY d.date
            )) * 100 as abs_return_pct
        FROM fact_stock_prices p
        JOIN dim_stocks s ON p.stock_id = s.stock_id
        JOIN dim_dates d ON p.date_id = d.date_id
        WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
    ) returns
    WHERE abs_return_pct > 20
)
SELECT 
    check_type,
    issues_found,
    description,
    CASE 
        WHEN issues_found = 0 THEN '✅ PASS'
        WHEN issues_found < 5 THEN '⚠️ MINOR ISSUES'
        ELSE '❌ MAJOR ISSUES'
    END as status
FROM quality_checks
ORDER BY issues_found DESC;
```

#### Performance Monitoring
```sql
-- Database performance metrics
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_stat_get_tuples_returned(c.oid) as rows_read,
    pg_stat_get_tuples_fetched(c.oid) as rows_fetched,
    pg_stat_get_tuples_inserted(c.oid) as rows_inserted,
    pg_stat_get_tuples_updated(c.oid) as rows_updated,
    pg_stat_get_tuples_deleted(c.oid) as rows_deleted
FROM pg_tables pt
JOIN pg_class c ON c.relname = pt.tablename
WHERE schemaname = 'public'
  AND (tablename LIKE 'fact_%' OR tablename LIKE 'dim_%')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 7. ETL and Data Pipeline Queries

#### Data Transformation Pipeline
```sql
-- Transform raw stock data into fact table format
INSERT INTO fact_stock_prices (
    stock_id, 
    date_id, 
    open_usd, 
    high_usd, 
    low_usd, 
    close_usd, 
    volume
)
SELECT 
    s.stock_id,
    d.date_id,
    (raw_data->>'open')::numeric as open_usd,
    (raw_data->>'high')::numeric as high_usd,
    (raw_data->>'low')::numeric as low_usd,
    (raw_data->>'close')::numeric as close_usd,
    (raw_data->>'volume')::bigint as volume
FROM raw_stock_data rsd
JOIN dim_stocks s ON s.symbol = rsd.symbol
JOIN dim_dates d ON d.date = (rsd.raw_data->>'date')::date
WHERE rsd.processed_at IS NULL
ON CONFLICT (stock_id, date_id) DO UPDATE SET
    open_usd = EXCLUDED.open_usd,
    high_usd = EXCLUDED.high_usd,
    low_usd = EXCLUDED.low_usd,
    close_usd = EXCLUDED.close_usd,
    volume = EXCLUDED.volume,
    updated_at = CURRENT_TIMESTAMP;

-- Mark raw data as processed
UPDATE raw_stock_data 
SET processed_at = CURRENT_TIMESTAMP 
WHERE processed_at IS NULL;
```

#### Daily Top 5 Performers
```sql
-- Get top 5 stocks by daily return percentage
SELECT 
    s.symbol,
    s.company_name,
    d.date,
    p.close_usd,
    ROUND(
        ((p.close_usd - LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) 
         / LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) * 100, 
        2
    ) as daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date = CURRENT_DATE - INTERVAL '1 day'
  AND LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date) IS NOT NULL
ORDER BY daily_return_pct DESC
LIMIT 5;
```

#### Weekly Top Performers
```sql
-- Get top performers over the last 7 trading days
WITH weekly_performance AS (
    SELECT 
        s.symbol,
        s.company_name,
        MIN(p.close_usd) as week_start_price,
        MAX(p.close_usd) as week_end_price,
        COUNT(*) as trading_days
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE d.date >= CURRENT_DATE - INTERVAL '7 days'
      AND d.is_trading_day = TRUE
    GROUP BY s.symbol, s.company_name
    HAVING COUNT(*) >= 5  -- At least 5 trading days
)
SELECT 
    symbol,
    company_name,
    week_start_price,
    week_end_price,
    ROUND(
        ((week_end_price - week_start_price) / week_start_price) * 100, 
        2
    ) as weekly_return_pct
FROM weekly_performance
ORDER BY weekly_return_pct DESC;
```

### Currency Conversion Examples

#### Stock Prices in GBP
```sql
-- Convert all stock prices to GBP using daily exchange rates
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    cr.exchange_rate as usd_to_gbp_rate,
    ROUND(p.close_usd / cr.exchange_rate, 4) as close_gbp,
    ROUND(p.open_usd / cr.exchange_rate, 4) as open_gbp,
    ROUND(p.high_usd / cr.exchange_rate, 4) as high_gbp,
    ROUND(p.low_usd / cr.exchange_rate, 4) as low_gbp
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN fact_currency_rates cr ON d.date_id = cr.date_id
WHERE cr.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
  AND cr.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP')
  AND d.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY s.symbol, d.date;
```

### Data Quality Validation

#### Missing Data Detection
```sql
-- Identify missing trading days or stock data
WITH expected_trading_days AS (
    SELECT DISTINCT date_id, date
    FROM dim_dates
    WHERE is_trading_day = TRUE
      AND date >= CURRENT_DATE - INTERVAL '30 days'
),
actual_data AS (
    SELECT DISTINCT 
        p.date_id, 
        s.symbol,
        COUNT(*) OVER (PARTITION BY p.date_id) as stocks_reported
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    WHERE p.date_id IN (SELECT date_id FROM expected_trading_days)
)
SELECT 
    etd.date,
    COALESCE(ad.stocks_reported, 0) as stocks_reported,
    (SELECT COUNT(*) FROM dim_stocks) as expected_stocks,
    CASE 
        WHEN COALESCE(ad.stocks_reported, 0) < (SELECT COUNT(*) FROM dim_stocks) 
        THEN 'INCOMPLETE DATA'
        ELSE 'COMPLETE'
    END as data_status
FROM expected_trading_days etd
LEFT JOIN actual_data ad ON etd.date_id = ad.date_id
ORDER BY etd.date DESC;
```

### Performance Optimization

#### Recommended Indexes
```sql
-- Primary indexes for fact tables
CREATE INDEX idx_fact_stock_prices_date_stock ON fact_stock_prices(date_id, stock_id);
CREATE INDEX idx_fact_stock_prices_stock_date ON fact_stock_prices(stock_id, date_id);
CREATE INDEX idx_fact_currency_rates_date ON fact_currency_rates(date_id);

-- Indexes for common WHERE clauses
CREATE INDEX idx_dim_dates_date ON dim_dates(date);
CREATE INDEX idx_dim_dates_trading_day ON dim_dates(is_trading_day, date);
CREATE INDEX idx_dim_stocks_symbol ON dim_stocks(symbol);
CREATE INDEX idx_dim_currencies_code ON dim_currencies(code);
```

### Moving Averages
```sql
-- Calculate 5-day and 20-day moving averages
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_5_day,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_20_day
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY s.symbol, d.date;
```

### API Query Templates

#### FastAPI Endpoint Queries

**Top Performers Endpoint**
```sql
-- File: sql/queries/top_performers.sql
SELECT symbol, daily_return_pct, close_usd, date 
FROM v_top_performers 
WHERE daily_return_pct IS NOT NULL 
ORDER BY daily_return_pct DESC 
LIMIT 5;
```

**Price Range Endpoint**
```sql
-- File: sql/queries/price_ranges.sql
SELECT 
    s.symbol,
    s.company_name,
    p.close_usd,
    d.date
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE p.close_usd BETWEEN $1 AND $2
  AND d.date = (SELECT MAX(date) FROM dim_dates WHERE is_trading_day = TRUE)
ORDER BY p.close_usd DESC;
```

### Best Practices

#### Query Optimization
1. **Use appropriate indexes** for WHERE and JOIN clauses
2. **Limit result sets** with proper LIMIT clauses
3. **Use views** for complex, reusable calculations
4. **Partition large tables** by date when volume grows
5. **Analyze query plans** with EXPLAIN for optimization

#### Data Quality
1. **Implement CHECK constraints** on fact tables
2. **Use NOT NULL constraints** for critical fields
3. **Create validation views** for data quality monitoring
4. **Set up alerts** for data anomalies

#### Maintainability
1. **Store complex queries** in separate .sql files
2. **Document query logic** with comments
3. **Use consistent naming** conventions
4. **Version control** all SQL scripts
5. **Test queries** with sample data before production

## Future Enhancements

1. **Migration System**: Database migration management for schema changes
2. **Backup/Restore**: Automated backup and restore capabilities
3. **Data Validation**: Enhanced data integrity checks
4. **Performance Monitoring**: Database performance metrics and optimization
5. **Connection Pooling**: Connection pool management for high-load scenarios
