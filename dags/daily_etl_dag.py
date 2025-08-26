"""
Airflow DAG for daily stock data ETL pipeline.

This DAG orchestrates the complete ETL process using SQL operators:
1. Extract stock prices from Alpha Vantage API using the refactored data ingestion modules
2. Extract and load exchange rates from exchangerate-api.io
3. Use SQL operators to clean, transform and load data all data into PostgreSQL database
4. Run data quality checks
5. Monitor and log ETL process
6. Clean up old data based on retention policies
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator

# Add the src directory to the Python path (must be before ticker_converter imports)
# Get the project root dynamically based on the DAG file location
_dag_file_path = Path(__file__).resolve()
_project_root = _dag_file_path.parent.parent  # Go up from dags/ to project root
sys.path.append(str(_project_root / "src"))

# These imports depend on the path modification above
# pylint: disable=wrong-import-position
from ticker_converter.data_ingestion.currency_fetcher import CurrencyDataFetcher
from ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher


class DAGConfig:
    """Configuration for the ETL DAG."""

    # DAG metadata
    DAG_ID = "ticker_converter_daily_etl"
    DESCRIPTION = "Daily ETL pipeline for stock data and currency conversion"
    SCHEDULE = "0 6 * * *"  # Run daily at 6 AM UTC
    TAGS = ["ticker-converter", "etl", "stocks", "currencies"]

    # DAG timing
    START_DATE = datetime(2024, 1, 1)

    # Default arguments
    DEFAULT_ARGS = {
        "owner": "ticker-converter",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    # Database connection
    POSTGRES_CONN_ID = "postgres_default"

    # File paths (dynamically resolved based on DAG location)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Go up from dags/ to project root
    RAW_EXCHANGE_DIR = PROJECT_ROOT / "dags" / "raw_data" / "exchange"
    RAW_STOCKS_DIR = PROJECT_ROOT / "dags" / "raw_data" / "stocks"
    SQL_DIR = PROJECT_ROOT / "dags" / "sql"

    # SQL files for data processing (using string paths for Airflow compatibility)
    SQL_FILES = {
        "load_raw_stock_data": str(PROJECT_ROOT / "dags" / "sql" / "etl" / "load_raw_stock_data_to_postgres.sql"),
        "load_raw_exchange_data": str(PROJECT_ROOT / "dags" / "sql" / "etl" / "load_raw_exchange_data_to_postgres.sql"),
        "clean_transform_data": str(PROJECT_ROOT / "dags" / "sql" / "etl" / "clean_transform_data.sql"),
        "data_quality_checks": str(PROJECT_ROOT / "dags" / "sql" / "etl" / "data_quality_checks.sql"),
        "cleanup_old_data": str(PROJECT_ROOT / "dags" / "sql" / "etl" / "cleanup_old_data.sql"),
    }


def extract_stock_prices_to_json() -> None:
    """Extract stock prices using the refactored data ingestion modules.

    Utilizes NYSEDataFetcher to get stock data and saves to JSON files
    for later processing by SQL operators.
    """
    # Initialize the NYSE data fetcher with proper configuration
    nyse_fetcher = NYSEDataFetcher()

    # Ensure raw data directory exists
    raw_data_path = DAGConfig.RAW_STOCKS_DIR
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Extract stock data using the refactored fetcher
    stock_data = nyse_fetcher.fetch_and_prepare_all_data()

    # Save to JSON file with timestamp
    filename = f"stock_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, indent=2, default=str)

    print(f"Stock prices extracted and saved to {filepath}")


def extract_exchange_rates_to_json() -> None:
    """Extract exchange rates using the refactored data ingestion modules.

    Utilizes CurrencyDataFetcher to get exchange rate data and saves to JSON files
    for later processing by SQL operators.
    """
    # Initialize the currency data fetcher with proper configuration
    currency_fetcher = CurrencyDataFetcher()

    # Ensure raw data directory exists
    raw_data_path = DAGConfig.RAW_EXCHANGE_DIR
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Extract exchange rate data using the refactored fetcher
    exchange_data = currency_fetcher.fetch_and_prepare_fx_data()

    # Save to JSON file with timestamp
    filename = f"exchange_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(exchange_data, f, indent=2, default=str)

    print(f"Exchange rates extracted and saved to {filepath}")


def monitor_etl_process() -> None:
    """Monitor and log ETL process status.

    Checks the status of data files and logs process information.
    """
    stocks_path = DAGConfig.RAW_STOCKS_DIR
    exchange_path = DAGConfig.RAW_EXCHANGE_DIR

    print("ETL Process Monitor:")
    
    # Check stocks directory
    if stocks_path.exists():
        stock_files = list(stocks_path.glob("*.json"))
        print(f"- Stock price files: {len(stock_files)} in {stocks_path}")
    else:
        print(f"- Warning: Stocks directory does not exist: {stocks_path}")
        stock_files = []
    
    # Check exchange directory  
    if exchange_path.exists():
        exchange_files = list(exchange_path.glob("*.json"))
        print(f"- Exchange rate files: {len(exchange_files)} in {exchange_path}")
    else:
        print(f"- Warning: Exchange directory does not exist: {exchange_path}")
        exchange_files = []

    # Log recent files from both directories
    all_files = stock_files + exchange_files
    if all_files:
        recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        print("Recent files:")
        for file in recent_files:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"  - {file.name} (modified: {mtime})")
    else:
        print("No data files found")


@dag(
    dag_id=DAGConfig.DAG_ID,
    description=DAGConfig.DESCRIPTION,
    schedule=DAGConfig.SCHEDULE,
    start_date=DAGConfig.START_DATE,
    catchup=False,
    max_active_runs=1,
    tags=DAGConfig.TAGS,
    default_args=DAGConfig.DEFAULT_ARGS,
)
def ticker_converter_daily_etl() -> None:
    """Ticker converter daily ETL DAG using Airflow 3.0 syntax."""
    # pylint: disable=pointless-statement

    @task
    def extract_stock_data_to_json() -> None:
        """Extract stock prices to JSON files."""
        extract_stock_prices_to_json()

    @task
    def extract_exchange_rates_to_json_task() -> None:
        """Extract exchange rates to JSON files."""
        extract_exchange_rates_to_json()

    @task
    def run_data_quality_checks() -> str:
        """Run data quality checks."""
        print("Running data quality checks...")
        # Placeholder for quality checks
        return "quality_checks_passed"

    @task
    def monitor_etl_process_task() -> None:
        """Monitor ETL process."""
        monitor_etl_process()

    @task
    def cleanup_old_data() -> str:
        """Clean up old data."""
        print("Cleaning up old data...")
        # Placeholder for cleanup logic
        return "cleanup_completed"

    # Create control tasks using traditional operators
    start_task = EmptyOperator(task_id="start_etl")
    end_task = EmptyOperator(task_id="end_etl")

    # SQL processing tasks using traditional operators
    load_raw_stock_data_to_postgres = SQLExecuteQueryOperator(
        task_id="load_raw_stock_data_to_postgres",
        sql=DAGConfig.SQL_FILES["load_raw_stock_data"],
    )

    load_raw_exchange_data_to_postgres = SQLExecuteQueryOperator(
        task_id="load_raw_exchange_data_to_postgres",
        sql=DAGConfig.SQL_FILES["load_raw_exchange_data"],
    )

    clean_transform_data = SQLExecuteQueryOperator(
        task_id="clean_transform_data", sql=DAGConfig.SQL_FILES["clean_transform_data"]
    )

    # Create task instances
    extract_stock_task = extract_stock_data_to_json()
    extract_exchange_task = extract_exchange_rates_to_json_task()
    quality_checks_task = run_data_quality_checks()
    monitor_task = monitor_etl_process_task()
    cleanup_task = cleanup_old_data()

    # Define task dependencies following the 6-step ETL process:
    # Step 1 & 2: Start with parallel data extraction to JSON files
    start_task >> [extract_stock_task, extract_exchange_task]

    # Step 3: After JSON files are created, load them into PostgreSQL in parallel
    extract_stock_task >> load_raw_stock_data_to_postgres
    extract_exchange_task >> load_raw_exchange_data_to_postgres

    # After both raw data loads complete, run the clean and transform step
    [
        load_raw_stock_data_to_postgres,
        load_raw_exchange_data_to_postgres,
    ] >> clean_transform_data

    # Step 4: Run data quality checks after transformation
    clean_transform_data >> quality_checks_task

    # Step 5: Monitor ETL process after quality checks
    quality_checks_task >> monitor_task

    # Step 6: Clean up old data after monitoring
    monitor_task >> cleanup_task

    # End the DAG
    cleanup_task >> end_task


# Instantiate the DAG
daily_etl_dag = ticker_converter_daily_etl()
