"""Integration tests specifically targeting Airflow 3.x PostgreSQL hanging issues.

This module tests the specific hanging issues mentioned in dags/helpers/assess_records.py
and connection management problems that occur during Airflow task execution.
"""

import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError
from unittest.mock import patch

import psycopg2
import pytest
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestAirflowPostgresHanging:
    """Test Airflow 3.x specific PostgreSQL hanging scenarios."""

    def test_postgres_hook_connection_pool_exhaustion(self) -> None:
        """Test connection pool exhaustion that causes hanging in Airflow tasks."""
        hooks = []
        connections = []

        try:
            # Create multiple hooks to test pool exhaustion
            for i in range(10):
                hook = PostgresHook(postgres_conn_id="postgres_default")
                hooks.append(hook)

                # Get connection but do not immediately close
                conn = hook.get_conn()
                connections.append(conn)

                # Quick test query
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                assert result[0] == 1
                cursor.close()

            # All connections should work without hanging
            assert len(connections) == 10, "Should create 10 connections"

        finally:
            # Clean up connections
            for conn in connections:
                try:
                    conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

    def test_postgres_hook_with_task_timeout(self) -> None:
        """Test PostgreSQL hook operations with realistic task timeouts."""

        def run_postgres_operation():
            """Simulate the assess_records operation that hangs."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Test the specific queries from assess_records that hang
            queries = [
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'stock_dimension';",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'currency_dimension';",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fact_stock';",
            ]

            results = []
            for query in queries:
                result = hook.get_first(query)
                results.append(result[0] if result else 0)

            return results

        # Use ThreadPoolExecutor with timeout to detect hanging
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_postgres_operation)

            try:
                # 30 second timeout - operation should complete much faster
                results = future.result(timeout=30)
                assert len(results) == 3, "Should return 3 query results"
                assert all(isinstance(r, int) for r in results), "All results should be integers"

            except ConcurrentTimeoutError:
                pytest.fail("PostgreSQL operations timed out - indicates hanging issue in Airflow 3.x")

    def test_postgres_hook_connection_cleanup(self) -> None:
        """Test that PostgreSQL hook properly cleans up connections."""
        initial_connections = self._count_active_connections()

        # Create and use multiple hooks
        for i in range(5):
            hook = PostgresHook(postgres_conn_id="postgres_default")
            result = hook.get_first("SELECT %s;", parameters=(i,))
            assert result[0] == i

            # Force connection cleanup
            if hasattr(hook, "get_conn"):
                try:
                    conn = hook.get_conn()
                    conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

        # Wait for cleanup
        time.sleep(2)

        final_connections = self._count_active_connections()

        # Should not have significantly more connections
        connection_diff = final_connections - initial_connections
        assert connection_diff <= 2, f"Too many lingering connections: {connection_diff}"

    def test_postgres_hook_signal_interruption(self) -> None:
        """Test PostgreSQL hook behavior with signal interruption (common in Airflow)."""

        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")

        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Set up signal handler for timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)

        try:
            signal.alarm(5)  # 5 second timeout

            # This should complete quickly
            result = hook.get_first("SELECT pg_sleep(0.1);")  # 100ms sleep

            signal.alarm(0)  # Cancel alarm
            assert result is not None, "Query should complete successfully"

        except TimeoutError:
            pytest.fail("PostgreSQL operation was interrupted by signal - indicates hanging")
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def test_assess_records_hanging_scenario(self) -> None:
        """Test the specific assess_records function that's commented out due to hanging."""
        import sys
        from pathlib import Path

        # Add dags directory to path
        dags_dir = Path(__file__).parent.parent.parent / "dags"
        sys.path.append(str(dags_dir))

        from helpers.assess_records import assess_latest_records

        # Test with timeout to catch hanging
        def run_assess_records():
            return assess_latest_records()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_assess_records)

            try:
                result = future.result(timeout=45)  # 45 second timeout

                # Verify the function returns expected structure
                assert isinstance(result, dict), "Should return dictionary"
                expected_keys = [
                    "json_stock_files",
                    "json_exchange_files",
                    "db_stock_dimension_count",
                    "db_currency_dimension_count",
                    "db_fact_stock_count",
                ]
                for key in expected_keys:
                    assert key in result, f"Should contain {key}"

            except ConcurrentTimeoutError:
                pytest.fail("assess_latest_records() timed out - confirms hanging issue exists")

    def test_postgres_hook_concurrent_access(self) -> None:
        """Test concurrent PostgreSQL hook access (simulating multiple Airflow workers)."""
        results = []
        exceptions = []

        def worker_task(worker_id):
            try:
                hook = PostgresHook(postgres_conn_id="postgres_default")

                # Simulate the type of queries used in DAG helpers
                queries = [
                    f"SELECT {worker_id} as id, 'worker' as type;",
                    "SELECT COUNT(*) FROM information_schema.tables;",
                    f"SELECT pg_sleep(0.1), {worker_id};",  # Small delay to test concurrency
                ]

                worker_results = []
                for query in queries:
                    result = hook.get_first(query)
                    worker_results.append(result)

                results.append((worker_id, worker_results))

            except Exception as e:
                exceptions.append(f"Worker {worker_id}: {str(e)}")

        # Run concurrent workers
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_task, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=30)
            if thread.is_alive():
                pytest.fail("Worker thread did not complete - indicates hanging issue")

        # Verify results
        assert len(exceptions) == 0, f"Workers should not have exceptions: {exceptions}"
        assert len(results) == 3, "All workers should complete"

        # Verify each worker got expected results
        for worker_id, worker_results in results:
            assert len(worker_results) == 3, f"Worker {worker_id} should have 3 results"
            assert worker_results[0][0] == worker_id, f"Worker {worker_id} ID mismatch"

    def _count_active_connections(self) -> int:
        """Count active PostgreSQL connections (helper method)."""
        try:
            hook = PostgresHook(postgres_conn_id="postgres_default")
            result = hook.get_first(
                """
                SELECT count(*)
                FROM pg_stat_activity
                WHERE state = 'active'
                AND datname = current_database()
                AND pid != pg_backend_pid();
            """
            )
            return result[0] if result else 0
        except (psycopg2.Error, AirflowException):
            return 0


class TestAirflowConnectionManagement:
    """Test Airflow 3.x connection management specific issues."""

    def test_connection_validator_timeout_behavior(self) -> None:
        """Test connection validator doesn't hang during validation."""
        import sys
        from pathlib import Path

        dags_dir = Path(__file__).parent.parent.parent / "dags"
        sys.path.append(str(dags_dir))

        from helpers.connection_validator import STANDARD_PIPELINE_CONNECTIONS, validate_dag_connections

        def run_validation():
            return validate_dag_connections(
                required_connections=STANDARD_PIPELINE_CONNECTIONS, task_name="test_hanging_validation"
            )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_validation)

            try:
                result = future.result(timeout=30)

                assert isinstance(result, dict), "Should return validation results"
                assert "validation_results" in result, "Should contain validation results"
                assert "summary" in result, "Should contain summary"

                # Verify postgres_default was validated
                validation_results = result["validation_results"]
                assert "postgres_default" in validation_results, "Should validate postgres_default"

            except ConcurrentTimeoutError:
                pytest.fail("Connection validation timed out - indicates hanging issue")

    def test_base_hook_get_connection_timeout(self) -> None:
        """Test BaseHook.get_connection doesn't hang in Airflow 3.x."""

        def get_connection_info():
            try:
                connection = BaseHook.get_connection("postgres_default")
                return {
                    "conn_type": connection.conn_type,
                    "host": connection.host,
                    "port": connection.port,
                    "schema": connection.schema,
                    "login": connection.login,
                    "uri_length": len(connection.get_uri()) if connection.get_uri() else 0,
                }
            except Exception as e:
                return {"error": str(e)}

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_connection_info)

            try:
                result = future.result(timeout=10)

                if "error" in result:
                    pytest.fail(f"Connection retrieval failed: {result['error']}")

                assert result["conn_type"] == "postgres", "Should be PostgreSQL connection"
                assert result["host"] is not None, "Should have host configured"
                assert result["uri_length"] > 0, "Should have valid URI"

            except ConcurrentTimeoutError:
                pytest.fail("BaseHook.get_connection() timed out - indicates hanging issue")

    def test_postgres_hook_with_airflow_context(self) -> None:
        """Test PostgreSQL hook within Airflow 3.x task context simulation."""
        from datetime import datetime
        from unittest.mock import MagicMock

        # Simulate Airflow 3.x task context
        mock_context = {
            "dag": MagicMock(),
            "task": MagicMock(),
            "execution_date": datetime.now(),
            "task_instance": MagicMock(),
            "run_id": "test_run_001",
        }

        def task_with_postgres_hook(**context):
            """Simulate task function using PostgreSQL hook."""
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Test operations that were hanging in assess_records
            queries = [
                "SELECT current_database();",
                "SELECT current_user;",
                "SELECT version();",
                "SELECT COUNT(*) FROM information_schema.tables;",
            ]

            results = []
            for query in queries:
                result = hook.get_first(query)
                results.append(result[0] if result else None)

            return results

        # Execute with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(task_with_postgres_hook, **mock_context)

            try:
                results = future.result(timeout=20)

                assert len(results) == 4, "Should execute all 4 queries"
                assert all(r is not None for r in results), "All queries should return results"
                assert isinstance(results[3], int), "Table count should be integer"

            except ConcurrentTimeoutError:
                pytest.fail("PostgreSQL hook in task context timed out - indicates hanging issue")


class TestAirflowPostgresErrorHandling:
    """Test error handling scenarios that might cause hanging."""

    def test_postgres_hook_invalid_query_recovery(self) -> None:
        """Test PostgreSQL hook recovery after invalid query."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # First, execute invalid query
        try:
            hook.get_first("SELECT FROM invalid_syntax;")
            pytest.fail("Invalid query should raise exception")
        except Exception:
            pass  # Expected

        # Then execute valid query - should not hang
        start_time = time.time()
        try:
            result = hook.get_first("SELECT 1;")
            elapsed = time.time() - start_time

            assert result[0] == 1, "Valid query should work after invalid query"
            assert elapsed < 5, f"Recovery should be fast, took {elapsed:.2f}s"

        except Exception as e:
            pytest.fail(f"PostgreSQL hook should recover after invalid query: {e}")

    def test_postgres_hook_connection_interruption(self) -> None:
        """Test PostgreSQL hook behavior when connection is interrupted."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Get connection and close it forcefully
        conn = hook.get_conn()
        original_closed = conn.closed

        try:
            # Force close connection
            conn.close()
            assert conn.closed != original_closed, "Connection should be closed"

            # Try to use hook again - should reconnect without hanging
            start_time = time.time()
            result = hook.get_first("SELECT 2;")
            elapsed = time.time() - start_time

            assert result[0] == 2, "Hook should reconnect successfully"
            assert elapsed < 10, f"Reconnection should be fast, took {elapsed:.2f}s"

        except Exception as e:
            pytest.fail(f"PostgreSQL hook should handle connection interruption: {e}")

    def test_postgres_hook_database_not_exist_timeout(self) -> None:
        """Test PostgreSQL hook timeout when database doesn't exist."""
        from airflow.models import Connection

        from airflow import settings

        # Create a connection to a non-existent database
        session = settings.Session()
        try:
            start_time = time.time()

            # Create temporary connection to non-existent database
            temp_conn = Connection(
                conn_id="temp_nonexistent_db",
                conn_type="postgres",
                host="localhost",
                login="postgres",
                password="postgres",
                schema="nonexistent_database_12345",
            )
            session.add(temp_conn)
            session.commit()

            try:
                hook = PostgresHook(postgres_conn_id="temp_nonexistent_db")
                hook.get_first("SELECT 1;")
                pytest.fail("Query to non-existent database should fail")
            except Exception as e:
                # Expected failure - check it happens quickly
                elapsed = time.time() - start_time
                assert elapsed < 10, f"Should fail quickly, took {elapsed:.2f}s"
                # Should get database connection error, not timeout
                assert (
                    "database" in str(e).lower() or "does not exist" in str(e).lower() or "fatal" in str(e).lower()
                ), f"Should be database error: {e}"

        finally:
            # Clean up temporary connection
            try:
                session.delete(temp_conn)
                session.commit()
            except:
                pass
            session.close()
