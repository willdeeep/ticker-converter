"""Integration tests for specific DAG helper hanging issues.

Tests the exact scenarios where DAG helpers were hanging, focusing on
Airflow-PostgreSQL integration layer problems rather than pure database issues.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import psycopg2
import pytest
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestDAGHelperHangingIssues:
    """Test specific hanging issues identified in DAG helpers."""

    def setup_method(self):
        """Add dags directory to path for importing helpers."""
        self.dags_dir = Path(__file__).parent.parent.parent / "dags"
        if str(self.dags_dir) not in sys.path:
            sys.path.append(str(self.dags_dir))

    def test_assess_records_hanging_prevention(self) -> None:
        """Test that assess_records.py operations do not hang in Airflow context."""
        # Import the helper after adding to path
        from helpers.assess_records import assess_latest_records

        # Test the function with timeout monitoring
        start_time = time.time()

        def run_assess_records():
            """Run assess_records with timeout monitoring."""
            try:
                result = assess_latest_records()
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run in separate thread with timeout
        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_assess_records()))
        thread.start()
        thread.join(timeout=30)  # 30 second timeout

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"assess_records hung after {elapsed:.2f}s - thread still alive")

        assert len(result_container) == 1, "Should have completed"
        result = result_container[0]

        if result["success"]:
            data = result["result"]
            assert isinstance(data, dict), "Should return dictionary"
            assert "json_stock_files" in data, "Should contain file counts"
            print(f"✅ assess_records completed in {elapsed:.2f}s: {data}")
        else:
            # Function may skip database operations to avoid hanging
            print(f"⚠️ assess_records skipped database operations: {result['error']}")
            # This is acceptable as it prevents hanging

    def test_connection_validator_airflow_integration(self) -> None:
        """Test connection_validator.py integration with Airflow hooks."""
        from helpers.connection_validator import STANDARD_PIPELINE_CONNECTIONS, validate_dag_connections

        start_time = time.time()

        def run_validation():
            """Run connection validation with error handling."""
            try:
                result = validate_dag_connections(
                    required_connections=STANDARD_PIPELINE_CONNECTIONS, task_name="integration_test"
                )
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run with timeout
        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_validation()))
        thread.start()
        thread.join(timeout=25)  # 25 second timeout

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"Connection validation hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "Should have completed"
        result = result_container[0]

        assert result["success"], f"Connection validation should succeed: {result.get('error')}"

        validation_data = result["result"]
        assert "validation_results" in validation_data, "Should contain validation results"
        assert "postgres_default" in validation_data["validation_results"], "Should validate postgres_default"

        print(f"✅ Connection validation completed in {elapsed:.2f}s")
        print(f"📊 Summary: {validation_data['summary']}")

    def test_load_raw_to_db_hanging_prevention(self) -> None:
        """Test that load_raw_to_db.py operations do not hang in Airflow context."""
        from helpers.load_raw_to_db import load_raw_to_db

        start_time = time.time()

        def run_load_operation():
            """Run load operation with minimal data to test hanging."""
            try:
                # Use empty directories to test connection logic without actual data
                import tempfile

                with tempfile.TemporaryDirectory() as temp_dir:
                    stocks_dir = Path(temp_dir) / "stocks"
                    exchange_dir = Path(temp_dir) / "exchange"
                    stocks_dir.mkdir()
                    exchange_dir.mkdir()

                    result = load_raw_to_db(data_directory=temp_dir)
                    return {"success": True, "result": result}

            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run with timeout
        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(run_load_operation()))
        thread.start()
        thread.join(timeout=30)  # 30 second timeout

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"load_raw_to_db hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "Should have completed"
        result = result_container[0]

        if result["success"]:
            data = result["result"]
            assert isinstance(data, dict), "Should return dictionary"
            assert "stock_inserted" in data, "Should contain insertion counts"
            print(f"✅ load_raw_to_db completed in {elapsed:.2f}s: {data}")
        else:
            # May fail due to missing database tables, but shouldn't hang
            print(f"⚠️ load_raw_to_db failed (expected in some environments): {result['error']}")


class TestAirflowHookHangingScenarios:
    """Test specific PostgreSQL hook scenarios that can cause hanging."""

    def test_hook_connection_in_task_simulation(self) -> None:
        """Test PostgreSQL hook connection patterns that mirror DAG task execution."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Simulate the exact connection pattern used by DAG helpers
        test_scenarios = [
            {
                "name": "assess_records_pattern",
                "operations": [
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",
                    "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public'",
                ],
            },
            {
                "name": "connection_validator_pattern",
                "operations": [
                    "SELECT version()",
                    "SELECT current_database(), current_user",
                    "SELECT inet_server_addr(), inet_server_port()",
                ],
            },
            {
                "name": "load_raw_pattern",
                "operations": [
                    "BEGIN",
                    "SELECT 1",
                    "COMMIT",
                ],
            },
        ]

        for scenario in test_scenarios:
            start_time = time.time()

            def run_scenario():
                """Run database operations for scenario."""
                try:
                    with hook.get_conn() as conn:
                        cursor = conn.cursor()

                        for operation in scenario["operations"]:
                            cursor.execute(operation)
                            if operation.startswith("SELECT"):
                                cursor.fetchall()  # Consume results

                        cursor.close()

                    return {"success": True, "elapsed": time.time() - start_time}

                except Exception as e:
                    return {"success": False, "error": str(e), "elapsed": time.time() - start_time}

            # Run with timeout
            result_container = []
            thread = threading.Thread(target=lambda: result_container.append(run_scenario()))
            thread.start()
            thread.join(timeout=15)  # 15 second timeout per scenario

            elapsed = time.time() - start_time

            if thread.is_alive():
                pytest.fail(f"{scenario['name']} hung after {elapsed:.2f}s")

            assert len(result_container) == 1, f"Should have completed {scenario['name']}"
            result = result_container[0]

            assert result["success"], f"{scenario['name']} should succeed: {result.get('error')}"
            assert result["elapsed"] < 10, f"{scenario['name']} should complete quickly: {result['elapsed']:.2f}s"

            print(f"✅ {scenario['name']} completed in {result['elapsed']:.2f}s")

    def test_hook_context_switching_hanging(self) -> None:
        """Test hook behavior under rapid context switching (like Airflow task execution)."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        def simulate_task_execution(task_id: int):
            """Simulate rapid Airflow task execution with connection handling."""
            start_time = time.time()
            operations_completed = 0

            try:
                # Simulate multiple quick operations like DAG helpers do
                for i in range(5):
                    # Quick connection operations
                    result = hook.get_first("SELECT 1 as test_value")
                    assert result[0] == 1
                    operations_completed += 1

                    # Small delay to simulate processing
                    time.sleep(0.1)

                elapsed = time.time() - start_time
                return {
                    "task_id": task_id,
                    "success": True,
                    "operations_completed": operations_completed,
                    "elapsed": elapsed,
                }

            except Exception as e:
                elapsed = time.time() - start_time
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e),
                    "operations_completed": operations_completed,
                    "elapsed": elapsed,
                }

        # Run multiple "tasks" concurrently
        results = []
        threads = []

        for task_id in range(3):
            result_container = []
            thread = threading.Thread(target=lambda tid=task_id: result_container.append(simulate_task_execution(tid)))
            threads.append((thread, result_container))
            thread.start()

        # Wait for all threads with timeout
        for thread, result_container in threads:
            thread.join(timeout=20)

            if thread.is_alive():
                pytest.fail("Task simulation hung - thread still alive")

            assert len(result_container) == 1, "Task should have completed"
            result = result_container[0]
            results.append(result)

        # Validate all tasks completed successfully
        failed_tasks = [r for r in results if not r["success"]]
        assert len(failed_tasks) == 0, f"All tasks should succeed: {failed_tasks}"

        # All tasks should complete quickly
        slow_tasks = [r for r in results if r["elapsed"] > 10]
        assert len(slow_tasks) == 0, f"Tasks should complete quickly: {slow_tasks}"

        print("✅ Context switching test passed:")
        for result in results:
            print(f"   • Task {result['task_id']}: {result['operations_completed']} ops in {result['elapsed']:.2f}s")

    def test_hook_signal_handling_integration(self) -> None:
        """Test hook behavior with signal handling (which was causing issues)."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Test the type of operations that were hanging when signal.alarm was used
        operations = [
            ("quick_select", "SELECT 1"),
            ("metadata_query", "SELECT COUNT(*) FROM information_schema.tables"),
            ("version_check", "SELECT version()"),
            ("connection_info", "SELECT current_database(), current_user"),
        ]

        for op_name, query in operations:
            start_time = time.time()

            def run_operation():
                """Run operation without signal handling that was causing issues."""
                try:
                    result = hook.get_first(query)
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            # Run with threading timeout instead of signal.alarm
            result_container = []
            thread = threading.Thread(target=lambda: result_container.append(run_operation()))
            thread.start()
            thread.join(timeout=10)

            elapsed = time.time() - start_time

            if thread.is_alive():
                pytest.fail(f"{op_name} hung after {elapsed:.2f}s")

            assert len(result_container) == 1, f"Should have completed {op_name}"
            result = result_container[0]

            assert result["success"], f"{op_name} should succeed: {result.get('error')}"
            assert elapsed < 5, f"{op_name} should complete quickly: {elapsed:.2f}s"

            print(f"✅ {op_name} completed in {elapsed:.2f}s")


class TestAirflowErrorRecoveryScenarios:
    """Test error recovery scenarios specific to Airflow-PostgreSQL integration."""

    def test_hook_recovery_after_connection_failure(self) -> None:
        """Test PostgreSQL hook recovery after simulated connection failures."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # First, establish a working connection
        result1 = hook.get_first("SELECT 'initial_connection' as status")
        assert result1[0] == "initial_connection"

        # Simulate connection disruption by forcing connection close
        try:
            if hasattr(hook, "_connection") and hook._connection:
                hook._connection.close()
        except (psycopg2.Error, AttributeError):
            # psycopg2.Error for database errors, AttributeError for missing attributes
            pass  # Connection might already be closed

        # Clear any cached connections
        if hasattr(hook, "connection"):
            hook.connection = None

        # Test recovery with timeout
        start_time = time.time()

        def test_recovery():
            """Test connection recovery."""
            try:
                result = hook.get_first("SELECT 'recovered_connection' as status")
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        result_container = []
        thread = threading.Thread(target=lambda: result_container.append(test_recovery()))
        thread.start()
        thread.join(timeout=15)

        elapsed = time.time() - start_time

        if thread.is_alive():
            pytest.fail(f"Connection recovery hung after {elapsed:.2f}s")

        assert len(result_container) == 1, "Recovery should complete"
        result = result_container[0]

        assert result["success"], f"Connection should recover: {result.get('error')}"
        assert result["result"][0] == "recovered_connection", "Should return expected result"

        print(f"✅ Connection recovery test passed in {elapsed:.2f}s")

    def test_airflow_task_retry_simulation(self) -> None:
        """Test behavior during Airflow task retry scenarios."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Simulate multiple task retry attempts
        for attempt in range(3):
            start_time = time.time()

            def simulate_retry_attempt():
                """Simulate task retry with fresh connection."""
                try:
                    # Start with clean slate (simulate Airflow task restart)
                    new_hook = PostgresHook(postgres_conn_id="postgres_default")

                    # Perform typical DAG helper operations
                    table_count = new_hook.get_first(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                    )[0]

                    version_info = new_hook.get_first("SELECT version()")[0]

                    return {
                        "success": True,
                        "table_count": table_count,
                        "has_postgres_version": "PostgreSQL" in str(version_info),
                    }

                except Exception as e:
                    return {"success": False, "error": str(e)}

            result_container = []
            thread = threading.Thread(target=lambda: result_container.append(simulate_retry_attempt()))
            thread.start()
            thread.join(timeout=12)

            elapsed = time.time() - start_time

            if thread.is_alive():
                pytest.fail(f"Task retry attempt {attempt + 1} hung after {elapsed:.2f}s")

            assert len(result_container) == 1, f"Retry attempt {attempt + 1} should complete"
            result = result_container[0]

            assert result["success"], f"Retry attempt {attempt + 1} should succeed: {result.get('error')}"
            assert result["has_postgres_version"], "Should detect PostgreSQL version"

            print(f"✅ Retry attempt {attempt + 1} completed in {elapsed:.2f}s (tables: {result['table_count']})")

            # Small delay between retries
            time.sleep(0.5)


class TestDAGHelperMockingScenarios:
    """Test DAG helpers with mocked scenarios to isolate hanging issues."""

    def setup_method(self):
        """Add dags directory to path for importing helpers."""
        self.dags_dir = Path(__file__).parent.parent.parent / "dags"
        if str(self.dags_dir) not in sys.path:
            sys.path.append(str(self.dags_dir))

    def test_assess_records_with_slow_database(self) -> None:
        """Test assess_records behavior when database is slow (not hanging)."""
        from helpers.assess_records import assess_latest_records

        # Mock PostgresHook to simulate slow but responsive database
        def slow_get_first(query):
            time.sleep(2)  # Simulate slow query
            if "COUNT" in query:
                return (42,)  # Mock count result
            return ("mock_result",)

        with patch("helpers.assess_records.PostgresHook") as mock_hook:
            mock_hook.return_value.get_first = slow_get_first

            start_time = time.time()
            result = assess_latest_records()
            elapsed = time.time() - start_time

            # Should handle slow database gracefully
            assert isinstance(result, dict), "Should return result even with slow database"
            print(f"✅ assess_records handled slow database in {elapsed:.2f}s: {result}")

    def test_connection_validator_with_timeout_simulation(self) -> None:
        """Test connection validator with simulated timeout scenarios."""
        from helpers.connection_validator import validate_dag_connections

        # Mock BaseHook.get_connection to simulate various timeout scenarios
        def mock_get_connection(conn_id):
            if conn_id == "postgres_default":
                # Simulate delay in connection retrieval
                time.sleep(1)

                # Return mock connection object
                class MockConnection:
                    """
                    A mock connection object simulating a PostgreSQL connection for testing purposes.

                    Attributes:
                        conn_type (str): The type of the connection (e.g., "postgres").
                        host (str): The hostname of the database server.
                        port (int): The port number on which the database server is listening.
                        schema (str): The database schema to connect to.
                        login (str): The username used for authentication.

                    Methods:
                        get_uri(): Returns a masked URI string representing the connection.
                    """

                    def __init__(self):
                        self.conn_type = "postgres"
                        self.host = "localhost"
                        self.port = 5432
                        self.schema = "test_db"
                        self.login = "test_user"

                    def get_uri(self):
                        return "postgres://test_user:***@localhost:5432/test_db"

                return MockConnection()
            else:
                raise ValueError(f"Unknown connection: {conn_id}")

        with patch("helpers.connection_validator.BaseHook.get_connection", mock_get_connection):
            start_time = time.time()

            result = validate_dag_connections(required_connections=["postgres_default"], task_name="timeout_test")

            elapsed = time.time() - start_time

            # Should complete even with simulated delays
            assert result["validation_results"]["postgres_default"]["is_valid"], "Should validate successfully"
            assert elapsed < 10, f"Should complete within reasonable time: {elapsed:.2f}s"

            print(f"✅ Connection validation with timeout simulation: {elapsed:.2f}s")
