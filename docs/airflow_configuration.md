# Airflow SQL Operators Configuration Guide

## Overview

This guide provides comprehensive configuration instructions for setting up Apache Airflow with SQL operators for the ticker-converter project. The configuration focuses on PostgreSQL integration and SQL-first ETL operations.

## Prerequisites

### System Requirements
- Apache Airflow 2.5+
- PostgreSQL 12+
- Python 3.9+
- Required Airflow providers

### Required Airflow Providers
```bash
# Install PostgreSQL provider
pip install apache-airflow-providers-postgres

# Install additional providers for monitoring
pip install apache-airflow-providers-email
pip install apache-airflow-providers-slack  # Optional for alerts
```

## Airflow Configuration

### 1. Core Configuration (`airflow.cfg`)

#### Database Configuration
```ini
[database]
# Use PostgreSQL for Airflow metadata (recommended for production)
sql_alchemy_conn = postgresql://airflow_user:airflow_password@localhost:5432/airflow_db

# Connection pool settings
sql_alchemy_pool_size = 5
sql_alchemy_max_overflow = 10
sql_alchemy_pool_pre_ping = True
sql_alchemy_pool_recycle = 3600

[core]
# DAGs configuration
dags_folder = /opt/airflow/dags
base_log_folder = /opt/airflow/logs
remote_logging = False
log_level = INFO

# Executor configuration (use LocalExecutor for single machine, CeleryExecutor for distributed)
executor = LocalExecutor

# Security
fernet_key = your_fernet_key_here  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# DAG processing
dagbag_import_timeout = 30
dag_file_processor_timeout = 50
```

#### Scheduler Configuration
```ini
[scheduler]
# Job heartbeat and processing intervals
job_heartbeat_sec = 5
scheduler_heartbeat_sec = 5
num_runs = -1
processor_poll_interval = 1

# DAG processing
max_dagruns_to_create_per_loop = 10
max_dagruns_per_dag_for_dag_processor = 2

# Task instance limits
max_tis_per_query = 512
```

#### Webserver Configuration
```ini
[webserver]
# Web server settings
web_server_host = 0.0.0.0
web_server_port = 8080
web_server_worker_timeout = 120

# Authentication (for production)
authenticate = True
auth_backend = airflow.auth.backends.password_auth

# RBAC
rbac = True
```

### 2. Environment Variables

#### Create `.env` file for Airflow:
```bash
# Database connections
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow_user:airflow_password@localhost:5432/airflow_db

# Application database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticker_converter
POSTGRES_USER=ticker_user
POSTGRES_PASSWORD=your_secure_password

# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CURRENCY_API_KEY=your_currency_api_key

# Airflow specific
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
```

## Connection Configuration

### 1. PostgreSQL Connection Setup

#### Via Airflow CLI
```bash
# Add the main database connection
airflow connections add postgres_default \
    --conn-type postgres \
    --conn-host localhost \
    --conn-schema ticker_converter \
    --conn-login ticker_user \
    --conn-password your_secure_password \
    --conn-port 5432 \
    --conn-extra '{"sslmode": "prefer", "connect_timeout": "10"}'

# Test the connection
airflow connections test postgres_default
```

#### Via Airflow Web UI
```
Connection Id: postgres_default
Connection Type: PostgreSQL
Host: localhost
Schema: ticker_converter
Login: ticker_user
Password: your_secure_password
Port: 5432
Extra: {"sslmode": "prefer", "connect_timeout": "10"}
```

#### Via Python (for automation)
```python
from airflow.models import Connection
from airflow import settings

def create_postgres_connection():
    """Create PostgreSQL connection programmatically"""
    new_conn = Connection(
        conn_id='postgres_default',
        conn_type='postgres',
        host='localhost',
        schema='ticker_converter',
        login='ticker_user',
        password='your_secure_password',
        port=5432,
        extra='{"sslmode": "prefer", "connect_timeout": "10"}'
    )

    session = settings.Session()
    # Delete if exists
    session.query(Connection).filter(Connection.conn_id == 'postgres_default').delete()
    session.add(new_conn)
    session.commit()
    session.close()
```

### 2. Variables Configuration

#### Set Airflow Variables via CLI
```bash
# Database configuration
airflow variables set postgres_host "localhost"
airflow variables set postgres_port "5432"
airflow variables set postgres_db "ticker_converter"
airflow variables set postgres_user "ticker_user"
airflow variables set postgres_password "your_secure_password"

# API keys
airflow variables set alpha_vantage_api_key "your_alpha_vantage_key"
airflow variables set currency_api_key "your_currency_api_key"

# ETL configuration
airflow variables set magnificent_seven_symbols '["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]'
airflow variables set data_retention_days "365"
airflow variables set staging_retention_days "7"
```

#### Via JSON file (bulk import)
```bash
# Create variables.json
cat > variables.json << EOF
{
    "postgres_host": "localhost",
    "postgres_port": "5432",
    "postgres_db": "ticker_converter",
    "postgres_user": "ticker_user",
    "postgres_password": "your_secure_password",
    "alpha_vantage_api_key": "your_alpha_vantage_key",
    "currency_api_key": "your_currency_api_key",
    "magnificent_seven_symbols": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"],
    "data_retention_days": "365",
    "staging_retention_days": "7"
}
EOF

# Import variables
airflow variables import variables.json
```

## SQL File Organization

### Directory Structure
```bash
# Create SQL directory structure
mkdir -p /opt/airflow/sql/{ddl,etl,queries,dml}

# SQL files structure
/opt/airflow/sql/
├── ddl/                          # Data Definition Language
│   ├── 001_create_dimensions.sql
│   ├── 002_create_facts.sql
│   ├── 003_create_views.sql
│   ├── 004_create_indexes.sql
│   └── 005_create_staging.sql
├── etl/                          # ETL SQL Scripts
│   ├── load_dimensions.sql
│   ├── daily_transform.sql
│   ├── data_quality_checks.sql
│   └── cleanup_staging.sql
├── dml/                          # Data Manipulation
│   ├── backfill_dimensions.sql
│   └── data_corrections.sql
└── queries/                      # API Query Templates
    ├── top_performers.sql
    ├── price_ranges.sql
    └── currency_conversion.sql
```

### SQL File Access Configuration
```python
# In Airflow DAG - Configure SQL path
import os
from pathlib import Path

# SQL files base path
SQL_PATH = Path(os.getenv('AIRFLOW_HOME', '/opt/airflow')) / 'sql'

def get_sql_file_path(category: str, filename: str) -> str:
    """Get full path to SQL file"""
    return str(SQL_PATH / category / filename)

# Usage in PostgresOperator
transform_task = PostgresOperator(
    task_id='transform_to_warehouse',
    postgres_conn_id='postgres_default',
    sql=get_sql_file_path('etl', 'daily_transform.sql'),
    dag=dag
)
```

## PostgresOperator Configuration

### 1. Basic PostgresOperator Usage
```python
from airflow.providers.postgres.operators.postgres import PostgresOperator

# Simple SQL execution
simple_task = PostgresOperator(
    task_id='simple_sql_task',
    postgres_conn_id='postgres_default',
    sql="SELECT COUNT(*) FROM dim_stocks;",
    dag=dag
)

# SQL from external file
file_task = PostgresOperator(
    task_id='load_dimensions',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_dimensions.sql',
    dag=dag
)

# SQL with parameters
parameterized_task = PostgresOperator(
    task_id='cleanup_old_data',
    postgres_conn_id='postgres_default',
    sql="""
        DELETE FROM staging_stock_data 
        WHERE created_at < NOW() - INTERVAL '{{ var.value.staging_retention_days }} days'
    """,
    dag=dag
)
```

### 2. Advanced PostgresOperator Configuration
```python
# Task with custom configuration
advanced_task = PostgresOperator(
    task_id='advanced_transform',
    postgres_conn_id='postgres_default',
    sql='sql/etl/daily_transform.sql',
    parameters={
        'execution_date': '{{ ds }}',
        'batch_size': 1000
    },
    autocommit=True,  # Auto-commit transactions
    split_statements=True,  # Split multiple statements
    dag=dag,
    # Error handling
    trigger_rule='all_success',
    retries=2,
    retry_delay=timedelta(minutes=5),
    # Resource configuration
    pool='postgres_pool',  # Resource pool
    priority_weight=10,
    # Monitoring
    on_failure_callback=lambda context: send_failure_alert(context),
    on_success_callback=lambda context: log_success(context)
)
```

### 3. PostgresOperator with XCom
```python
def get_latest_date(**context):
    """Get latest data date from XCom"""
    return context['ti'].xcom_pull(task_ids='get_max_date')

get_max_date = PostgresOperator(
    task_id='get_max_date',
    postgres_conn_id='postgres_default',
    sql="""
        SELECT MAX(date) as max_date 
        FROM dim_dates 
        WHERE is_trading_day = TRUE
    """,
    do_xcom_push=True,  # Push result to XCom
    dag=dag
)

use_max_date = PostgresOperator(
    task_id='process_latest_data',
    postgres_conn_id='postgres_default',
    sql="""
        SELECT * FROM fact_stock_prices p
        JOIN dim_dates d ON p.date_id = d.date_id
        WHERE d.date = '{{ ti.xcom_pull(task_ids='get_max_date') }}'
    """,
    dag=dag
)

get_max_date >> use_max_date
```

## Error Handling and Monitoring

### 1. Connection Pool Configuration
```python
# PostgreSQL hook with custom pool settings
from airflow.providers.postgres.hooks.postgres import PostgresHook

def get_postgres_hook():
    """Get PostgreSQL hook with custom configuration"""
    return PostgresHook(
        postgres_conn_id='postgres_default',
        schema='ticker_converter'
    )

# Custom task with connection handling
def execute_with_retry(**context):
    """Execute SQL with connection retry logic"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            hook = get_postgres_hook()
            result = hook.run(sql="SELECT 1")
            return result
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            time.sleep(5 * retry_count)  # Exponential backoff
```

### 2. SQL Transaction Management
```python
# PostgresOperator with transaction control
transaction_task = PostgresOperator(
    task_id='atomic_operation',
    postgres_conn_id='postgres_default',
    sql="""
        BEGIN;
        
        -- Multiple operations in single transaction
        INSERT INTO fact_stock_prices (...) VALUES (...);
        UPDATE dim_stocks SET last_updated = NOW() WHERE symbol = 'AAPL';
        
        -- Conditional logic
        DO $$
        BEGIN
            IF (SELECT COUNT(*) FROM fact_stock_prices WHERE date_id = 
                (SELECT date_id FROM dim_dates WHERE date = CURRENT_DATE)) = 0 
            THEN
                RAISE EXCEPTION 'No data loaded for today';
            END IF;
        END $$;
        
        COMMIT;
    """,
    autocommit=False,  # Manual transaction control
    dag=dag
)
```

### 3. Monitoring and Alerting
```python
# Custom monitoring task
def monitor_data_quality(**context):
    """Monitor data quality and send alerts"""
    hook = PostgresHook(postgres_conn_id='postgres_default')

    # Check data freshness
    result = hook.get_first("""
        SELECT 
            COUNT(*) as record_count,
            MAX(d.date) as latest_date,
            (CURRENT_DATE - MAX(d.date)) as days_old
        FROM fact_stock_prices p
        JOIN dim_dates d ON p.date_id = d.date_id
    """)

    record_count, latest_date, days_old = result

    # Alert conditions
    if days_old > 2:
        send_alert(f"Data is {days_old} days old - last update: {latest_date}")

    if record_count == 0:
        send_critical_alert("No stock price data found in database")

    # Log metrics
    context['ti'].xcom_push(key='data_quality_metrics', value={
        'record_count': record_count,
        'latest_date': str(latest_date),
        'days_old': days_old
    })

monitoring_task = PythonOperator(
    task_id='monitor_data_quality',
    python_callable=monitor_data_quality,
    dag=dag
)
```

## Performance Optimization

### 1. Connection Pool Configuration
```ini
# In airflow.cfg
[database]
sql_alchemy_pool_size = 10
sql_alchemy_max_overflow = 20
sql_alchemy_pool_pre_ping = True
sql_alchemy_pool_recycle = 3600

# Custom pool for PostgreSQL tasks
[pool]
# Create pools via Airflow UI or CLI
# Pool Name: postgres_pool
# Pool Slots: 5
# Pool Description: PostgreSQL operations pool
```

### 2. Resource Management
```python
# Pool configuration via CLI
# airflow pools set postgres_pool 5 "PostgreSQL operations pool"

# Task with resource pool
optimized_task = PostgresOperator(
    task_id='optimized_operation',
    postgres_conn_id='postgres_default',
    sql='sql/etl/large_transform.sql',
    pool='postgres_pool',  # Limit concurrent PostgreSQL operations
    priority_weight=10,    # Higher priority
    dag=dag
)
```

### 3. SQL Query Optimization
```sql
-- Optimized SQL for large datasets
-- File: sql/etl/optimized_transform.sql

-- Use EXPLAIN ANALYZE for query optimization
/*
EXPLAIN ANALYZE
SELECT ... FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
WHERE ...;
*/

-- Batch processing for large operations
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
WHERE st.date = '{{ ds }}'
  AND st.created_at >= '{{ ds }} 00:00:00'
  AND st.created_at < '{{ next_ds }} 00:00:00'
ON CONFLICT (date_id, stock_id) DO UPDATE SET
    open_usd = EXCLUDED.open_usd,
    high_usd = EXCLUDED.high_usd,
    low_usd = EXCLUDED.low_usd,
    close_usd = EXCLUDED.close_usd,
    volume = EXCLUDED.volume;

-- Vacuum and analyze after large operations
VACUUM ANALYZE fact_stock_prices;
```

## Security Configuration

### 1. Connection Security
```python
# Use Airflow's built-in encryption for sensitive data
from airflow.models import Variable
from cryptography.fernet import Fernet

# Store sensitive variables encrypted
def set_encrypted_variable(key: str, value: str):
    """Set encrypted variable in Airflow"""
    Variable.set(key, value, serialize_json=False)

# Usage in DAG
postgres_password = Variable.get("postgres_password")  # Automatically decrypted
api_key = Variable.get("alpha_vantage_api_key")
```

### 2. SQL Injection Prevention
```python
# Safe parameter passing
safe_task = PostgresOperator(
    task_id='safe_parameterized_query',
    postgres_conn_id='postgres_default',
    sql="""
        SELECT * FROM fact_stock_prices p
        JOIN dim_stocks s ON p.stock_id = s.stock_id
        WHERE s.symbol = %(symbol)s
          AND p.date_id = (
              SELECT date_id FROM dim_dates 
              WHERE date = %(target_date)s
          )
    """,
    parameters={
        'symbol': '{{ var.value.target_symbol }}',
        'target_date': '{{ ds }}'
    },
    dag=dag
)
```

### 3. Access Control
```bash
# PostgreSQL user permissions (run as superuser)
-- Create dedicated Airflow user with limited permissions
CREATE USER airflow_etl WITH PASSWORD 'secure_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE ticker_converter TO airflow_etl;
GRANT USAGE ON SCHEMA public TO airflow_etl;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO airflow_etl;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO airflow_etl;

-- Grant execute on stored procedures if needed
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO airflow_etl;
```

## Deployment Checklist

### 1. Pre-deployment Validation
```bash
# Test PostgreSQL connection
psql "postgresql://ticker_user:password@localhost:5432/ticker_converter" -c "SELECT 1"

# Validate SQL files syntax
for sql_file in sql/**/*.sql; do
    echo "Checking $sql_file"
    psql "postgresql://ticker_user:password@localhost:5432/ticker_converter" -f "$sql_file" --single-transaction --set ON_ERROR_STOP=on --dry-run
done

# Test Airflow configuration
airflow config list
airflow connections test postgres_default
```

### 2. Deployment Steps
```bash
# 1. Deploy SQL schema
psql $DATABASE_URL -f sql/ddl/001_create_dimensions.sql
psql $DATABASE_URL -f sql/ddl/002_create_facts.sql
psql $DATABASE_URL -f sql/ddl/003_create_views.sql
psql $DATABASE_URL -f sql/ddl/004_create_indexes.sql
psql $DATABASE_URL -f sql/ddl/005_create_staging.sql

# 2. Copy DAG and SQL files
cp dags/nyse_stock_etl.py $AIRFLOW_HOME/dags/
cp -r sql/ $AIRFLOW_HOME/

# 3. Set up connections and variables
airflow connections add postgres_default --conn-type postgres --conn-host localhost --conn-schema ticker_converter --conn-login ticker_user --conn-password $POSTGRES_PASSWORD --conn-port 5432

# 4. Import variables
airflow variables import variables.json

# 5. Test DAG
airflow dags test nyse_stock_etl 2024-01-01

# 6. Enable DAG
airflow dags unpause nyse_stock_etl
```

### 3. Post-deployment Monitoring
```bash
# Monitor DAG runs
airflow dags state nyse_stock_etl 2024-01-01

# Check task logs
airflow tasks logs nyse_stock_etl transform_to_warehouse 2024-01-01

# Monitor database performance
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE datname = 'ticker_converter'"
```

This comprehensive configuration ensures a robust, secure, and performant Airflow setup optimized for SQL-centric ETL operations with PostgreSQL.
