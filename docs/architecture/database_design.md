# Database Management Architecture Documentation

## Overview

This document details the PostgreSQL database management system implemented following the unified CLI→Orchestrator→Manager→Service architectural pattern.

## Architecture Flow

```
Makefile Commands → CLI (cli_ingestion.py) → Orchestrator → DatabaseManager → PostgreSQL DDL/Operations
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

## Database Schema Management

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

## Future Enhancements

1. **Migration System**: Database migration management for schema changes
2. **Backup/Restore**: Automated backup and restore capabilities
3. **Data Validation**: Enhanced data integrity checks
4. **Performance Monitoring**: Database performance metrics and optimization
5. **Connection Pooling**: Connection pool management for high-load scenarios
