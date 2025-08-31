"""
Load JSON files from dags/raw_data directly into fact tables using DatabaseManager.

This wrapper loads stock and currency data directly into fact_stock_prices and
fact_currency_rates tables, bypassing the removed raw table intermediary layer.
DAGs call it via PythonOperator and it delegates to DatabaseManager for insertion.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from ticker_converter.data_ingestion.database_manager import DatabaseManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # helpers -> dags -> project_root
RAW_STOCKS_DIR = PROJECT_ROOT / "dags" / "raw_data" / "stocks"
RAW_EXCHANGE_DIR = PROJECT_ROOT / "dags" / "raw_data" / "exchange"


def _get_database_connection() -> str:
    """Get database connection string from environment variables."""
    # Check for full DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build PostgreSQL URL from components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "local_db")
    user = os.getenv("POSTGRES_USER", "dbuser123")
    password = os.getenv("POSTGRES_PASSWORD", "password123")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _validate_stock_record(record: Dict[str, Any]) -> bool:
    """Validate a stock record has required fields."""
    required_fields = ["symbol", "data_date", "open_price", "high_price", "low_price", "close_price", "volume"]

    for field in required_fields:
        if field not in record or record[field] is None:
            print(f"⚠️ Invalid stock record missing {field}: {record}")
            return False

    # Validate data types
    try:
        float(record["open_price"])
        float(record["high_price"])
        float(record["low_price"])
        float(record["close_price"])
        int(record["volume"])
    except (ValueError, TypeError):
        print(f"⚠️ Invalid stock record data types: {record}")
        return False

    return True


def _validate_currency_record(record: Dict[str, Any]) -> bool:
    """Validate a currency record has required fields."""
    required_fields = ["from_currency", "to_currency", "data_date", "exchange_rate"]

    for field in required_fields:
        if field not in record or record[field] is None:
            print(f"⚠️ Invalid currency record missing {field}: {record}")
            return False

    # Validate data types
    try:
        float(record["exchange_rate"])
    except (ValueError, TypeError):
        print(f"⚠️ Invalid currency record data types: {record}")
        return False

    return True


def _read_json_files(directory: Path) -> List[Dict[str, Any]]:
    """Read and validate JSON files from directory."""
    records: List[Dict[str, Any]] = []
    invalid_count = 0

    for p in sorted(directory.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Validate each record based on directory type
                    is_stock_dir = "stocks" in str(directory)
                    for record in data:
                        if is_stock_dir and _validate_stock_record(record):
                            records.append(record)
                        elif not is_stock_dir and _validate_currency_record(record):
                            records.append(record)
                        else:
                            invalid_count += 1
                elif isinstance(data, dict):
                    # Support single-file dict wrappers
                    is_stock_dir = "stocks" in str(directory)
                    if is_stock_dir and _validate_stock_record(data):
                        records.append(data)
                    elif not is_stock_dir and _validate_currency_record(data):
                        records.append(data)
                    else:
                        invalid_count += 1
        except Exception as e:
            print(f"⚠️ Error reading {p}: {e}")
            continue

    if invalid_count > 0:
        print(f"⚠️ Skipped {invalid_count} invalid records from {directory}")

    return records


def load_raw_to_db(data_directory: str = None, connection_string: str = None) -> Dict[str, int]:
    """Load JSON files directly into fact tables (bypassing raw tables).

    Reads JSON files from configured directories and inserts them directly 
    into fact_stock_prices and fact_currency_rates tables respectively.

    Args:
        data_directory (str, optional): Override directory path for JSON files.
                                      If provided, function looks for 'stocks' and 'exchange' subdirectories.
                                      If None, uses configured RAW_STOCKS_DIR and RAW_EXCHANGE_DIR.
        connection_string (str, optional): Override PostgreSQL connection string.
                                         If None, uses environment configuration.

    Returns a summary dict with inserted counts.
    """
    # Use provided connection string or get from environment
    conn_str = connection_string if connection_string else _get_database_connection()
    db = DatabaseManager(connection_string=conn_str)

    # Determine data directories
    if data_directory:
        stocks_dir = os.path.join(data_directory, "stocks")
        exchange_dir = os.path.join(data_directory, "exchange")
        print(f"Loading stock data from: {stocks_dir}")
        print(f"Loading exchange data from: {exchange_dir}")
    else:
        stocks_dir = RAW_STOCKS_DIR
        exchange_dir = RAW_EXCHANGE_DIR
        print(f"Loading stock data from: {stocks_dir}")
        print(f"Loading exchange data from: {exchange_dir}")

    # Read stock records
    stock_records = _read_json_files(Path(stocks_dir))
    print(f"Found {len(stock_records)} stock records to insert")
    stock_inserted = db.insert_stock_data(stock_records) if stock_records else 0

    # Read exchange records
    exchange_records = _read_json_files(Path(exchange_dir))
    print(f"Found {len(exchange_records)} exchange records to insert")
    exchange_inserted = db.insert_currency_data(exchange_records) if exchange_records else 0

    print(f"Insertion complete: {stock_inserted} stocks, {exchange_inserted} exchange rates")
    return {"stock_inserted": stock_inserted, "exchange_inserted": exchange_inserted}
