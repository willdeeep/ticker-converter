"""
Simple daily ETL DAG for stock data pipeline.

Three clear steps:
1. Assess latest records in DB and JSON
2. Collect API records - write to JSON raw_data
3. Collect raw_data and write to DB
"""

from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.providers.standard.operators.python import PythonOperator

# Import task functions
from py.assess_records import assess_latest_records
from py.collect_api_data import collect_api_data
from py.load_json_to_db import load_json_to_db


@dag(
    dag_id="daily_etl_dag",
    description="Simple daily stock data ETL pipeline",
    schedule="0 9 * * 1-5",  # 9 AM on weekdays
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ticker-converter", "etl"],
    default_args={
        "owner": "ticker-converter",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
)
def daily_etl_dag():
    """Simple daily ETL DAG."""

    # Step 1: Assess latest records
    step1 = PythonOperator(
        task_id="assess_latest_records",
        python_callable=assess_latest_records,
    )

    # Step 2: Collect API data
    step2 = PythonOperator(
        task_id="collect_api_data",
        python_callable=collect_api_data,
    )

    # Step 3: Load to database
    step3 = PythonOperator(
        task_id="load_json_to_db",
        python_callable=load_json_to_db,
    )

    # Simple linear workflow
    step1 >> step2 >> step3


# Instantiate the DAG
etl_dag = daily_etl_dag()

import glob
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
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
    DAG_ID = "daily_etl_dag"
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

    # SQL files for data processing (using relative paths for Airflow template compatibility)
    SQL_FILES = {
        "load_raw_stock_data": "sql/etl/load_raw_stock_data_to_postgres.sql",
        "load_raw_exchange_data": "sql/etl/load_raw_exchange_data_to_postgres.sql",
        "clean_transform_data": "sql/etl/clean_transform_data.sql",
        "data_quality_checks": "sql/etl/data_quality_checks.sql",
        "cleanup_old_data": "sql/etl/cleanup_old_data.sql",
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
    def load_stock_json_to_postgres() -> str:
        """Load stock data from JSON files to PostgreSQL - simple test version."""
        print("🔍 Testing stock JSON loading to PostgreSQL...")

        # Get PostgreSQL connection
        postgres_hook = PostgresHook(postgres_conn_id=DAGConfig.POSTGRES_CONN_ID)

        # Test basic connectivity first
        result = postgres_hook.get_first("SELECT 'Connection successful' as status, current_database() as db;")
        print(f"✅ Database connection test: {result}")

        # Find all stock JSON files
        stock_files = list(DAGConfig.RAW_STOCKS_DIR.glob("*.json"))
        print(f"📁 Found {len(stock_files)} stock JSON files in {DAGConfig.RAW_STOCKS_DIR}")

        if not stock_files:
            print("⚠️  No stock JSON files found")
            return "no_stock_files_found"

        # Just count records without processing for now
        total_records = 0
        for json_file in stock_files[:1]:  # Only process first file for testing
            print(f"📖 Examining {json_file.name}...")

            try:
                with open(json_file, "r") as f:
                    stock_data = json.load(f)

                if isinstance(stock_data, dict):
                    # Handle different JSON structures
                    if "Time Series (Daily)" in stock_data:
                        records = len(stock_data["Time Series (Daily)"])
                    elif "data" in stock_data:
                        records = len(stock_data["data"])
                    else:
                        records = len(stock_data)
                else:
                    records = len(stock_data)

                print(f"📊 Found {records} records in {json_file.name}")
                total_records += records

                # Simple test - create a basic table if it doesn't exist
                postgres_hook.run(
                    """
                    CREATE TABLE IF NOT EXISTS test_stock_load (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255),
                        record_count INTEGER,
                        loaded_at TIMESTAMP DEFAULT NOW()
                    );
                """
                )

                # Insert test record
                postgres_hook.run(
                    "INSERT INTO test_stock_load (filename, record_count) VALUES (%s, %s)",
                    parameters=[json_file.name, records],
                )

                print(f"✅ Successfully tested {json_file.name}")
                break  # Only test one file

            except Exception as e:
                print(f"❌ Error processing {json_file.name}: {e}")
                raise

        print(f"🎉 Test completed - found {total_records} stock records")
        return f"test_completed_{total_records}_records"

    @task
    def load_exchange_json_to_postgres() -> str:
        """Load exchange rate data from JSON files to PostgreSQL - simple test version."""
        print("🔍 Testing exchange rate JSON loading to PostgreSQL...")

        # Get PostgreSQL connection
        postgres_hook = PostgresHook(postgres_conn_id=DAGConfig.POSTGRES_CONN_ID)

        # Test basic connectivity first
        result = postgres_hook.get_first("SELECT 'Connection successful' as status, current_database() as db;")
        print(f"✅ Database connection test: {result}")

        # Find all exchange rate JSON files
        exchange_files = list(DAGConfig.RAW_EXCHANGE_DIR.glob("*.json"))
        print(f"📁 Found {len(exchange_files)} exchange rate JSON files in {DAGConfig.RAW_EXCHANGE_DIR}")

        if not exchange_files:
            print("⚠️  No exchange rate JSON files found")
            return "no_exchange_files_found"

        # Just count records without processing for now
        total_records = 0
        for json_file in exchange_files[:1]:  # Only process first file for testing
            print(f"📖 Examining {json_file.name}...")

            try:
                with open(json_file, "r") as f:
                    exchange_data = json.load(f)

                if isinstance(exchange_data, dict):
                    # Handle different JSON structures
                    if "rates" in exchange_data:
                        records = len(exchange_data["rates"])
                    elif "data" in exchange_data:
                        records = len(exchange_data["data"])
                    else:
                        records = len(exchange_data)
                else:
                    records = len(exchange_data)

                print(f"📊 Found {records} records in {json_file.name}")
                total_records += records

                # Simple test - create a basic table if it doesn't exist
                postgres_hook.run(
                    """
                    CREATE TABLE IF NOT EXISTS test_exchange_load (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255),
                        record_count INTEGER,
                        loaded_at TIMESTAMP DEFAULT NOW()
                    );
                """
                )

                # Insert test record
                postgres_hook.run(
                    "INSERT INTO test_exchange_load (filename, record_count) VALUES (%s, %s)",
                    parameters=[json_file.name, records],
                )

                print(f"✅ Successfully tested {json_file.name}")
                break  # Only test one file

            except Exception as e:
                print(f"❌ Error processing {json_file.name}: {e}")
                raise

        print(f"🎉 Test completed - found {total_records} exchange rate records")
        return f"test_completed_{total_records}_records"

    @task
    def cleanup_old_data() -> str:
        """Clean up old data."""
        print("Cleaning up old data...")
        # Placeholder for cleanup logic
        return "cleanup_completed"

    # Create control tasks using traditional operators
    start_task = EmptyOperator(task_id="start_etl")
    end_task = EmptyOperator(task_id="end_etl")

    # SQL processing tasks for cleanup and transformation
    clean_transform_data = SQLExecuteQueryOperator(
        task_id="clean_transform_data",
        sql=DAGConfig.SQL_FILES["clean_transform_data"],
        conn_id=DAGConfig.POSTGRES_CONN_ID,
    )

    # Create task instances
    extract_stock_task = extract_stock_data_to_json()
    extract_exchange_task = extract_exchange_rates_to_json_task()
    load_stock_task = load_stock_json_to_postgres()
    load_exchange_task = load_exchange_json_to_postgres()
    quality_checks_task = run_data_quality_checks()
    monitor_task = monitor_etl_process_task()
    cleanup_task = cleanup_old_data()

    # Define task dependencies following the 6-step ETL process:
    # Step 1 & 2: Start with parallel data extraction to JSON files
    start_task >> [extract_stock_task, extract_exchange_task]

    # Step 3: After JSON files are created, load them into PostgreSQL in parallel
    extract_stock_task >> load_stock_task
    extract_exchange_task >> load_exchange_task

    # After both raw data loads complete, run the clean and transform step
    [load_stock_task, load_exchange_task] >> clean_transform_data

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
