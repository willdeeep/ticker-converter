# Airflow DAGs for Ticker Converter

This directory contains Apache Airflow 3.0.4 DAGs that orchestrate the modern data pipeline for the Ticker Converter application using the latest @dag and @task decorators.

## Available DAGs

### 1. Daily ETL Pipeline (`daily_etl_dag.py`)
- **Purpose**: Automated daily extraction, transformation, and loading of stock and currency data
- **Schedule**: `@daily` (runs daily using Airflow 3.0 schedule patterns)
- **Features**:
  - TaskFlow-based implementation with @task decorators
  - Smart branching logic for initial runs vs. incremental updates
  - Parallel data processing with comprehensive error handling
  - SQL-based data transformation and validation
  - Graceful failure handling with trigger_rule configuration

### 2. Test ETL Pipeline (`test_etl_dag.py`)
- **Purpose**: Development and testing validation of ETL logic
- **Schedule**: Manual trigger only (no automatic schedule)
- **Features**:
  - Simplified DAG structure for testing workflows
  - Validation of core ETL components
  - Safe testing environment with isolated data paths
  - Development workflow validation

## Modern Airflow 3.0.4 Architecture

The DAGs leverage Airflow 3.0.4's latest features:

### TaskFlow API (@task decorators)
```python
@task(task_id="assess_latest")
def assess_latest_task() -> dict[str, Any]:
    return assess_latest_records()

@task.branch(task_id="decide_collect")
def decide_collect(assess: dict[str, Any]) -> str:
    # Smart branching logic
    return "collect_api" if is_initial_run else "skip_collection"
```

### Smart Dependency Management
- **trigger_rule="none_failed_min_one_success"**: Join point after branching
- **trigger_rule="none_failed"**: Final task coordination
- Outdated pendulum datetime handling removed as it is only advised for Airflow 2.x and we are using Airflow 3.x

### Helper Module Integration
Both DAGs follow a clean architecture pattern:
1. **DAG files**: Thin orchestration layer with @task decorators
2. **Helper modules** (`dags/helpers/`): Business logic implementation
3. **SQL operations** (`dags/sql/`): Data processing and validation queries
4. **Core library** (`src/ticker_converter/`): Shared utilities and models

## Directory Structure

```
dags/
├── README.md                    # This file
├── daily_etl_dag.py            # Daily automated pipeline (Airflow 3.0.4)
├── test_etl_dag.py             # Testing and validation DAG
├── helpers/                    # Business logic modules
│   ├── __init__.py
│   ├── assess_records.py       # Record assessment logic
│   ├── collect_api_data.py     # API data collection
│   └── load_raw_to_db.py       # Database loading operations
├── sql/                        # SQL query files and DDL
│   ├── ddl/                    # Data definition language (schema)
│   │   └── 001_create_dimensions.sql
│   ├── etl/                    # ETL transformation queries
│   └── queries/                # Reusable query templates
└── raw_data/                   # Temporary data storage
    ├── stocks/                 # Stock price data files
    └── exchange/               # Exchange rate data files
```

## Quality and Testing Integration

### Code Quality Standards
- **Pylint 10.00/10**: All DAG files maintain perfect quality scores
- **Strategic Suppressions**: Airflow 3.0 compatibility handled gracefully
- **Import Order**: Proper Airflow import patterns for 3.0.4
- **Type Safety**: Comprehensive type annotations throughout

### Testing Integration
- **make quality**: Full 7-step validation including DAG syntax
- **Airflow DAG validation**: Built-in syntax and structure checks
- **Import validation**: Ensures all dependencies are properly resolved

## Running DAGs

### Daily ETL Pipeline
The daily ETL pipeline runs automatically but can be triggered manually:

```bash
# Start Airflow services
make airflow

# Access Airflow Web UI
# URL: http://localhost:8080
# Username: admin
# Password: [from .env AIRFLOW_ADMIN_PASSWORD]

# Trigger DAG manually via CLI
make run DAG_NAME=daily_etl_pipeline
```

### Development and Testing

```bash
# Validate DAG syntax
python dags/daily_etl_dag.py

# Test DAG structure
airflow dags list-import-errors

# Run specific tasks for testing
airflow tasks test daily_etl_pipeline assess_latest 2025-01-01
```

## Integration with Project Workflow

### Makefile Integration
- **make airflow**: Start Airflow with proper environment setup
- **make run**: Execute pipeline with optional DAG_NAME parameter
- **make quality**: Validate DAG code quality as part of 7-step pipeline

### Environment Configuration
DAGs automatically load configuration from `.env` file:
- Database connections (PostgreSQL)
- API credentials (Alpha Vantage)
- Airflow-specific settings
- File system paths and directories

### Error Handling and Monitoring
- **Graceful failures**: DAGs handle API rate limits and temporary outages
- **Comprehensive logging**: Detailed task output for debugging
- **Email notifications**: Configurable alerts for failures (production)
- **Retry logic**: Automatic retry with exponential backoff
