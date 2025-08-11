"""
Airflow DAG for daily stock data ETL pipeline.

This DAG orchestrates the complete ETL process using SQL operators:
1. Load dimension data (stocks, dates, currencies)
2. Extract and load stock prices from Alpha Vantage API
3. Extract and load exchange rates from exchangerate-api.io
4. Run daily transformations to calculate derived metrics
5. Run data quality checks
6. Clean up old data based on retention policies
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator


# Default arguments for the DAG
default_args = {
    'owner': 'ticker-converter',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'ticker_converter_daily_etl',
    default_args=default_args,
    description='Daily ETL pipeline for stock data and currency conversion',
    schedule_interval='0 6 * * *',  # Run daily at 6 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['ticker-converter', 'etl', 'stocks', 'currencies'],
)

# Start task
start_task = DummyOperator(
    task_id='start_etl',
    dag=dag,
)

# Load dimension data
load_stock_dimension = PostgresOperator(
    task_id='load_stock_dimension',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_stock_dimension.sql',
    dag=dag,
)

load_date_dimension = PostgresOperator(
    task_id='load_date_dimension',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_date_dimension.sql',
    dag=dag,
)

load_currency_dimension = PostgresOperator(
    task_id='load_currency_dimension',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_currency_dimension.sql',
    dag=dag,
)

# Data extraction tasks (these would be Python operators calling APIs)
def extract_stock_prices():
    """Extract stock prices from Alpha Vantage API."""
    # Implementation would call Alpha Vantage API for each stock
    # and insert into staging tables or directly into fact_stock_prices
    pass

def extract_exchange_rates():
    """Extract exchange rates from exchangerate-api.io."""
    # Implementation would call exchange rate API
    # and insert into fact_exchange_rates
    pass

extract_stock_data = PythonOperator(
    task_id='extract_stock_data',
    python_callable=extract_stock_prices,
    dag=dag,
)

extract_currency_data = PythonOperator(
    task_id='extract_currency_data',
    python_callable=extract_exchange_rates,
    dag=dag,
)

# Daily transformations
run_daily_transforms = PostgresOperator(
    task_id='run_daily_transforms',
    postgres_conn_id='postgres_default',
    sql='sql/etl/daily_transforms.sql',
    dag=dag,
)

# Data quality checks
run_data_quality_checks = PostgresOperator(
    task_id='run_data_quality_checks',
    postgres_conn_id='postgres_default',
    sql='sql/etl/data_quality_checks.sql',
    dag=dag,
)

# Cleanup old data
cleanup_old_data = PostgresOperator(
    task_id='cleanup_old_data',
    postgres_conn_id='postgres_default',
    sql='sql/etl/cleanup_old_data.sql',
    dag=dag,
)

# End task
end_task = DummyOperator(
    task_id='end_etl',
    dag=dag,
)

# Define task dependencies
start_task >> [load_stock_dimension, load_date_dimension, load_currency_dimension]

[load_stock_dimension, load_date_dimension, load_currency_dimension] >> [extract_stock_data, extract_currency_data]

[extract_stock_data, extract_currency_data] >> run_daily_transforms

run_daily_transforms >> run_data_quality_checks

run_data_quality_checks >> cleanup_old_data

cleanup_old_data >> end_task
