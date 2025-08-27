"""
Step 1: Assess latest records in DB and JSON files.
Uses existing DDL structure from dags/sql/ddl/
"""

import json
import sys
from pathlib import Path

from airflow.providers.postgres.hooks.postgres import PostgresHook

# Add the src directory to the Python path
_dag_file_path = Path(__file__).resolve()
_project_root = _dag_file_path.parent.parent.parent
sys.path.append(str(_project_root / "src"))


# Configuration
PROJECT_ROOT = _project_root
RAW_STOCKS_DIR = PROJECT_ROOT / "dags" / "raw_data" / "stocks"
RAW_EXCHANGE_DIR = PROJECT_ROOT / "dags" / "raw_data" / "exchange"
SQL_DDL_DIR = PROJECT_ROOT / "dags" / "sql" / "ddl"
POSTGRES_CONN_ID = "postgres_default"


def assess_latest_records() -> dict:
    """Step 1: Assess latest records in DB and JSON."""
    print("🔍 Assessing latest records...")

    # Check JSON files
    stock_files = list(RAW_STOCKS_DIR.glob("*.json"))
    exchange_files = list(RAW_EXCHANGE_DIR.glob("*.json"))

    print(f"📁 Found {len(stock_files)} stock JSON files")
    print(f"📁 Found {len(exchange_files)} exchange JSON files")

    # Check database using existing schema
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    # Ensure schema exists using existing DDL
    print("🔧 Ensuring database schema exists...")
    ddl_file = SQL_DDL_DIR / "001_create_dimensions.sql"
    if ddl_file.exists():
        with open(ddl_file, "r", encoding="utf-8") as f:
            postgres_hook.run(f.read())

    # Count existing records in proper schema tables
    try:
        stock_count = postgres_hook.get_first("SELECT COUNT(*) FROM dim_stocks")[0]
        print(f"📊 Database stock dimension records: {stock_count}")
    except Exception as e:
        print(f"⚠️ Error counting stocks: {e}")
        stock_count = 0

    try:
        currency_count = postgres_hook.get_first("SELECT COUNT(*) FROM dim_currency")[0]
        print(f"📊 Database currency dimension records: {currency_count}")
    except Exception as e:
        print(f"⚠️ Error counting currencies: {e}")
        currency_count = 0

    # Check for fact tables (will be created later in pipeline)
    try:
        fact_stock_count = (
            postgres_hook.get_first("SELECT COUNT(*) FROM fact_stock_prices")[0]
            if postgres_hook.get_first("SELECT to_regclass('fact_stock_prices')")[0]
            else 0
        )
        print(f"📊 Database fact stock records: {fact_stock_count}")
    except Exception:
        fact_stock_count = 0

    return {
        "json_stock_files": len(stock_files),
        "json_exchange_files": len(exchange_files),
        "db_stock_dimension_count": stock_count,
        "db_currency_dimension_count": currency_count,
        "db_fact_stock_count": fact_stock_count,
    }
