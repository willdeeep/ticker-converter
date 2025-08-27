"""Airflow DAG: daily ETL pipeline.

TaskFlow Task-based DAG using helpers in `dags/py` and core logic in `src/`.

This module follows the project's guidance: use `@task`, keep business logic
in helper modules, and keep the DAG thin and declarative.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from pendulum import datetime as pdatetime

# Add the project root to the Python path
_dag_file_path = Path(__file__).resolve()
_project_root = _dag_file_path.parent.parent
if str(_project_root) not in sys.path:
    sys.path.append(str(_project_root))

from dags.helpers.assess_records import assess_latest_records
from dags.helpers.collect_api_data import collect_api_data
from dags.helpers.load_raw_to_db import load_raw_to_db

from airflow.decorators import task
from airflow.models import DAG


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
    start_date=pdatetime(2025, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
) as dag:

    @task(task_id="assess_latest")
    def assess_latest_task() -> dict[str, Any]:
        return assess_latest_records()

    @task.branch(task_id="decide_collect")
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

    @task(task_id="collect_api")
    def collect_api_task() -> dict:
        """Task to collect data from the API."""
        return collect_api_data()

    @task(task_id="skip_collection")
    def skip_collection_task():
        """Dummy task to allow skipping the API collection step."""
        pass

    @task(task_id="load_raw", trigger_rule="none_failed_min_one_success")
    def load_raw_task() -> dict:
        """
        Task to load raw data from JSON files into the database.
        This task acts as a join point after the branching logic.
        """
        return load_raw_to_db()

    @task(task_id="end", trigger_rule="none_failed")
    def end_task():
        """Final task in the pipeline."""
        pass

    # Define task instances
    assess = assess_latest_task()
    branch = decide_collect(assess)
    collect = collect_api_task()
    skip = skip_collection_task()
    load = load_raw_task()
    end = end_task()

    # Define the DAG structure with branching
    assess >> branch
    branch >> collect >> load
    branch >> skip >> load
    load >> end
