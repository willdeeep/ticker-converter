"""
Airflow DAG for daily stock data ETL pipeline.

This DAG orchestrates the complete ETL process using SQL operators:
1. Load dimension data (stocks, dates, currencies)
2. Extract and load stock prices from Alpha Vantage API
3. Extract and load exchange rates from exchangerate-api.io
4. Run daily transformations to calculate derived metrics
5. Run data quality checks
6. Clean up old data based to retention policies
"""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

# Add src to path to import our modules
sys.path.append('/Users/willhuntleyclarke/repos/interests/ticker-converter/src')

# pylint: disable=wrong-import-position,import-error
from ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher
from ticker_converter.data_ingestion.currency_fetcher import CurrencyDataFetcher
from ticker_converter.data_ingestion.database_manager import DatabaseManager


class DAGConfig:
    """Configuration for the ETL DAG."""

    # DAG metadata
    DAG_ID = "ticker_converter_daily_etl"
    DESCRIPTION = "Daily ETL pipeline for stock data and currency conversion"
    SCHEDULE = "0 6 * * *"  # Run daily at 6 AM UTC
    TAGS = ["ticker-converter", "etl", "stocks", "currencies"]

    # Default arguments
    DEFAULT_ARGS = {
        "owner": "ticker-converter",
        "depends_on_past": False,
        "start_date": datetime(2024, 1, 1),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    # Database connection
    POSTGRES_CONN_ID = "postgres_default"

    # SQL file paths
    SQL_DIR = "sql/etl"
    DIMENSION_TABLES = [
        "load_stock_dimension.sql",
        "load_date_dimension.sql",
        "load_currency_dimension.sql",
    ]


def extract_stock_prices() -> None:
    """Extract stock prices from Alpha Vantage API.

    This function calls the Alpha Vantage API for each stock
    and inserts into staging tables (raw_stock_data).
    """
    # Initialize components
    db_manager = DatabaseManager()
    fetcher = NYSEDataFetcher()

    try:
        # Fetch data for all Magnificent Seven stocks (last 5 days)
        all_records = fetcher.fetch_and_prepare_all_data(days_back=5)

        if all_records:
            # Insert into raw_stock_data table
            db_manager.insert_stock_data(all_records)
            print(f"Successfully inserted {len(all_records)} stock records")
        else:
            print("No stock data to insert")

    except Exception as e:
        print(f"Error extracting stock prices: {e}")
        raise


def extract_exchange_rates() -> None:
    """Extract exchange rates from exchangerate-api.io.

    This function calls the exchange rate API
    and inserts into staging tables (raw_currency_data).
    """
    # Initialize components
    db_manager = DatabaseManager()
    fetcher = CurrencyDataFetcher()

    try:
        # Fetch USD/GBP exchange rates (last 5 days)
        all_records = fetcher.fetch_and_prepare_fx_data(days_back=5)

        if all_records:
            # Insert into raw_currency_data table
            db_manager.insert_currency_data(all_records)
            print(f"Successfully inserted {len(all_records)} currency records")
        else:
            print("No currency data to insert")

    except Exception as e:
        print(f"Error extracting exchange rates: {e}")
        raise


def create_dimension_load_tasks(dag_instance: DAG) -> list[SQLExecuteQueryOperator]:
    """Create dimension loading tasks.

    Args:
        dag_instance: Airflow DAG instance

    Returns:
        List of dimension loading tasks
    """
    tasks = []

    for sql_file in DAGConfig.DIMENSION_TABLES:
        task_id = sql_file.replace(".sql", "")
        task = SQLExecuteQueryOperator(
            task_id=task_id,
            conn_id=DAGConfig.POSTGRES_CONN_ID,
            sql=f"{DAGConfig.SQL_DIR}/{sql_file}",
            dag=dag_instance,
        )
        tasks.append(task)

    return tasks


def create_extraction_tasks(dag_instance: DAG) -> list[PythonOperator]:
    """Create data extraction tasks.

    Args:
        dag_instance: Airflow DAG instance

    Returns:
        List of extraction tasks
    """
    stock_data_task = PythonOperator(
        task_id="extract_stock_data",
        python_callable=extract_stock_prices,
        dag=dag_instance,
    )

    currency_data_task = PythonOperator(
        task_id="extract_currency_data",
        python_callable=extract_exchange_rates,
        dag=dag_instance,
    )

    return [stock_data_task, currency_data_task]


def create_transformation_tasks(dag_instance: DAG) -> list[SQLExecuteQueryOperator]:
    """Create transformation and quality check tasks.

    Args:
        dag_instance: Airflow DAG instance

    Returns:
        List of transformation tasks
    """
    daily_transforms_task = SQLExecuteQueryOperator(
        task_id="run_daily_transforms",
        conn_id=DAGConfig.POSTGRES_CONN_ID,
        sql=f"{DAGConfig.SQL_DIR}/daily_transforms.sql",
        dag=dag_instance,
    )

    quality_checks_task = SQLExecuteQueryOperator(
        task_id="run_data_quality_checks",
        conn_id=DAGConfig.POSTGRES_CONN_ID,
        sql=f"{DAGConfig.SQL_DIR}/data_quality_checks.sql",
        dag=dag_instance,
    )

    cleanup_task = SQLExecuteQueryOperator(
        task_id="cleanup_old_data",
        conn_id=DAGConfig.POSTGRES_CONN_ID,
        sql=f"{DAGConfig.SQL_DIR}/cleanup_old_data.sql",
        dag=dag_instance,
    )

    return [daily_transforms_task, quality_checks_task, cleanup_task]


# Create the DAG
dag = DAG(  # pylint: disable=unexpected-keyword-arg
    dag_id=DAGConfig.DAG_ID,
    description=DAGConfig.DESCRIPTION,
    default_args=DAGConfig.DEFAULT_ARGS,
    schedule=DAGConfig.SCHEDULE,
    catchup=False,
    max_active_runs=1,
    tags=DAGConfig.TAGS,
)

# Create control tasks
start_task = EmptyOperator(task_id="start_etl", dag=dag)
end_task = EmptyOperator(task_id="end_etl", dag=dag)

# Create task groups
dimension_tasks = create_dimension_load_tasks(dag)
extraction_tasks = create_extraction_tasks(dag)
transformation_tasks = create_transformation_tasks(dag)

# Extract individual tasks for easier reference
# Dimension tasks (3 tasks as defined in DIMENSION_TABLES)
load_stock_dimension = dimension_tasks[0]  # pylint: disable=unused-variable
load_date_dimension = dimension_tasks[1]  # pylint: disable=unused-variable
load_currency_dimension = dimension_tasks[2]  # pylint: disable=unused-variable

# Extraction tasks (2 tasks)
extract_stock_data = extraction_tasks[0]  # pylint: disable=unused-variable
extract_currency_data = extraction_tasks[1]  # pylint: disable=unused-variable

# Transformation tasks (3 tasks)
run_daily_transforms = transformation_tasks[0]
run_data_quality_checks = transformation_tasks[1]
cleanup_old_data = transformation_tasks[2]


# Define task dependencies using a more declarative approach
def setup_dependencies() -> None:
    """Setup task dependencies in a clear, maintainable way."""

    # Start with dimension loading in parallel
    start_task >> dimension_tasks

    # Wait for all dimensions to load before extracting data
    for dim_task in dimension_tasks:
        for extract_task in extraction_tasks:
            dim_task >> extract_task

    # Run transformations after data extraction
    for extract_task in extraction_tasks:
        extract_task >> run_daily_transforms

    # Sequential quality and cleanup operations
    run_daily_transforms >> run_data_quality_checks >> cleanup_old_data

    # End the DAG
    cleanup_old_data >> end_task


# Setup all dependencies
setup_dependencies()
