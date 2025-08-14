"""
Airflow DAG for daily stock data ETL pipeline.

This DAG orchestrates the complete ETL process using SQL operators:
1. Extract stock prices from Alpha Vantage API and load into Json storage in raw_data/exchange
2. Extract and load exchange rates from exchangerate-api.io and load in raw Json format in raw_data/exchange
3. Use SQL operators to clean, transform and load data all data into PostgreSQL database
4. Run data quality checks
5. Monitor and log ETL process
6. Clean up old data based on retention policies
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator


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

    # File paths
    RAW_DATA_DIR = "raw_data/exchange"
    SQL_DIR = "sql/etl"

    # SQL files for data processing
    SQL_FILES = {
        "load_raw_stock_data": "load_raw_stock_data_to_postgres.sql",
        "load_raw_exchange_data": "load_raw_exchange_data_to_postgres.sql",
        "clean_transform_data": "clean_transform_data.sql",
        "data_quality_checks": "data_quality_checks.sql",
        "cleanup_old_data": "cleanup_old_data.sql",
    }


def extract_stock_prices_to_json() -> None:
    """Extract stock prices from Alpha Vantage API and save to JSON files.

    Fetches stock data from Alpha Vantage API and saves raw JSON responses
    to raw_data/exchange directory for later processing.
    """
    # pylint: disable=fixme
    # TODO: Implement Alpha Vantage API integration

    # Ensure raw data directory exists
    raw_data_path = Path(DAGConfig.RAW_DATA_DIR)
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Placeholder: Create sample JSON file structure
    sample_data = {
        "Meta Data": {
            "1. Information": "Daily Prices and Volumes",
            "2. Symbol": "SAMPLE",
            "3. Last Refreshed": datetime.now().isoformat(),
            "4. Output Size": "Compact",
        },
        "Time Series (Daily)": {
            datetime.now().strftime("%Y-%m-%d"): {
                "1. open": "100.00",
                "2. high": "105.00",
                "3. low": "99.00",
                "4. close": "103.50",
                "5. volume": "1000000",
            }
        },
    }

    # Save to JSON file with timestamp
    filename = f"stock_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)

    print(f"Stock prices saved to {filepath}")


def extract_exchange_rates_to_json() -> None:
    """Extract exchange rates from exchangerate-api.io and save to JSON files.

    Fetches exchange rate data and saves raw JSON responses
    to raw_data/exchange directory for later processing.
    """
    # pylint: disable=fixme
    # TODO: Implement exchange rate API integration

    # Ensure raw data directory exists
    raw_data_path = Path(DAGConfig.RAW_DATA_DIR)
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Placeholder: Create sample JSON file structure
    sample_data = {
        "result": "success",
        "provider": "https://www.exchangerate-api.com",
        "documentation": "https://www.exchangerate-api.com/docs/free",
        "terms_of_use": "https://www.exchangerate-api.com/terms",
        "time_last_update_unix": int(datetime.now().timestamp()),
        "time_last_update_utc": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "time_next_update_unix": int((datetime.now() + timedelta(days=1)).timestamp()),
        "time_next_update_utc": (datetime.now() + timedelta(days=1)).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        ),
        "base_code": "USD",
        "conversion_rates": {
            "USD": 1,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.5,
            "CAD": 1.25,
        },
    }

    # Save to JSON file with timestamp
    filename = f"exchange_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)

    print(f"Exchange rates saved to {filepath}")


def monitor_etl_process() -> None:
    """Monitor and log ETL process status.

    Checks the status of data files and logs process information.
    """
    raw_data_path = Path(DAGConfig.RAW_DATA_DIR)

    if not raw_data_path.exists():
        print("Warning: Raw data directory does not exist")
        return

    # Count files in raw data directory
    json_files = list(raw_data_path.glob("*.json"))
    stock_files = [f for f in json_files if f.name.startswith("stock_prices_")]
    exchange_files = [f for f in json_files if f.name.startswith("exchange_rates_")]

    print("ETL Process Monitor:")
    print(f"- Total JSON files: {len(json_files)}")
    print(f"- Stock price files: {len(stock_files)}")
    print(f"- Exchange rate files: {len(exchange_files)}")
    print(f"- Raw data directory: {raw_data_path}")

    # Log recent files
    if json_files:
        recent_files = sorted(
            json_files, key=lambda x: x.stat().st_mtime, reverse=True
        )[:5]
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
def ticker_converter_daily_etl():
    """Ticker converter daily ETL DAG using Airflow 3.0 syntax."""
    # pylint: disable=pointless-statement

    @task
    def extract_stock_data_to_json():
        """Extract stock prices to JSON files."""
        extract_stock_prices_to_json()

    @task
    def extract_exchange_rates_to_json_task():
        """Extract exchange rates to JSON files."""
        extract_exchange_rates_to_json()

    @task
    def run_data_quality_checks():
        """Run data quality checks."""
        print("Running data quality checks...")
        # Placeholder for quality checks
        return "quality_checks_passed"

    @task
    def monitor_etl_process_task():
        """Monitor ETL process."""
        monitor_etl_process()

    @task
    def cleanup_old_data():
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
    start_task >> [
        extract_stock_task,
        extract_exchange_task,
    ]  # pylint: disable=pointless-statement

    # Step 3: After JSON files are created, load them into PostgreSQL in parallel
    [
        extract_stock_task,
        extract_exchange_task,
    ] >> [  # pylint: disable=pointless-statement
        load_raw_stock_data_to_postgres,
        load_raw_exchange_data_to_postgres,
    ]

    # After both raw data loads complete, run the clean and transform step
    [  # pylint: disable=pointless-statement
        load_raw_stock_data_to_postgres,
        load_raw_exchange_data_to_postgres,
    ] >> clean_transform_data

    # Step 4: Run data quality checks after transformation
    clean_transform_data >> quality_checks_task  # pylint: disable=pointless-statement

    # Step 5: Monitor ETL process after quality checks
    quality_checks_task >> monitor_task  # pylint: disable=pointless-statement

    # Step 6: Clean up old data after monitoring
    monitor_task >> cleanup_task  # pylint: disable=pointless-statement

    # End the DAG
    cleanup_task >> end_task  # pylint: disable=pointless-statement


# Instantiate the DAG
daily_etl_dag = ticker_converter_daily_etl()
