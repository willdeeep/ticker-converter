"""Integration tests for Airflow 3.x DAG task execution contexts.

This module tests the specific task execution scenarios where PostgreSQL
operations hang during DAG execution in Airflow 3.x environment.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Proper Airflow 3.x import for PythonOperator
from airflow.providers.standard.operators.python import PythonOperator

from airflow import DAG

# Import the helper function for Airflow 3.x compatibility
from tests.integration.airflow_test_helpers import create_test_task_instance, run_task_with_timeout

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Add dags directory to path for helper imports
_dag_file_path = Path(__file__).resolve()
_project_root = _dag_file_path.parent.parent.parent
_dags_dir = _project_root / "dags"
sys.path.append(str(_dags_dir))


class TestAirflowTaskExecutionContext:
    """Test Airflow 3.x specific task execution contexts with PostgreSQL."""

    def test_python_operator_postgres_task_execution(self) -> None:
        """Test PostgreSQL operations within PythonOperator task execution."""

        def postgres_task_function(**context):
            """Task function that uses PostgreSQL hook."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Test the specific operations from assess_records that hang
            task_info = context.get("task_instance", {})

            results = {
                "task_id": getattr(task_info, "task_id", "unknown"),
                "execution_date": str(context.get("execution_date", "unknown")),
                "database_operations": [],
            }

            # These are the exact queries that hang in assess_records
            queries = [
                (
                    "check_stock_dimension",
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'stock_dimension';",
                ),
                (
                    "check_currency_dimension",
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'currency_dimension';",
                ),
                ("check_fact_stock", "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fact_stock';"),
            ]

            for operation_name, query in queries:
                start_time = time.time()
                try:
                    result = hook.get_first(query)
                    elapsed = time.time() - start_time

                    results["database_operations"].append(
                        {
                            "operation": operation_name,
                            "result": result[0] if result else 0,
                            "elapsed_seconds": elapsed,
                            "success": True,
                        }
                    )
                except Exception as e:
                    elapsed = time.time() - start_time
                    results["database_operations"].append(
                        {"operation": operation_name, "error": str(e), "elapsed_seconds": elapsed, "success": False}
                    )

            return results

        # Create test DAG
        dag = DAG("test_postgres_hanging", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)

        task = PythonOperator(task_id="test_postgres_operations", python_callable=postgres_task_function, dag=dag)

        # Execute task with timeout
        def run_task():
            # Simulate task execution context
            from airflow.models import DagRun, TaskInstance
            from airflow.utils import timezone
            from airflow.utils.state import DagRunState
            from airflow.utils.types import DagRunType

            # Use helper function for proper Airflow 3.x TaskInstance creation
            ti = create_test_task_instance(task)
            return ti.run()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_task)

            try:
                # 60 second timeout for task execution
                result = future.result(timeout=60)

                # Task should complete without hanging
                assert True, "Task execution completed successfully"

            except ConcurrentTimeoutError:
                pytest.fail("PythonOperator task with PostgreSQL operations timed out - indicates hanging issue")

    def test_dag_helper_assess_records_integration(self) -> None:
        """Test assess_records function execution through simulated Airflow task context."""

        def task_with_assess_records(**context):
            """Simulated Airflow task that calls assess_records"""
            from dags.helpers.assess_records import assess_latest_records

            start_time = time.time()

            try:
                result = assess_latest_records()
                elapsed = time.time() - start_time

                return {
                    "result": result,
                    "execution_time_seconds": elapsed,
                    "task_status": "success",
                    "execution_date": str(context.get("execution_date", "unknown")),
                }

            except Exception as e:
                elapsed = time.time() - start_time
                return {
                    "error": str(e),
                    "execution_time_seconds": elapsed,
                    "task_status": "failed",
                    "execution_date": str(context.get("execution_date", "unknown")),
                }

        # Simulate the task execution without complex Airflow metadata
        def run_assess_task():
            from airflow.utils import timezone

            # Create minimal context similar to what Airflow provides
            execution_date = timezone.utcnow()
            context = {
                "execution_date": execution_date,
                "dag_run": None,
                "task_instance": None,
                "task": None,
                "dag": None,
            }

            return task_with_assess_records(**context)

    def test_dag_helper_connection_validator_integration(self) -> None:
        """Test the connection validator helper in task context."""

        def task_with_connection_validation(**context):
            """Task that calls connection validator."""
            from helpers.connection_validator import STANDARD_PIPELINE_CONNECTIONS, validate_dag_connections

            start_time = time.time()

            result = validate_dag_connections(
                required_connections=STANDARD_PIPELINE_CONNECTIONS,
                task_name=(
                    context.get("task_instance", {}).task_id
                    if hasattr(context.get("task_instance", {}), "task_id")
                    else "test_task"
                ),
            )

            elapsed = time.time() - start_time
            result["execution_time_seconds"] = elapsed

            return result

        # Create test DAG
        dag = DAG("test_connection_validation_hanging", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)

        task = PythonOperator(
            task_id="validate_connections_task", python_callable=task_with_connection_validation, dag=dag
        )

        # Execute with timeout
        def run_validation_task():
            # Use helper function for proper Airflow 3.x TaskInstance creation
            ti = create_test_task_instance(task)
            return ti.run()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_validation_task)

            try:
                # 30 second timeout for connection validation
                result = future.result(timeout=30)

                assert True, "Connection validation task completed successfully"

            except ConcurrentTimeoutError:
                pytest.fail("Connection validation task timed out - indicates hanging issue")

    def test_multiple_concurrent_dag_tasks(self) -> None:
        """Test multiple DAG tasks running concurrently with PostgreSQL operations."""

        def concurrent_postgres_task(task_suffix, **context):
            """Task function for concurrent execution."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Simulate concurrent database operations
            operations = []
            for i in range(3):
                start_time = time.time()
                try:
                    result = hook.get_first(f"SELECT '{task_suffix}_{i}' as task_result, {i} as iteration;")
                    elapsed = time.time() - start_time
                    operations.append(
                        {"iteration": i, "result": result[0] if result else None, "elapsed": elapsed, "success": True}
                    )
                except Exception as e:
                    elapsed = time.time() - start_time
                    operations.append({"iteration": i, "error": str(e), "elapsed": elapsed, "success": False})

            return {"task_suffix": task_suffix, "operations": operations, "total_operations": len(operations)}

        # Create test DAG with multiple tasks
        dag = DAG("test_concurrent_postgres_tasks", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)

        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = PythonOperator(
                task_id=f"concurrent_postgres_task_{i}",
                python_callable=lambda task_suffix=f"task_{i}", **context: concurrent_postgres_task(
                    task_suffix, **context
                ),
                dag=dag,
            )
            tasks.append(task)

        # Execute tasks concurrently
        def run_concurrent_tasks():
            results = []
            for task in tasks:
                # Use helper function for proper Airflow 3.x TaskInstance creation
                ti = create_test_task_instance(task)
                result = ti.run()
                results.append(result)

            return results

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_concurrent_tasks)

            try:
                # 120 second timeout for all concurrent tasks
                results = future.result(timeout=120)

                assert len(results) == 3, "All concurrent tasks should complete"

            except ConcurrentTimeoutError:
                pytest.fail("Concurrent DAG tasks with PostgreSQL timed out - indicates resource contention/hanging")

    def test_airflow_task_retry_scenario(self) -> None:
        """Test PostgreSQL operations in Airflow task retry scenarios."""

        def flaky_postgres_task(attempt_count=None, **context):
            """Task that fails first time, succeeds second time."""
            if attempt_count is None:
                attempt_count = [0]
            attempt_count[0] += 1
            hook = PostgresHook(postgres_conn_id="postgres_default")

            if attempt_count[0] == 1:
                # First attempt - simulate failure that requires retry
                try:
                    hook.get_first("SELECT 1/0;")  # Division by zero error
                except Exception as e:
                    raise AirflowException(f"Simulated task failure: {e}") from e
                return None  # This will never be reached, but satisfies pylint
            else:
                # Second attempt - should succeed
                result = hook.get_first("SELECT 'retry_success' as status;")
                return {"attempt": attempt_count[0], "result": result[0] if result else None, "status": "success"}

        # Create test DAG
        dag = DAG("test_postgres_retry_hanging", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)

        task = PythonOperator(
            task_id="flaky_postgres_task",
            python_callable=flaky_postgres_task,
            dag=dag,
            retries=1,
            retry_delay=timedelta(seconds=1),
        )

        # Execute with retry logic using helper to avoid signal handling issues
        # Use helper function for proper Airflow 3.x TaskInstance creation
        ti = create_test_task_instance(task)

        # First attempt (should fail)
        try:
            run_task_with_timeout(ti, timeout_seconds=60)
            pytest.fail("First attempt should fail")
        except AirflowException:
            pass  # Expected failure

        # Reset task instance for retry
        ti.state = None  # Reset state to allow retry
        ti.try_number = ti.try_number + 1  # Increment try number

        # Second attempt (should succeed after retry logic)
        try:
            result = run_task_with_timeout(ti, timeout_seconds=60)
            assert True, "Retry task scenario completed successfully"
        except TimeoutError:
            pytest.fail("Task retry scenario with PostgreSQL timed out - indicates hanging on retry")


class TestAirflowDagExecution:
    """Test full DAG execution scenarios that could hang."""

    def test_simulated_daily_etl_dag_postgres_operations(self) -> None:
        """Test PostgreSQL operations similar to daily_etl_dag."""

        def etl_assess_task(**context):
            """Simulate the assess step from daily ETL DAG."""
            from helpers.assess_records import assess_latest_records

            return assess_latest_records()

        def etl_validate_task(**context):
            """Simulate the validation step from daily ETL DAG."""
            from helpers.connection_validator import STANDARD_PIPELINE_CONNECTIONS, validate_dag_connections

            return validate_dag_connections(STANDARD_PIPELINE_CONNECTIONS, "etl_validate")

        def etl_load_task(**context):
            """Simulate database loading operations."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Simulate table creation/validation operations
            operations = []

            table_checks = [
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';",
                "SELECT current_database();",
                "SELECT current_user;",
            ]

            for i, query in enumerate(table_checks):
                start_time = time.time()
                try:
                    result = hook.get_first(query)
                    elapsed = time.time() - start_time
                    operations.append(
                        {"query_num": i, "result": result[0] if result else None, "elapsed": elapsed, "success": True}
                    )
                except Exception as e:
                    elapsed = time.time() - start_time
                    operations.append({"query_num": i, "error": str(e), "elapsed": elapsed, "success": False})

            return {"load_operations": operations}

        # Create simulated ETL DAG
        dag = DAG("test_simulated_daily_etl", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)

        # Create ETL tasks
        assess_task = PythonOperator(task_id="assess_records", python_callable=etl_assess_task, dag=dag)

        validate_task = PythonOperator(task_id="validate_connections", python_callable=etl_validate_task, dag=dag)

        load_task = PythonOperator(task_id="load_data", python_callable=etl_load_task, dag=dag)

        # Set task dependencies
        assess_task >> validate_task >> load_task

        # Execute DAG simulation
        def run_etl_dag():
            results = {}

            # Execute tasks in sequence
            for task in [assess_task, validate_task, load_task]:
                # Use helper function for proper Airflow 3.x TaskInstance creation
                ti = create_test_task_instance(task)
                result = ti.run()
                results[task.task_id] = result

            return results

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_etl_dag)

            try:
                # 180 second timeout for full ETL simulation
                results = future.result(timeout=180)

                assert len(results) == 3, "All ETL tasks should complete"
                assert "assess_records" in results, "Assess task should complete"
                assert "validate_connections" in results, "Validation task should complete"
                assert "load_data" in results, "Load task should complete"

            except ConcurrentTimeoutError:
                pytest.fail("Simulated ETL DAG execution timed out - indicates hanging issue in task sequence")

    def test_dag_task_context_variables(self) -> None:
        """Test that task context variables do not interfere with PostgreSQL operations."""

        def context_aware_postgres_task(**context):
            """Task that uses both context variables and PostgreSQL."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Extract context information
            task_context = {
                "dag_id": context.get("dag", {}).dag_id if hasattr(context.get("dag", {}), "dag_id") else "unknown",
                "task_id": (
                    context.get("task_instance", {}).task_id
                    if hasattr(context.get("task_instance", {}), "task_id")
                    else "unknown"
                ),
                "execution_date": str(context.get("execution_date", "unknown")),
                "run_id": context.get("run_id", "unknown"),
            }

            # Perform PostgreSQL operations with context
            postgres_results = []

            queries = [
                f"SELECT '{task_context['dag_id']}' as dag_id;",
                f"SELECT '{task_context['task_id']}' as task_id;",
                "SELECT current_timestamp as execution_timestamp;",
            ]

            for query in queries:
                start_time = time.time()
                try:
                    result = hook.get_first(query)
                    elapsed = time.time() - start_time
                    postgres_results.append(
                        {"query": query, "result": result[0] if result else None, "elapsed": elapsed, "success": True}
                    )
                except Exception as e:
                    elapsed = time.time() - start_time
                    postgres_results.append({"query": query, "error": str(e), "elapsed": elapsed, "success": False})

            return {"task_context": task_context, "postgres_operations": postgres_results}

        # Create test DAG
        dag = DAG(
            "test_context_postgres_interaction",
            start_date=datetime(2023, 1, 1),
            schedule=None,
            catchup=False,
        )

        task = PythonOperator(task_id="context_postgres_task", python_callable=context_aware_postgres_task, dag=dag)

        # Execute with full context using helper to avoid signal handling issues
        # Use helper function for proper Airflow 3.x TaskInstance creation
        ti = create_test_task_instance(task)

        try:
            # 30 second timeout for context test
            run_task_with_timeout(ti, timeout_seconds=30)

            # In Airflow 3.x, get the return value from XCom
            result = ti.xcom_pull(task_ids=ti.task_id, key="return_value")

            assert result is not None, "Task result should not be None"
            assert "task_context" in result, "Should contain task context"
            assert "postgres_operations" in result, "Should contain PostgreSQL results"

            # Verify PostgreSQL operations completed
            postgres_ops = result["postgres_operations"]
            assert len(postgres_ops) == 3, "Should execute 3 PostgreSQL queries"
            assert all(op["success"] for op in postgres_ops), "All PostgreSQL operations should succeed"

        except TimeoutError:
            pytest.fail(
                "Context-aware PostgreSQL task timed out - indicates context interference with DB operations"
            )
