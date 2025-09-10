"""
Step 1: Assess latest records in DB and JSON files.
Uses existing DDL structure from dags/sql/ddl/
"""

import sys
from pathlib import Path

import psycopg2
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

    # Initialize default values for database counts
    stock_count = 0
    currency_count = 0
    fact_stock_count = 0

    # Now attempt database operations with proper connection management
    print("🔗 Attempting database assessment with improved connection handling...")

    try:
        # Use PostgreSQL hook with proper timeout and connection management
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

        # Database queries to check table counts using hook methods (not raw connections)
        tables_to_check = ["stock_dimension", "currency_dimension", "fact_stock"]

        for table_name in tables_to_check:
            print(f"🔍 Checking {table_name} table...")
            
            # Check if table exists using hook.get_first with simple query format
            table_exists_query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}' AND table_schema = 'public'"
            result = hook.get_first(table_exists_query)
            table_exists = result[0] if result else 0

            if table_exists > 0:
                # Table exists, get row count using hook.get_first
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count_result = hook.get_first(count_query)
                row_count = count_result[0] if count_result else 0

                if table_name == "stock_dimension":
                    stock_count = row_count
                elif table_name == "currency_dimension":
                    currency_count = row_count
                elif table_name == "fact_stock":
                    fact_stock_count = row_count

                print(f"✅ {table_name}: {row_count} records")
            else:
                print(f"⚠️ {table_name}: table not found")

        print("✅ Database assessment completed successfully")

    except (psycopg2.Error, psycopg2.OperationalError) as db_error:
        print(f"⚠️ Database connection error: {str(db_error)}")
        print("📊 Continuing with file-based assessment only")
        # Do not raise the exception - allow the function to continue with file counts
    except Exception as e:
        print(f"⚠️ Unexpected error during database assessment: {str(e)}")
        print("📊 Continuing with file-based assessment only")
        # Do not raise the exception - allow the function to continue with file counts

    # Return comprehensive assessment
    result = {
        "json_stock_files": len(stock_files),
        "json_exchange_files": len(exchange_files),
        "db_stock_dimension_count": stock_count,
        "db_currency_dimension_count": currency_count,
        "db_fact_stock_count": fact_stock_count,
    }

    print(f"📊 Assessment complete: {result}")
    return result
