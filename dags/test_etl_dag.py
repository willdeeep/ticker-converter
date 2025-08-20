"""
Test DAG for ticker converter ETL pipeline.

This DAG verifies Airflow configuration and connectivity to external services.
It ensures AIRFLOW__CORE__DAGS_FOLDER is established from .env and tests
connectivity to Alpha Vantage API and PostgreSQL database.
"""

import os
from datetime import datetime, timedelta

import psycopg2
import requests
from airflow.decorators import dag, task


@dag(
    dag_id="test_etl_dag",
    description="Test DAG for service connectivity verification",
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["test", "ticker-converter"],
    default_args={
        "owner": "ticker-converter",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
)
def test_etl_dag() -> None:
    """Test DAG definition using Airflow 3.0 syntax with service connectivity tests."""

    @task
    def test_airflow_configuration() -> str:
        """Test Airflow configuration and environment variables."""
        # Verify AIRFLOW__CORE__DAGS_FOLDER is set from environment
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")

        if not dags_folder:
            raise ValueError("AIRFLOW__CORE__DAGS_FOLDER environment variable not set")

        if "dags" not in dags_folder:
            raise ValueError(
                f"AIRFLOW__CORE__DAGS_FOLDER seems incorrect: {dags_folder}"
            )

        print(f"✅ AIRFLOW__CORE__DAGS_FOLDER correctly set to: {dags_folder}")
        return "airflow_config_ok"

    @task
    def test_alpha_vantage_api_access() -> str:
        """Test Alpha Vantage API access without making actual API calls."""
        # Check API key environment variable
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")

        if api_key in ["demo", "your_api_key_here", ""]:
            raise ValueError("ALPHA_VANTAGE_API_KEY appears to be a placeholder value")

        # Test basic connectivity to Alpha Vantage (without using API key quota)
        try:
            response = requests.get("https://www.alphavantage.co", timeout=10)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Cannot reach alphavantage.co: {response.status_code}"
                )
        except requests.RequestException as e:
            raise ConnectionError(f"Cannot connect to Alpha Vantage: {e}") from e

        print("✅ Alpha Vantage API accessibility verified")
        print(f"✅ API key configured (length: {len(api_key)})")
        return "alpha_vantage_access_ok"

    @task
    def test_postgresql_database_access() -> str:
        """Test PostgreSQL database access using configured user from .env."""
        # Load database configuration from environment
        db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "ticker_converter"),
            "user": os.getenv("POSTGRES_USER", "ticker_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "ticker_password"),
        }

        # Verify all required environment variables are set
        for key, value in db_config.items():
            env_var = f"POSTGRES_{key.upper()}"
            if not value or value == f"your_{key}_here":
                raise ValueError(f"{env_var} environment variable not properly set")

        # Test database connectivity
        try:
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"],
                user=db_config["user"],
                password=db_config["password"],
                connect_timeout=10,
            )

            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()

            cursor.close()
            conn.close()

            print(f"✅ PostgreSQL database accessible: {db_config['database']}")
            print(f"✅ Database user configured: {db_config['user']}")
            print(f"✅ PostgreSQL version: {version[0][:50]}...")
            return "postgresql_access_ok"

        except psycopg2.Error as e:
            raise ConnectionError(f"Cannot connect to PostgreSQL: {e}") from e

    # Define task dependencies
    test_airflow_configuration()
    test_alpha_vantage_api_access()
    test_postgresql_database_access()

    # All tests can run in parallel - no return needed here


# Instantiate the DAG
test_dag = test_etl_dag()
