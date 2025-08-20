"""
Manual backfill DAG for historical stock data.

This DAG provides manual historical data backfill capabilities using SQL operators:
1. Extract historical stock prices for configurable date ranges
2. Extract historical exchange rates for the same period
3. Use SQL operators to process and load historical data
4. Run comprehensive data validation for historical datasets
5. Generate backfill completion reports

This DAG is designed to be triggered manually with custom parameters
rather than running on a schedule.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.empty import EmptyOperator

# Add the src directory to the Python path (must be before ticker_converter imports)
sys.path.append("/Users/willhuntleyclarke/repos/interests/ticker-converter/src")

# These imports depend on the path modification above
# pylint: disable=wrong-import-position
from ticker_converter.data_ingestion.currency_fetcher import CurrencyDataFetcher
from ticker_converter.data_ingestion.nyse_fetcher import NYSEDataFetcher


class BackfillDAGConfig:
    """Configuration for the manual backfill DAG."""

    # DAG metadata
    DAG_ID = "ticker_converter_manual_backfill"
    DESCRIPTION = "Manual backfill pipeline for historical stock and currency data"
    TAGS = ["ticker-converter", "backfill", "historical", "manual"]

    # DAG timing
    START_DATE = datetime(2024, 1, 1)

    # Default arguments
    DEFAULT_ARGS = {
        "owner": "ticker-converter",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
    }

    # Database connection
    POSTGRES_CONN_ID = "postgres_default"

    # File paths
    RAW_DATA_DIR = "raw_data/backfill"
    SQL_DIR = "dags/sql"

    # SQL files for backfill processing
    SQL_FILES = {
        "validate_backfill_period": "sql/backfill/validate_backfill_period.sql",
        "load_historical_stock_data": "sql/backfill/load_historical_stock_data.sql",
        "load_historical_exchange_data": "sql/backfill/load_historical_exchange_data.sql",
        "deduplicate_historical_data": "sql/backfill/deduplicate_historical_data.sql",
        "validate_historical_data": "sql/backfill/validate_historical_data.sql",
        "generate_backfill_report": "sql/backfill/generate_backfill_report.sql",
    }


def extract_historical_stock_data(start_date: str, end_date: str, symbols: list[str] | None = None) -> str:
    """Extract historical stock data for specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        symbols: Optional list of specific symbols to backfill

    Returns:
        Path to the created JSON file
    """
    # Initialize the NYSE data fetcher
    nyse_fetcher = NYSEDataFetcher()

    # Ensure raw data directory exists
    raw_data_path = Path(BackfillDAGConfig.RAW_DATA_DIR)
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Extract historical stock data
    # Note: This would need to be enhanced to support date ranges in the fetcher
    historical_data = nyse_fetcher.fetch_and_prepare_all_data()

    # Add backfill metadata
    backfill_metadata = {
        "backfill_type": "historical_stock_data",
        "start_date": start_date,
        "end_date": end_date,
        "symbols": symbols or "all",
        "extraction_timestamp": datetime.now().isoformat(),
        "data": historical_data,
    }

    # Save to JSON file with backfill identifier
    filename = f"historical_stocks_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backfill_metadata, f, indent=2, default=str)

    print(f"Historical stock data extracted and saved to {filepath}")
    return str(filepath)


def extract_historical_exchange_data(start_date: str, end_date: str) -> str:
    """Extract historical exchange rate data for specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Path to the created JSON file
    """
    # Initialize the currency data fetcher
    currency_fetcher = CurrencyDataFetcher()

    # Ensure raw data directory exists
    raw_data_path = Path(BackfillDAGConfig.RAW_DATA_DIR)
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Extract historical exchange rate data
    # Note: This would need to be enhanced to support date ranges in the fetcher
    historical_data = currency_fetcher.fetch_and_prepare_fx_data()

    # Add backfill metadata
    backfill_metadata = {
        "backfill_type": "historical_exchange_data",
        "start_date": start_date,
        "end_date": end_date,
        "extraction_timestamp": datetime.now().isoformat(),
        "data": historical_data,
    }

    # Save to JSON file with backfill identifier
    filename = f"historical_exchange_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = raw_data_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backfill_metadata, f, indent=2, default=str)

    print(f"Historical exchange data extracted and saved to {filepath}")
    return str(filepath)


def generate_backfill_summary(stock_file: str, exchange_file: str, start_date: str, end_date: str) -> dict:
    """Generate backfill completion summary.

    Args:
        stock_file: Path to stock data file
        exchange_file: Path to exchange data file
        start_date: Backfill start date
        end_date: Backfill end date

    Returns:
        Dictionary containing backfill summary
    """
    summary = {
        "backfill_completed": datetime.now().isoformat(),
        "date_range": {"start_date": start_date, "end_date": end_date},
        "files_created": {"stock_data": stock_file, "exchange_data": exchange_file},
        "status": "completed",
        "next_steps": [
            "Review data quality validation results",
            "Check for any data gaps or anomalies",
            "Verify data integrity in target tables",
        ],
    }

    # Save summary report
    raw_data_path = Path(BackfillDAGConfig.RAW_DATA_DIR)
    summary_file = raw_data_path / f"backfill_summary_{start_date}_{end_date}.json"

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Backfill summary saved to {summary_file}")
    return summary


@dag(
    dag_id=BackfillDAGConfig.DAG_ID,
    description=BackfillDAGConfig.DESCRIPTION,
    schedule=None,  # Manual trigger only
    start_date=BackfillDAGConfig.START_DATE,
    catchup=False,
    max_active_runs=1,
    tags=BackfillDAGConfig.TAGS,
    default_args=BackfillDAGConfig.DEFAULT_ARGS,
    params={
        "start_date": Param(default="2024-01-01", description="Start date for backfill (YYYY-MM-DD)", type="string"),
        "end_date": Param(default="2024-01-31", description="End date for backfill (YYYY-MM-DD)", type="string"),
        "symbols": Param(default="", description="Comma-separated list of symbols (empty for all)", type="string"),
        "validate_only": Param(
            default=False, description="Only validate date range without extracting data", type="boolean"
        ),
    },
)
def ticker_converter_manual_backfill() -> None:
    """Manual backfill DAG using Airflow 3.0 syntax with configurable parameters."""
    # pylint: disable=pointless-statement

    @task
    def validate_backfill_parameters(**context) -> dict:
        """Validate backfill parameters and date range."""
        params = context["params"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        symbols = params["symbols"]
        validate_only = params["validate_only"]

        # Parse and validate dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}") from e

        if start_dt >= end_dt:
            raise ValueError("Start date must be before end date")

        if end_dt > datetime.now():
            raise ValueError("End date cannot be in the future")

        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None

        validation_result = {
            "start_date": start_date,
            "end_date": end_date,
            "symbols": symbol_list,
            "validate_only": validate_only,
            "date_range_days": (end_dt - start_dt).days,
            "validation_status": "passed",
        }

        print(f"Backfill validation passed: {validation_result}")
        return validation_result

    @task
    def extract_historical_stocks(**context) -> str:
        """Extract historical stock data based on parameters."""
        validation_result = context["ti"].xcom_pull(task_ids="validate_parameters")

        if validation_result["validate_only"]:
            print("Validation-only mode: Skipping stock data extraction")
            return "validation_only"

        return extract_historical_stock_data(
            validation_result["start_date"], validation_result["end_date"], validation_result["symbols"]
        )

    @task
    def extract_historical_exchange(**context) -> str:
        """Extract historical exchange rate data based on parameters."""
        validation_result = context["ti"].xcom_pull(task_ids="validate_parameters")

        if validation_result["validate_only"]:
            print("Validation-only mode: Skipping exchange data extraction")
            return "validation_only"

        return extract_historical_exchange_data(validation_result["start_date"], validation_result["end_date"])

    @task
    def generate_completion_report(**context) -> dict:
        """Generate backfill completion report."""
        validation_result = context["ti"].xcom_pull(task_ids="validate_parameters")
        stock_file = context["ti"].xcom_pull(task_ids="extract_historical_stocks")
        exchange_file = context["ti"].xcom_pull(task_ids="extract_historical_exchange")

        if validation_result["validate_only"]:
            return {
                "validation_only": True,
                "parameters_validated": validation_result,
                "status": "validation_completed",
            }

        return generate_backfill_summary(
            stock_file, exchange_file, validation_result["start_date"], validation_result["end_date"]
        )

    # Create control tasks
    start_task = EmptyOperator(task_id="start_backfill")
    end_task = EmptyOperator(task_id="end_backfill")

    # SQL processing tasks for backfill
    load_historical_stocks = SQLExecuteQueryOperator(
        task_id="load_historical_stocks",
        sql=BackfillDAGConfig.SQL_FILES["load_historical_stock_data"],
    )

    load_historical_exchange = SQLExecuteQueryOperator(
        task_id="load_historical_exchange",
        sql=BackfillDAGConfig.SQL_FILES["load_historical_exchange_data"],
    )

    deduplicate_data = SQLExecuteQueryOperator(
        task_id="deduplicate_historical_data",
        sql=BackfillDAGConfig.SQL_FILES["deduplicate_historical_data"],
    )

    validate_data = SQLExecuteQueryOperator(
        task_id="validate_historical_data",
        sql=BackfillDAGConfig.SQL_FILES["validate_historical_data"],
    )

    # Create task instances
    validate_params_task = validate_backfill_parameters()
    extract_stocks_task = extract_historical_stocks()
    extract_exchange_task = extract_historical_exchange()
    completion_report_task = generate_completion_report()

    # Define task dependencies for manual backfill workflow:
    # Step 1: Validate parameters
    start_task >> validate_params_task

    # Step 2: Extract historical data in parallel (conditionally)
    validate_params_task >> [extract_stocks_task, extract_exchange_task]

    # Step 3: Load extracted data into database (conditionally)
    extract_stocks_task >> load_historical_stocks
    extract_exchange_task >> load_historical_exchange

    # Step 4: Deduplicate data after both loads complete
    [load_historical_stocks, load_historical_exchange] >> deduplicate_data

    # Step 5: Validate loaded data
    deduplicate_data >> validate_data

    # Step 6: Generate completion report
    validate_data >> completion_report_task

    # End the backfill
    completion_report_task >> end_task


# Instantiate the DAG
manual_backfill_dag = ticker_converter_manual_backfill()
