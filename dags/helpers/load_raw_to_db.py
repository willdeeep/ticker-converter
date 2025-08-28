"""
Load raw JSON files from dags/raw_data into raw tables using DatabaseManager.

This wrapper is intentionally small: DAGs call it via PythonOperator and it
delegates to the DatabaseManager for insertion, returning summary counts.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from ticker_converter.data_ingestion.database_manager import DatabaseManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


def _read_json_files(directory: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for p in sorted(directory.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records.extend(data)
                elif isinstance(data, dict):
                    # support single-file dict wrappers
                    records.append(data)
        except Exception:
            # Skip invalid files but continue processing others
            continue
    return records


def load_raw_to_db() -> Dict[str, int]:
    """Load JSON files into the database raw tables.

    Returns a summary dict with inserted counts.
    """
    # Use explicit database connection to avoid file system issues
    connection_string = _get_database_connection()
    db = DatabaseManager(connection_string=connection_string)

    # Read stock records
    stock_records = _read_json_files(RAW_STOCKS_DIR)
    stock_inserted = db.insert_stock_data(stock_records) if stock_records else 0

    # Read exchange records
    exchange_records = _read_json_files(RAW_EXCHANGE_DIR)
    exchange_inserted = db.insert_currency_data(exchange_records) if exchange_records else 0

    return {"stock_inserted": stock_inserted, "exchange_inserted": exchange_inserted}
