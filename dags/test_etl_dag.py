"""
Test DAG for ticker converter ETL pipeline.

This is a simple test DAG to verify Airflow is working correctly.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task


@dag(
    dag_id="test_etl_dag",
    description="A simple test DAG",
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
    """Test DAG definition using Airflow 3.0 syntax."""

    @task
    def test_function() -> str:
        """Simple test function."""
        print("Test DAG is working!")
        return "success"

    # Execute the test task
    test_function()


# Instantiate the DAG
test_dag = test_etl_dag()
