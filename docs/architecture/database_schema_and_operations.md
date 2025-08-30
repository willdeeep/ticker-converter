# Database Schema and Operations Reference

## Executive Summary

This document provides comprehensive reference documentation for the PostgreSQL database schema, normalization strategy, and operational procedures in the ticker-converter system. The database implements a **star schema design (3NF normalized dimensions with denormalized fact tables)** optimized for analytical workloads while maintaining data integrity and operational flexibility.

**Database Value Proposition**: A carefully designed dimensional model that balances normalization benefits (data integrity, reduced redundancy) with analytical performance (denormalized facts for fast aggregations), supporting both transactional operations and analytical queries.

## Database Normalization Strategy

### Normalization Level: **Mixed 3NF/Star Schema Design**

The ticker-converter database implements a **hybrid normalization approach** that combines the benefits of normalized dimension tables with denormalized fact tables for optimal analytical performance:

#### **Dimension Tables: 3rd Normal Form (3NF)**
- **Reasoning**: Dimensions change infrequently and benefit from normalization
- **Benefits**: Data integrity, reduced redundancy, easier maintenance
- **Trade-off**: Additional JOINs required for queries (acceptable for analytical workloads)

#### **Fact Tables: Denormalized Design**
- **Reasoning**: Facts are write-heavy and read-heavy for analytics
- **Benefits**: Fast aggregations, fewer JOINs, optimal for time-series analysis
- **Trade-off**: Some data duplication (controlled and acceptable)

### Detailed Normalization Analysis

#### **3NF Compliance in Dimensions**

**`dim_stocks` (3NF Compliant)**:
```sql
-- Satisfies 1NF: Atomic values, unique rows
-- Satisfies 2NF: No partial dependencies (single-column PK)
-- Satisfies 3NF: No transitive dependencies
CREATE TABLE dim_stocks (
    stock_id SERIAL PRIMARY KEY,           -- Surrogate key
    symbol VARCHAR(10) UNIQUE NOT NULL,    -- Natural key
    company_name VARCHAR(255) NOT NULL,    -- Directly dependent on stock_id
    sector VARCHAR(100),                   -- Directly dependent on stock_id
    exchange VARCHAR(10) NOT NULL          -- Directly dependent on stock_id
);
```

**`dim_dates` (3NF Compliant)**:
```sql
-- Optimized for date-based analytics with computed attributes
CREATE TABLE dim_dates (
    date_id SERIAL PRIMARY KEY,           -- Surrogate key
    date DATE UNIQUE NOT NULL,            -- Natural key
    year INTEGER NOT NULL,                -- Computed from date (acceptable redundancy)
    month INTEGER NOT NULL,               -- Computed from date (acceptable redundancy)
    quarter INTEGER NOT NULL,             -- Computed from date (acceptable redundancy)
    day_of_week INTEGER NOT NULL,         -- Computed from date (acceptable redundancy)
    is_trading_day BOOLEAN DEFAULT true   -- Business rule attribute
);
```

**`dim_currencies` (3NF Compliant)**:
```sql
CREATE TABLE dim_currencies (
    currency_id SERIAL PRIMARY KEY,       -- Surrogate key
    code VARCHAR(3) UNIQUE NOT NULL,      -- Natural key (ISO 4217)
    name VARCHAR(100) NOT NULL,           -- Directly dependent on currency_id
    country VARCHAR(100)                  -- Directly dependent on currency_id
);
```

#### **Fact Table Denormalization Strategy**

**`fact_stock_prices` (Intentionally Denormalized)**:
```sql
-- Denormalized for analytical performance
CREATE TABLE fact_stock_prices (
    price_id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id INTEGER NOT NULL REFERENCES dim_dates(date_id),
    -- OHLCV data: denormalized for fast aggregations
    open_usd DECIMAL(10,4) NOT NULL,
    high_usd DECIMAL(10,4) NOT NULL,
    low_usd DECIMAL(10,4) NOT NULL,
    close_usd DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    -- Computed fields for performance (controlled denormalization)
    daily_return DECIMAL(8,4),            -- Could be computed, stored for performance
    volume_weighted_price DECIMAL(10,4),   -- Could be computed, stored for performance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`fact_currency_rates` (Intentionally Denormalized)**:
```sql
-- Denormalized for fast currency conversion
CREATE TABLE fact_currency_rates (
    rate_id BIGSERIAL PRIMARY KEY,
    from_currency_id INTEGER NOT NULL REFERENCES dim_currencies(currency_id),
    to_currency_id INTEGER NOT NULL REFERENCES dim_currencies(currency_id),
    date_id INTEGER NOT NULL REFERENCES dim_dates(date_id),
    exchange_rate DECIMAL(12,8) NOT NULL, -- High precision for financial calculations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Normalization Trade-offs Analysis

| Aspect | 3NF Dimensions | Denormalized Facts | Rationale |
|--------|----------------|-------------------|-----------|
| **Data Integrity** | High | Controlled | Dimensions enforce referential integrity |
| **Storage Efficiency** | Optimal | Some redundancy | Facts optimized for query performance |
| **Query Performance** | Requires JOINs | Fast aggregations | Trade-off favoring analytical workloads |
| **Update Complexity** | Simple | Moderate | Dimensions rarely change, facts are append-only |
| **Maintenance Overhead** | Low | Low | Well-defined patterns reduce complexity |

## Schema Design Patterns

### Star Schema Implementation

The database follows **star schema design principles** with clear fact and dimension separation:

```
                    dim_dates
                        |
                    (date_id)
                        |
    dim_stocks ── fact_stock_prices ── dim_currencies
       |              |                     |
   (stock_id)    [Central Fact]      (currency_id)
                      |
              fact_currency_rates
                      |
                 dim_currencies
```

### Surrogate Key Strategy

**Why Surrogate Keys**:
- **Stability**: Natural keys may change (stock symbols can be reused)
- **Performance**: Integer keys are faster for JOINs than varchar keys
- **Independence**: Database keys independent of business rules

**Key Patterns**:
```sql
-- Pattern: Auto-incrementing surrogate + unique natural key
stock_id SERIAL PRIMARY KEY,           -- Surrogate (database)
symbol VARCHAR(10) UNIQUE NOT NULL,    -- Natural (business)
```

### Temporal Data Handling

**Date Dimension Strategy**:
- Pre-populated date dimension for performance
- Supports both calendar and business date logic
- Enables complex date-based analytics

**Time-Series Optimization**:
- Fact tables optimized for time-series queries
- Composite indexes on (date_id, stock_id) for performance
- Partition-ready design for future scaling

## Database Operations Architecture

### DDL Management Strategy

The database schema is managed through **version-controlled DDL files** executed in sequence:

#### **Execution Order (Dependency-Driven)**
1. **`001_create_dimensions.sql`**: Dimension tables (no dependencies)
2. **`002_create_facts.sql`**: Fact tables (reference dimensions)
3. **`003_create_views.sql`**: Analytical views (reference facts/dimensions)
4. **`004_create_indexes.sql`**: Performance indexes (reference all tables)

#### **DDL File Structure Standards**
```sql
-- File: 001_create_dimensions.sql
-- Purpose: Create all dimension tables
-- Dependencies: None
-- Idempotency: DROP IF EXISTS + CREATE

-- Stock dimension (3NF normalized)
DROP TABLE IF EXISTS dim_stocks CASCADE;
CREATE TABLE dim_stocks (
    stock_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    exchange VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Manager Architecture

**Connection Flow**:
```
Makefile Commands → CLI → Orchestrator → DatabaseManager → PostgreSQL
```

**Key Management Features**:
- **Environment-driven configuration**: Database URLs from `.env`
- **Connection pooling ready**: Designed for future pooling implementation
- **Error handling**: Comprehensive error reporting with context
- **Transaction management**: Explicit transaction boundaries for data operations

## Analytical Views Design

### Performance-Optimized Views

The database includes **materialized view candidates** designed for common analytical queries:

#### **`vw_daily_performance`**: Daily Stock Performance Analytics
```sql
-- Combines facts with dimensions for daily analytics
CREATE VIEW vw_daily_performance AS
SELECT 
    s.symbol,
    s.company_name,
    s.sector,
    d.date,
    p.close_usd,
    p.volume,
    LAG(p.close_usd) OVER (PARTITION BY s.stock_id ORDER BY d.date) as prev_close,
    p.daily_return,
    p.volume_weighted_price
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
ORDER BY d.date DESC, s.symbol;
```

#### **`vw_latest_stock_prices`**: Current Stock Positions
```sql
-- Latest price for each stock (optimized for API endpoints)
CREATE VIEW vw_latest_stock_prices AS
SELECT DISTINCT ON (s.stock_id)
    s.symbol,
    s.company_name,
    p.close_usd as current_price,
    p.volume as current_volume,
    d.date as price_date
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
ORDER BY s.stock_id, d.date DESC;
```

### View Design Principles
- **Denormalized output**: Views pre-JOIN facts with dimensions
- **Performance focused**: Designed for common API query patterns
- **Materialization ready**: Can be converted to materialized views for performance
- **Aggregation friendly**: Support GROUP BY and window function operations

## Index Strategy for Performance

### Primary Indexes (Performance Critical)

```sql
-- Fact table performance indexes
CREATE INDEX idx_fact_stock_prices_date_stock 
ON fact_stock_prices(date_id, stock_id);

CREATE INDEX idx_fact_stock_prices_stock_date 
ON fact_stock_prices(stock_id, date_id DESC); -- Time-series optimization

-- Dimension table performance indexes
CREATE INDEX idx_dim_stocks_symbol 
ON dim_stocks(symbol); -- Natural key lookup

CREATE INDEX idx_dim_dates_date 
ON dim_dates(date); -- Date range queries
```

### Composite Index Strategy
- **Query pattern driven**: Indexes match common WHERE clause patterns
- **Sort optimization**: DESC indexes for time-series queries
- **Covering indexes**: Include frequently accessed columns

## Data Loading and ETL Integration

### ETL-Optimized Schema Design

**Direct Fact Loading** (Streamlined ETL):
```sql
-- No staging tables - direct insertion into dimensional model
-- Data validation and transformation handled in Python layer
-- Date dimensions automatically populated during insertion
```

**ETL Processing Patterns**:
1. **Extract**: API responses processed in Python with validation
2. **Transform**: Data cleansing and type conversion in Python
3. **Load**: Direct bulk INSERT operations into fact tables with dimensional lookups
4. **Validate**: Data quality enforced at application layer and database constraints

### Bulk Loading Optimization

**Copy-Optimized Design**:
- No unnecessary constraints during bulk loading
- Deferred constraint checking
- Batch processing with transaction boundaries

**Example Bulk Insert Pattern**:
```python
# Optimized for PostgreSQL bulk loading
def bulk_insert_stock_prices(self, price_data):
    insert_query = """
    INSERT INTO fact_stock_prices 
    (stock_id, date_id, open_usd, high_usd, low_usd, close_usd, volume)
    VALUES %s
    ON CONFLICT (stock_id, date_id) DO UPDATE SET
        open_usd = EXCLUDED.open_usd,
        high_usd = EXCLUDED.high_usd,
        low_usd = EXCLUDED.low_usd,
        close_usd = EXCLUDED.close_usd,
        volume = EXCLUDED.volume,
        updated_at = CURRENT_TIMESTAMP
    """
    # Uses psycopg2.extras.execute_values for performance
```

This comprehensive database schema and operations reference provides the foundation for understanding both the strategic design decisions and practical implementation details of the ticker-converter's data architecture.

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

### Schema Creation
- Successfully executed all DDL files: `001_create_dimensions.sql`, `002_create_facts.sql`, `003_create_views.sql`, `004_create_indexes.sql`
- Proper statement parsing and execution
- PostgreSQL-specific syntax handling

### Database Teardown
- Successfully dropped 8 objects:
  - 3 views: `vw_daily_performance`, `vw_latest_stock_prices`, `vw_stock_rankings`
  - 5 tables: `dim_currency`, `dim_date`, `dim_stocks`, `fact_currency_rates`, `fact_stock_prices`
- Proper CASCADE handling
- Clean database state verification

### Smart Initialization
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

## SQL File Organization

### Consolidated Structure: `dags/sql/`
All SQL files are organized under `dags/sql/` for unified access by Airflow DAGs:

#### DDL (Data Definition Language) - `dags/sql/ddl/`
```
001_create_dimensions.sql    # Database dimension tables
002_create_facts.sql         # Database fact tables  
003_create_views.sql         # Database views
004_create_indexes.sql       # Database indexes
```

#### ETL (Extract, Transform, Load) - `dags/sql/etl/`
```
clean_transform_data.sql                      # Data cleaning and transformation
cleanup_old_data.sql                          # Data cleanup procedures
daily_transforms.sql                          # Daily data transformations
data_quality_checks.sql                       # Data quality validation
load_currency_dimension.sql                   # Currency dimension loading
load_date_dimension.sql                       # Date dimension loading
load_dimensions.sql                           # General dimension loading
load_raw_exchange_data_to_postgres.sql        # Raw exchange data loading
load_raw_stock_data_to_postgres.sql           # Raw stock data loading
load_stock_dimension.sql                      # Stock dimension loading
```

#### Query Templates - `dags/sql/queries/`
```
currency_conversion.sql                       # Currency conversion queries
magnificent_seven_performance_details.sql     # Detailed performance metrics
magnificent_seven_top_performers.sql          # Top performer identification
price_ranges.sql                              # Price range calculations
stock_summary.sql                             # Stock summary reports
top_performers.sql                            # General top performer queries
```

### File Naming Conventions
- **DDL Files**: Numbered for execution order (001_, 002_, etc.)
- **ETL Files**: Prefixed by operation type (load_, transform_, cleanup_)
- **Queries**: Descriptive names with consistent snake_case format
- **All Files**: Use plural forms where applicable for consistency

## Future Enhancements

1. **Migration System**: Database migration management for schema changes
2. **Backup/Restore**: Automated backup and restore capabilities
3. **Data Validation**: Enhanced data integrity checks
4. **Performance Monitoring**: Database performance metrics and optimization
5. **Connection Pooling**: Connection pool management for high-load scenarios
