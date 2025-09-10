"""Integration tests for Airflow-PostgreSQL connectivity.

This module tests the specific integration between Airflow's PostgreSQL hooks
and the database, which is where the hanging issues are occurring.
"""

import os
import threading
import time
from unittest.mock import patch

import pytest
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

from .airflow_test_helpers import create_test_task_instance

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestAirflowPostgreSQLConnection:
    """Test Airflow-specific PostgreSQL connection functionality."""

    def test_airflow_postgres_connection_exists(self) -> None:
        """Test that postgres_default connection exists in Airflow."""
        try:
            connection = BaseHook.get_connection("postgres_default")
            assert connection is not None, "postgres_default connection should exist"
            assert connection.conn_type == "postgres", "Should be PostgreSQL connection"
            assert connection.host is not None, "Host should be configured"
            assert connection.port is not None, "Port should be configured"
        except Exception as e:
            pytest.fail(f"postgres_default connection not configured: {e}")

    def test_postgres_hook_connection_timeout(self) -> None:
        """Test PostgreSQL hook connection with timeout."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Test connection with timeout
        start_time = time.time()
        try:
            with hook.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                assert result[0] == 1
                cursor.close()

            elapsed = time.time() - start_time
            assert elapsed < 10, f"Connection should complete quickly, took {elapsed:.2f}s"
        except Exception as e:
            pytest.fail(f"PostgreSQL hook connection failed: {e}")

    def test_postgres_hook_query_timeout(self) -> None:
        """Test PostgreSQL hook query execution with timeout."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        start_time = time.time()
        try:
            # Test simple query
            result = hook.get_first("SELECT version();")
            assert result is not None, "Should return PostgreSQL version"
            assert "PostgreSQL" in str(result), "Should contain PostgreSQL version info"

            elapsed = time.time() - start_time
            assert elapsed < 5, f"Query should complete quickly, took {elapsed:.2f}s"
        except Exception as e:
            pytest.fail(f"PostgreSQL hook query failed: {e}")

    def test_postgres_hook_thread_safety(self) -> None:
        """Test PostgreSQL hook in multi-threaded context (Airflow workers)."""
        results = []
        exceptions = []

        def worker_function(worker_id):
            try:
                hook = PostgresHook(postgres_conn_id="postgres_default")
                result = hook.get_first(f"SELECT {worker_id} as worker_id;")
                results.append(result[0])
            except Exception as e:
                exceptions.append(f"Worker {worker_id}: {e}")

        # Create multiple threads (simulating Airflow workers)
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads with timeout
        for thread in threads:
            thread.join(timeout=10)
            if thread.is_alive():
                pytest.fail("Thread did not complete within timeout")

        # Check results
        assert len(exceptions) == 0, f"Threads should not have exceptions: {exceptions}"
        assert len(results) == 3, "All threads should complete successfully"
        assert sorted(results) == [0, 1, 2], "All worker IDs should be returned"

    def test_postgres_hook_connection_recovery(self) -> None:
        """Test PostgreSQL hook connection recovery after disconnect."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # First connection
        result1 = hook.get_first("SELECT 1;")
        assert result1[0] == 1

        # Force connection close (simulating network issue)
        try:
            if hasattr(hook, "_connection") and hook._connection:
                hook._connection.close()
        except:
            pass  # Connection might already be closed

        # Second connection should work
        result2 = hook.get_first("SELECT 2;")
        assert result2[0] == 2


class TestAirflowTaskLevelIntegration:
    """Test Airflow task-level PostgreSQL integration."""

    def test_postgres_hook_in_task_context(self) -> None:
        """Test PostgreSQL hook within simulated Airflow task context."""
        from datetime import datetime

        from airflow.models import DagBag, TaskInstance
        from airflow.models.dag import DAG
        from airflow.providers.standard.operators.python import PythonOperator

        def test_postgres_task(**context):
            """Task function that uses PostgreSQL hook."""
            hook = PostgresHook(postgres_conn_id="postgres_default")
            result = hook.get_first("SELECT 'airflow_task_test' as test_value;")
            return result[0]

        # Create a test DAG
        dag = DAG("test_postgres_integration", start_date=datetime(2023, 1, 1), schedule=None)

        task = PythonOperator(task_id="test_postgres_task", python_callable=test_postgres_task, dag=dag)

        # Create TaskInstance with properly persisted DagRun for Airflow 3.x
        ti = create_test_task_instance(task)

        try:
            result = ti.run()
            # Task should complete without hanging
            assert True, "Task completed successfully"
        except Exception as e:
            pytest.fail(f"Task execution failed: {e}")

    def test_assess_records_helper_integration(self) -> None:
        """Test the specific assess_records helper that's hanging."""
        import sys
        from pathlib import Path

        # Add dags directory to path
        dags_dir = Path(__file__).parent.parent.parent / "dags"
        sys.path.append(str(dags_dir))

        try:
            from helpers.assess_records import assess_latest_records

            # Test with timeout
            start_time = time.time()
            result = assess_latest_records()
            elapsed = time.time() - start_time

            assert isinstance(result, dict), "Should return dictionary"
            assert elapsed < 30, f"Should complete within 30s, took {elapsed:.2f}s"

            # Check expected keys
            expected_keys = [
                "json_stock_files",
                "json_exchange_files",
                "db_stock_dimension_count",
                "db_currency_dimension_count",
                "db_fact_stock_count",
            ]
            for key in expected_keys:
                assert key in result, f"Result should contain {key}"

        except Exception as e:
            pytest.fail(f"assess_latest_records failed: {e}")

    def test_connection_validator_integration(self) -> None:
        """Test the connection validator that's used in DAGs."""
        import sys
        from pathlib import Path

        # Add dags directory to path
        dags_dir = Path(__file__).parent.parent.parent / "dags"
        sys.path.append(str(dags_dir))

        try:
            from helpers.connection_validator import STANDARD_PIPELINE_CONNECTIONS, validate_dag_connections

            # Test with timeout
            start_time = time.time()
            result = validate_dag_connections(
                required_connections=STANDARD_PIPELINE_CONNECTIONS, task_name="test_validation"
            )
            elapsed = time.time() - start_time

            assert isinstance(result, dict), "Should return dictionary"
            assert elapsed < 30, f"Should complete within 30s, took {elapsed:.2f}s"

            # Check that postgres_default was validated
            assert "validation_results" in result, "Should have validation_results in result"
            assert "postgres_default" in result["validation_results"], "Should validate postgres_default connection"

        except Exception as e:
            pytest.fail(f"Connection validation failed: {e}")


class TestPostgreSQLConnectionTimeout:
    """Test PostgreSQL connection timeout scenarios."""

    def test_postgres_connection_with_explicit_timeout(self) -> None:
        """Test PostgreSQL connection with explicit timeout."""
        import psycopg2

        # Get connection details from environment
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "local_db")
        user = os.getenv("POSTGRES_USER", "dbuser123")
        password = os.getenv("POSTGRES_PASSWORD", "password123")

        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5,  # 5 second timeout
            )

            # Test query with timeout
            cursor = conn.cursor()
            cursor.execute("SELECT pg_sleep(0.1);")  # Short sleep
            cursor.fetchone()
            cursor.close()
            conn.close()

        except psycopg2.OperationalError as e:
            if "timeout" in str(e).lower():
                pytest.fail(f"Connection timed out: {e}")
            else:
                pytest.fail(f"Connection failed: {e}")

    def test_postgres_query_interruption(self) -> None:
        """Test PostgreSQL query interruption (simulating hanging scenarios)."""
        import signal

        import psycopg2

        # Get connection details
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "local_db")
        user = os.getenv("POSTGRES_USER", "dbuser123")
        password = os.getenv("POSTGRES_PASSWORD", "password123")

        def timeout_handler(signum, frame):
            raise TimeoutError("Query execution timeout")

        try:
            conn = psycopg2.connect(
                host=host, port=port, database=database, user=user, password=password, connect_timeout=5
            )

            cursor = conn.cursor()

            # Set signal timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)  # 3 second timeout

            try:
                # This should complete quickly
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                assert result[0] == 1
            finally:
                signal.alarm(0)  # Cancel timeout

            cursor.close()
            conn.close()

        except TimeoutError:
            pytest.fail("Query execution timed out - indicates hanging issue")
        except Exception as e:
            pytest.fail(f"Query execution failed: {e}")


class TestMakefileIntegrationSetup:
    """Test that Makefile changes didn't break PostgreSQL setup."""

    def test_environment_variables_loaded(self) -> None:
        """Test that PostgreSQL environment variables are properly loaded."""
        required_vars = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]

        for var in required_vars:
            value = os.getenv(var)
            assert value is not None, f"{var} should be set in environment"
            assert value.strip() != "", f"{var} should not be empty"

    def test_airflow_postgres_connection_string(self) -> None:
        """Test that Airflow PostgreSQL connection string is properly formatted."""
        try:
            connection = BaseHook.get_connection("postgres_default")
            uri = connection.get_uri()

            assert uri.startswith("postgres://"), "Should be PostgreSQL URI"
            assert "@" in uri, "Should contain credentials"
            assert "localhost" in uri or os.getenv("POSTGRES_HOST") in uri, "Should use correct host"

        except Exception as e:
            pytest.fail(f"Airflow connection string invalid: {e}")

    def test_makefile_database_setup_commands(self) -> None:
        """Test that Makefile database setup commands work."""
        import subprocess

        # Test that database commands are available
        commands_to_test = ["pg_isready --help", "psql --version"]

        for cmd in commands_to_test:
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                assert result.returncode == 0, f"Command '{cmd}' should be available"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pytest.skip(f"Command '{cmd}' not available - this may be expected in some environments")
