# Airflow DAGs for Ticker Converter

This directory contains Airflow DAGs that orchestrate the SQL-first data pipeline for the Ticker Converter application.

## Available DAGs

### 1. Daily ETL Pipeline (`daily_etl_dag.py`)
- **Purpose**: Automated daily extraction, transformation, and loading of stock and currency data
- **Schedule**: Daily at 6:00 AM UTC
- **Features**:
  - Parallel extraction of stock prices and exchange rates
  - SQL-based data processing and transformation
  - Data quality validation
  - Comprehensive logging and monitoring

### 2. Manual Backfill Pipeline (`manual_backfill_dag.py`)
- **Purpose**: On-demand historical data backfill for custom date ranges
- **Schedule**: Manual trigger only (no automatic schedule)
- **Features**:
  - Configurable date ranges via DAG parameters
  - Optional symbol-specific backfills
  - Validation-only mode for testing
  - Comprehensive data validation and reporting
  - Duplicate detection and removal

## SQL-First Architecture

Both DAGs follow a SQL-first approach where:
1. **Python tasks** handle data extraction and file operations
2. **SQL operators** perform all data processing, transformation, and validation
3. **SQL files** in `sql/` subdirectories contain reusable query logic

## Directory Structure

```
dags/
├── README.md                    # This file
├── daily_etl_dag.py            # Daily automated pipeline
├── manual_backfill_dag.py      # Manual backfill operations
├── sql/                        # SQL query files
│   ├── etl/                    # Daily ETL SQL operations
│   └── backfill/               # Backfill-specific SQL operations
└── raw_data/                   # Temporary data storage
    ├── exchange/               # Daily pipeline data files
    └── backfill/               # Backfill operation data files
```

## Running the Manual Backfill DAG

The manual backfill DAG can be triggered with custom parameters:

### Required Parameters
- `start_date`: Start date for backfill (YYYY-MM-DD format)
- `end_date`: End date for backfill (YYYY-MM-DD format)

### Optional Parameters
- `symbols`: Comma-separated list of symbols (empty for all symbols)
- `validate_only`: Set to `true` to only validate parameters without extracting data

### Example Usage

1. **Full backfill for a date range**:
   ```json
   {
     "start_date": "2024-01-01",
     "end_date": "2024-01-31",
     "symbols": "",
     "validate_only": false
   }
   ```

2. **Symbol-specific backfill**:
   ```json
   {
     "start_date": "2024-01-01", 
     "end_date": "2024-01-07",
     "symbols": "AAPL,MSFT,GOOGL",
     "validate_only": false
   }
   ```

3. **Validation only (no data extraction)**:
   ```json
   {
     "start_date": "2024-01-01",
     "end_date": "2024-01-31", 
     "symbols": "",
     "validate_only": true
   }
   ```

## Migration from CLI Backfill

Previously, backfill operations were handled via a CLI command. This approach has been migrated to Airflow DAGs for better:

- **Orchestration**: Complex workflows with proper task dependencies
- **Monitoring**: Built-in Airflow UI for tracking progress
- **Scheduling**: Flexible parameter-based execution
- **SQL-First**: Consistent with overall architecture
- **Scalability**: Better resource management and parallel processing

The CLI now focuses on:
- Selective data refresh operations
- Pipeline validation
- System inspection
- Development tools

For historical data operations, always use the `manual_backfill_dag.py` DAG instead of CLI commands.
