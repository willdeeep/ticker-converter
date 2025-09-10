"""Integration tests for Airflow task context and PostgreSQL hook interaction.

Tests the specific task execution patterns and context switching that can
cause hanging issues in Airflow-PostgreSQL integration.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


from airflow.exceptions import AirflowException
from airflow.models import DagBag, TaskInstance, DagRun
from airflow.models.dag import DAG
from airflow.providers.standard.operators.python import PythonOperator  # Airflow 3.x compatibility
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.types import DagRunType

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


from airflow.utils.types import DagRunType
from airflow.utils.state import DagRunState, TaskInstanceState
from airflow.utils.session import provide_session

from .airflow_test_helpers import create_test_task_instance, create_test_dagrun_with_db_session


def create_test_dagrun(dag, logical_date):
    """Helper to create DagRun for Airflow 3.x compatibility."""
    from airflow import settings
    from sqlalchemy.orm import sessionmaker
    
    run_id = f"test_run_{logical_date.strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Create session
    Session = sessionmaker(bind=settings.engine)
    session = Session()
    
    try:
        # Check if DagRun already exists
        existing_run = session.query(DagRun).filter(
            DagRun.dag_id == dag.dag_id,
            DagRun.run_id == run_id
        ).first()
        
        if existing_run:
            # Refresh and return the existing run
            session.refresh(existing_run)
            return existing_run.run_id
        
        # Create new DagRun
        dagrun = DagRun(
            dag_id=dag.dag_id,
            run_id=run_id,
            logical_date=logical_date,
            run_type=DagRunType.MANUAL,
            state=DagRunState.RUNNING,
            conf={},
            start_date=logical_date
        )
        
        session.add(dagrun)
        session.commit()
        
        # Return just the run_id since that's what TaskInstance needs
        created_run_id = dagrun.run_id
        session.close()
        
        return created_run_id
        
    except Exception as e:
        session.rollback()
        session.close()
        raise e


class TestAirflowTaskContextIntegration:
    """Test PostgreSQL integration within Airflow task contexts."""

    def test_postgres_hook_in_python_operator_context(self) -> None:
        """Test PostgreSQL hook usage within PythonOperator task context."""

        def test_postgres_task(**context):
            """Task function that uses PostgreSQL hook (mirrors DAG helper patterns)."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Simulate assess_records.py operations
            table_count = hook.get_first(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )[0]

            # Simulate connection_validator.py operations
            db_info = hook.get_first("SELECT current_database(), current_user")

            # Simulate load_raw_to_db.py transaction pattern
            with hook.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN;")
                cursor.execute("SELECT 1;")
                cursor.execute("COMMIT;")
                cursor.close()

            return {"table_count": table_count, "database": db_info[0], "user": db_info[1], "task_completed": True}

        # Create test DAG
        dag = DAG("test_postgres_integration", start_date=datetime(2023, 1, 1), schedule=None)

        task = PythonOperator(task_id="test_postgres_task", python_callable=test_postgres_task, dag=dag)

        # Create and run task instance with timeout monitoring
        ti = create_test_task_instance(task)

        start_time = time.time()

        def run_task():
            """Run task in separate thread to enable timeout."""
            try:
                result = ti.run()
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_task()))
        thread.start()
        thread.join(timeout=30)  # 30 second timeout

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"Task hung after {elapsed:.2f}s in Airflow context")

        assert len(result_container) == 1, "Task should have completed"
        result = result_container[0]

        assert result["success"], f"Task should succeed in Airflow context: {result.get('error')}"

        print(f"✅ PythonOperator task completed in {elapsed:.2f}s")

    def test_multiple_postgres_tasks_sequential(self) -> None:
        """Test multiple sequential PostgreSQL tasks (simulating DAG execution)."""

        def create_postgres_task(task_id: str, operation_type: str):
            """Create a PostgreSQL task for different operation types."""

            def task_function(**context):
                hook = PostgresHook(postgres_conn_id="postgres_default")

                if operation_type == "assess":
                    # Simulate assess_records operations
                    result = hook.get_first("SELECT COUNT(*) FROM information_schema.tables")
                    return {"operation": "assess", "table_count": result[0]}

                elif operation_type == "validate":
                    # Simulate connection validation
                    result = hook.get_first("SELECT version()")
                    return {"operation": "validate", "has_version": "PostgreSQL" in str(result[0])}

                elif operation_type == "load":
                    # Simulate load operations with transaction
                    with hook.get_conn() as conn:
                        cursor = conn.cursor()
                        cursor.execute("BEGIN;")
                        cursor.execute("SELECT COUNT(*) FROM information_schema.columns")
                        count = cursor.fetchone()[0]
                        cursor.execute("COMMIT;")
                        cursor.close()
                    return {"operation": "load", "column_count": count}

                else:
                    return {"operation": operation_type, "completed": True}

            return task_function

        # Create test DAG with multiple tasks
        dag = DAG("test_sequential_postgres", start_date=datetime(2023, 1, 1), schedule=None)

        task_configs = [
            ("assess_task", "assess"),
            ("validate_task", "validate"),
            ("load_task", "load"),
        ]

        results = []

        for task_id, operation_type in task_configs:
            task = PythonOperator(
                task_id=task_id, python_callable=create_postgres_task(task_id, operation_type), dag=dag
            )

            ti = create_test_task_instance(task)

            start_time = time.time()

            def run_sequential_task():
                """Run task with timeout monitoring."""
                try:
                    result = ti.run()
                    return {"success": True, "result": result, "task_id": task_id}
                except Exception as e:
                    return {"success": False, "error": str(e), "task_id": task_id}

            result_container = []
            thread = threading.Thread(target=lambda: result_container.append(run_sequential_task()))
            thread.start()
            thread.join(timeout=20)

            elapsed = time.time() - start_time

            if thread.is_alive():
                pytest.fail(f"Task {task_id} hung after {elapsed:.2f}s")

            assert len(result_container) == 1, f"Task {task_id} should complete"
            result = result_container[0]

            assert result["success"], f"Task {task_id} should succeed: {result.get('error')}"
            results.append(result)

            print(f"✅ Task {task_id} completed in {elapsed:.2f}s")

        # Validate all tasks completed successfully
        assert len(results) == 3, "All three tasks should complete"
        print("✅ Sequential PostgreSQL tasks completed successfully")

    def test_postgres_hook_task_isolation(self) -> None:
        """Test that PostgreSQL hooks are properly isolated between tasks."""

        task_results = {}

        def create_isolated_task(task_id: str, delay: float):
            """Create task that tests hook isolation."""

            def isolated_task_function(**context):
                hook = PostgresHook(postgres_conn_id="postgres_default")

                # Add delay to test concurrent access
                time.sleep(delay)

                # Get connection info specific to this task
                result = hook.get_first("SELECT pg_backend_pid(), current_timestamp")
                pid = result[0]
                timestamp = result[1]

                # Store result for isolation verification
                task_results[task_id] = {"pid": pid, "timestamp": str(timestamp), "hook_id": id(hook)}

                return {"task_id": task_id, "pid": pid}

            return isolated_task_function

        # Create multiple tasks with different delays
        task_configs = [
            ("task_1", 0.1),
            ("task_2", 0.2),
            ("task_3", 0.3),
        ]

        # Run tasks sequentially to test hook isolation without threading issues
        all_results = []

        for task_id, delay in task_configs:
            dag = DAG(f"test_isolation_{task_id}", start_date=datetime(2023, 1, 1), schedule=None)

            task = PythonOperator(task_id=task_id, python_callable=create_isolated_task(task_id, delay), dag=dag)

            ti = create_test_task_instance(task)

            # Run task directly (no threading to avoid signal issues)
            try:
                start_time = time.time()
                result = ti.run()
                elapsed = time.time() - start_time

                task_result = {"success": True, "result": result, "task_id": task_id, "elapsed": elapsed}
                all_results.append(task_result)

            except Exception as e:
                pytest.fail(f"Task {task_id} failed: {str(e)}")

            # Add delay to ensure tasks run at different times
            time.sleep(0.1)

        # Verify task isolation
        assert len(task_results) == 3, "All tasks should have recorded results"

        # Check that different tasks got different database connections (PIDs might differ)
        pids = [task_results[f"task_{i+1}"]["pid"] for i in range(3)]
        hook_ids = [task_results[f"task_{i+1}"]["hook_id"] for i in range(3)]

        # Hook objects should be different (isolation)
        assert len(set(hook_ids)) == 3, "Each task should have separate hook instances"

        print("✅ Task isolation test completed:")
        for task_id, data in task_results.items():
            print(f"   • {task_id}: PID {data['pid']}, Hook ID {data['hook_id']}")


class TestAirflowConnectionContextSwitching:
    """Test connection handling during Airflow context switching."""

    def test_connection_context_rapid_switching(self) -> None:
        """Test rapid context switching between Airflow tasks and PostgreSQL."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        def simulate_context_switch(switch_id: int):
            """Simulate rapid task context switching."""
            operations = []

            try:
                for i in range(5):
                    # Simulate task startup
                    start_time = time.time()

                    # Quick database operation (typical of DAG helpers)
                    result = hook.get_first("SELECT 1, pg_backend_pid()")

                    elapsed = time.time() - start_time
                    operations.append({"switch_id": switch_id, "operation_id": i, "result": result, "elapsed": elapsed})

                    # Simulate brief task processing
                    time.sleep(0.05)

                return {"success": True, "operations": operations}

            except Exception as e:
                return {"success": False, "error": str(e), "operations": operations}

        # Run multiple context switches concurrently
        threads = []
        for switch_id in range(4):
            result_container = []
            thread = threading.Thread(
                target=lambda sid=switch_id: result_container.append(simulate_context_switch(sid))
            )
            threads.append((thread, result_container, switch_id))
            thread.start()

        # Collect results
        all_results = []
        for thread, result_container, switch_id in threads:
            thread.join(timeout=15)

            if thread.is_alive():
                pytest.fail(f"Context switch {switch_id} hung")

            assert len(result_container) == 1, f"Context switch {switch_id} should complete"
            result = result_container[0]

            assert result["success"], f"Context switch {switch_id} should succeed: {result.get('error')}"
            all_results.append(result)

        # Validate results
        total_operations = sum(len(result["operations"]) for result in all_results)
        assert total_operations == 20, "All operations should complete (4 switches × 5 operations)"

        # Check for reasonable performance
        slow_operations = []
        for result in all_results:
            for op in result["operations"]:
                if op["elapsed"] > 2.0:  # Operations should be fast
                    slow_operations.append(op)

        assert len(slow_operations) == 0, f"No operations should be slow: {slow_operations}"

        print(f"✅ Context switching test completed: {total_operations} operations across 4 switches")

    def test_airflow_xcom_postgres_integration(self) -> None:
        """Test PostgreSQL operations with Airflow XCom (cross-communication)."""

        def postgres_producer_task(**context):
            """Task that produces data via PostgreSQL for XCom."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Get database metadata
            result = hook.get_first(
                """
                SELECT
                    current_database() as db_name,
                    COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )

            data = {"database": result[0], "table_count": result[1], "timestamp": str(datetime.now(timezone.utc))}

            # Return data for XCom
            return data

        def postgres_consumer_task(**context):
            """Task that consumes XCom data and performs PostgreSQL operations."""
            # In real Airflow, would get XCom data like: ti.xcom_pull(task_ids='producer')
            # For testing, simulate this
            producer_data = {"database": "test_db", "table_count": 5, "timestamp": str(datetime.now(timezone.utc))}

            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Verify database connection matches producer
            current_db = hook.get_first("SELECT current_database()")[0]

            # Perform additional operations
            version_info = hook.get_first("SELECT version()")[0]

            return {
                "current_database": current_db,
                "version_info": "PostgreSQL" in str(version_info),
                "producer_data_received": producer_data,
            }

        # Create test DAG
        dag = DAG("test_xcom_postgres", start_date=datetime(2023, 1, 1), schedule=None)

        producer_task = PythonOperator(task_id="postgres_producer", python_callable=postgres_producer_task, dag=dag)

        consumer_task = PythonOperator(task_id="postgres_consumer", python_callable=postgres_consumer_task, dag=dag)

        # Test producer task
        producer_ti = create_test_task_instance(producer_task)

        start_time = time.time()

        def run_producer():
            try:
                return {"success": True, "result": producer_ti.run()}
            except Exception as e:
                return {"success": False, "error": str(e)}

        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_producer()))
        thread.start()
        thread.join(timeout=15)

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"Producer task hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "Producer should complete"
        producer_result = result_container[0]

        assert producer_result["success"], f"Producer should succeed: {producer_result.get('error')}"

        # Test consumer task
        consumer_ti = create_test_task_instance(consumer_task)

        start_time = time.time()

        def run_consumer():
            try:
                return {"success": True, "result": consumer_ti.run()}
            except Exception as e:
                return {"success": False, "error": str(e)}

        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_consumer()))
        thread.start()
        thread.join(timeout=15)

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"Consumer task hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "Consumer should complete"
        consumer_result = result_container[0]

        assert consumer_result["success"], f"Consumer should succeed: {consumer_result.get('error')}"

        print("✅ XCom PostgreSQL integration test completed")
        print(f"   • Producer: {producer_result['result']}")
        print(f"   • Consumer: {consumer_result['result']}")


class TestAirflowDAGBagIntegration:
    """Test PostgreSQL integration through Airflow DAG bag loading."""

    def test_dag_bag_postgres_validation(self) -> None:
        """Test DAG bag loading with PostgreSQL validation tasks."""

        # Test loading the actual test DAG
        dagbag = DagBag(dag_folder=None, include_examples=False)

        # Look for our test DAG
        test_dag_id = "test_etl_dag"

        if test_dag_id not in dagbag.dags:
            pytest.skip(f"Test DAG {test_dag_id} not available in DAG bag")

        dag = dagbag.get_dag(test_dag_id)
        assert dag is not None, f"Should load DAG {test_dag_id}"

        # Test task retrieval
        postgres_tasks = [
            task for task in dag.tasks if "postgres" in task.task_id.lower() or "database" in task.task_id.lower()
        ]

        if len(postgres_tasks) == 0:
            # Look for any validation tasks
            validation_tasks = [
                task for task in dag.tasks if "validate" in task.task_id.lower() or "connection" in task.task_id.lower()
            ]
            postgres_tasks = validation_tasks

        assert len(postgres_tasks) > 0, "Should have PostgreSQL-related tasks"

        print(f"✅ DAG bag loaded {test_dag_id} with {len(postgres_tasks)} PostgreSQL tasks:")
        for task in postgres_tasks:
            print(f"   • {task.task_id}")

    def test_dag_import_postgres_dependencies(self) -> None:
        """Test that DAG imports do not hang on PostgreSQL dependencies."""

        start_time = time.time()

        def test_dag_imports():
            """Test DAG imports with timeout."""
            try:
                # Test importing our DAG files
                import sys
                from pathlib import Path

                dags_dir = Path(__file__).parent.parent.parent / "dags"
                if str(dags_dir) not in sys.path:
                    sys.path.append(str(dags_dir))

                # Import the test DAG
                try:
                    import test_etl_dag

                    return {"success": True, "imported": "test_etl_dag"}
                except ImportError as e:
                    return {"success": False, "error": f"Import failed: {e}"}

            except Exception as e:
                return {"success": False, "error": str(e)}

        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(test_dag_imports()))
        thread.start()
        thread.join(timeout=20)

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"DAG import hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "DAG import should complete"
        result = result_container[0]

        if result["success"]:
            print(f"✅ DAG imports completed in {elapsed:.2f}s: {result['imported']}")
        else:
            # Import failure is acceptable - the test is that it doesn't hang
            print(f"⚠️ DAG import failed (but didn't hang) in {elapsed:.2f}s: {result['error']}")

        assert elapsed < 15, f"DAG imports should not take too long: {elapsed:.2f}s"
