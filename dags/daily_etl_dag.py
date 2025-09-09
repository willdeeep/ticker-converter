"""Airflow DAG: daily ETL pipeline.

TaskFlow Task-based DAG using helpers in `dags/py` and core logic in `src/`.

This module follows the project's guidance: use `@task`, keep business logic
in helper modules, and keep the DAG thin and declarative.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow import DAG
from airflow.decorators import task

# Get the current file's directory (dags directory)
_dag_file_path = Path(__file__).resolve()
_dags_dir = _dag_file_path.parent


# Import helper functions using absolute file paths
def _import_module_from_path(module_name: str, file_path: Path):
    """Import a module from an absolute file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    raise ImportError(f"Could not import {module_name} from {file_path}")


# Import helper modules
_assess_module = _import_module_from_path("assess_records", _dags_dir / "helpers" / "assess_records.py")
_collect_module = _import_module_from_path("collect_api_data", _dags_dir / "helpers" / "collect_api_data.py")
_load_module = _import_module_from_path("load_raw_to_db", _dags_dir / "helpers" / "load_raw_to_db.py")
_connection_validator_module = _import_module_from_path(
    "connection_validator", _dags_dir / "helpers" / "connection_validator.py"
)

# Extract the functions we need
assess_latest_records = _assess_module.assess_latest_records
collect_api_data = _collect_module.collect_api_data
load_raw_to_db = _load_module.load_raw_to_db
validate_dag_connections = _connection_validator_module.validate_dag_connections
STANDARD_PIPELINE_CONNECTIONS = _connection_validator_module.STANDARD_PIPELINE_CONNECTIONS

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# If you can't (yet) install stubs, add a local ignore for the DAG signature
with DAG(  # type: ignore[arg-type]
    dag_id="daily_etl_pipeline",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
) as dag:

    @task(task_id="validate_connections", execution_timeout=timedelta(seconds=30))
    def validate_connections_task() -> dict[str, Any]:
        """Validate that all required connections are available before starting the pipeline."""
        return validate_dag_connections(
            required_connections=STANDARD_PIPELINE_CONNECTIONS, task_name="validate_connections"
        )

    @task(task_id="assess_latest", execution_timeout=timedelta(seconds=30))
    def assess_latest_task() -> dict[str, Any]:
        return assess_latest_records()

    @task.branch(task_id="decide_collect", execution_timeout=timedelta(seconds=10))
    def decide_collect(assess: dict[str, Any]) -> str:
        """
        Decides whether to collect new data from the API.

        If there are no raw JSON files and no data in the fact table,
        it's an initial run, so we must collect data. Otherwise, we can
        skip the collection step and proceed to load any existing files.
        """
        is_initial_run = (
            assess.get("json_stock_files", 0) == 0
            and assess.get("json_exchange_files", 0) == 0
            and assess.get("db_fact_stock_count", 0) == 0
        )
        if is_initial_run:
            return "collect_api"
        return "skip_collection"

    @task(task_id="collect_api", execution_timeout=timedelta(minutes=2))
    def collect_api_task() -> dict:
        """Task to collect data from the API."""
        return collect_api_data()

    @task(task_id="skip_collection", execution_timeout=timedelta(seconds=10))
    def skip_collection_task():
        """Dummy task to allow skipping the API collection step."""
        pass

    @task(task_id="load_to_facts", trigger_rule="none_failed_min_one_success", execution_timeout=timedelta(seconds=60))
    def load_to_facts_task() -> dict:
        """
        Task to load data from JSON files directly into fact tables.
        This task acts as a join point after the branching logic and
        bypasses the removed raw table intermediary layer.
        """
        return load_raw_to_db()

    @task(task_id="end", trigger_rule="none_failed", execution_timeout=timedelta(seconds=10))
    def end_task():
        """Final task in the pipeline."""
        pass

    # Define task instances
    validate_connections = validate_connections_task()
    assess = assess_latest_task()
    branch = decide_collect(assess)
    collect = collect_api_task()
    skip = skip_collection_task()
    load = load_to_facts_task()
    end = end_task()

    # Define the DAG structure with branching
    validate_connections >> assess >> branch
    branch >> collect >> load
    branch >> skip >> load
    load >> end
