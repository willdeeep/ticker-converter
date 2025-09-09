"""Integration tests for Airflow PostgreSQL connection pool management.

Tests connection pool exhaustion scenarios that can cause hanging in Airflow tasks.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import psycopg2
import pytest
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestAirflowConnectionPool:
    """Test Airflow-specific connection pool behavior."""

    def test_connection_pool_concurrent_access(self) -> None:
        """Test connection pool under concurrent access from multiple tasks."""
        hook = PostgresHook(postgres_conn_id="postgres_default")
        results = []
        exceptions = []

        def simulate_airflow_task(task_id: int):
            """Simulate an Airflow task accessing PostgreSQL."""
            try:
                # Simulate typical DAG helper behavior
                with hook.get_conn() as conn:
                    cursor = conn.cursor()

                    # Simulate assess_records.py database queries
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
                    table_count = cursor.fetchone()[0]

                    # Simulate connection_validator.py connection test
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]

                    # Simulate load_raw_to_db.py transaction
                    cursor.execute("BEGIN;")
                    cursor.execute("SELECT 1;")
                    cursor.execute("COMMIT;")

                    cursor.close()

                    results.append(
                        {"task_id": task_id, "table_count": table_count, "version_info": "PostgreSQL" in str(version)}
                    )

            except (psycopg2.Error, AirflowException) as e:
                exceptions.append(f"Task {task_id}: {str(e)}")

        # Run 10 concurrent "tasks" (simulating Airflow parallel execution)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_airflow_task, i) for i in range(10)]

            # Wait for all with timeout
            for future in as_completed(futures, timeout=30):
                future.result()  # Raise any exceptions

        # Validate results
        assert len(exceptions) == 0, f"Tasks should not have exceptions: {exceptions}"
        assert len(results) == 10, "All tasks should complete successfully"

        print(f"✅ Connection pool test completed: {len(results)} tasks succeeded")

    def test_connection_pool_exhaustion_recovery(self) -> None:
        """Test recovery from connection pool exhaustion."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Create many connections to exhaust pool
        connections = []
        try:
            # Try to create more connections than typical pool size
            for _ in range(15):
                conn = hook.get_conn()
                connections.append(conn)

        except (psycopg2.OperationalError, psycopg2.DatabaseError, AirflowException) as e:
            print(f"Expected pool exhaustion at connection {len(connections)}: {e}")

        # Clean up connections
        for conn in connections:
            try:
                conn.close()
            except (psycopg2.Error, AttributeError):
                # psycopg2.Error for database errors, AttributeError for None connections
                pass

        # Wait for pool cleanup
        time.sleep(2)

        # Test that new connections work after cleanup
        result = hook.get_first("SELECT 'pool_recovered' as status;")
        assert result[0] == "pool_recovered", "Pool should recover after connection cleanup"

    def test_connection_timeout_in_task_context(self) -> None:
        """Test connection timeout behavior in Airflow task context."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        start_time = time.time()

        try:
            # Test connection with realistic Airflow task operations
            with hook.get_conn() as conn:
                cursor = conn.cursor()

                # These queries simulate the hanging scenarios in DAG helpers

                # 1. Information schema query (assess_records.py)
                cursor.execute(
                    """
                    SELECT schemaname, relname as tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public';
                """
                )
                stats = cursor.fetchall()

                # 2. Connection validation query (connection_validator.py)
                cursor.execute("SELECT current_database(), current_user, version();")
                db_info = cursor.fetchone()

                # 3. Transaction simulation (load_raw_to_db.py)
                cursor.execute("BEGIN;")
                cursor.execute("SELECT NOW();")
                cursor.execute("COMMIT;")

                cursor.close()

            elapsed = time.time() - start_time
            assert elapsed < 15, f"Operations should complete quickly, took {elapsed:.2f}s"

            print(f"✅ Task-level operations completed in {elapsed:.2f}s")
            print(f"📊 Found {len(stats)} user tables")
            print(f"🔗 Connected to database: {db_info[0]} as {db_info[1]}")

        except (psycopg2.Error, AirflowException, TimeoutError) as e:
            elapsed = time.time() - start_time
            pytest.fail(f"Task-level operations failed after {elapsed:.2f}s: {e}")


class TestAirflowTransactionManagement:
    """Test Airflow PostgreSQL transaction management issues."""

    def test_transaction_deadlock_handling(self) -> None:
        """Test handling of potential transaction deadlocks in Airflow tasks."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        def task_with_transaction(task_id: int, delay: float):
            """Simulate Airflow task with database transaction."""
            with hook.get_conn() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("BEGIN;")

                    # Simulate table access patterns from DAG helpers
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables;")

                    # Add delay to increase chance of contention
                    time.sleep(delay)

                    cursor.execute("SELECT pg_backend_pid();")
                    pid = cursor.fetchone()[0]

                    cursor.execute("COMMIT;")
                    cursor.close()

                    return f"Task {task_id} completed with PID {pid}"

                except (psycopg2.Error, AirflowException) as e:
                    cursor.execute("ROLLBACK;")
                    cursor.close()
                    raise e

        # Run concurrent transactions
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(task_with_transaction, i, 0.1) for i in range(3)]

            results = []
            for future in as_completed(futures, timeout=20):
                results.append(future.result())

        assert len(results) == 3, "All transactions should complete without deadlock"
        print(f"✅ Transaction deadlock test passed: {results}")

    def test_long_running_query_interruption(self) -> None:
        """Test interruption of long-running queries (simulating hanging scenarios)."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        def run_query_with_timeout():
            """Run a query that could potentially hang."""
            start_time = time.time()

            try:
                # This simulates the queries that were hanging in assess_records.py
                result = hook.get_first(
                    """
                    SELECT
                        COUNT(*) as total_tables,
                        (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public') as total_columns
                    FROM information_schema.tables
                    WHERE table_schema = 'public';
                """
                )

                elapsed = time.time() - start_time
                return {"success": True, "elapsed": elapsed, "result": result}

            except (psycopg2.Error, AirflowException, TimeoutError) as e:
                elapsed = time.time() - start_time
                return {"success": False, "elapsed": elapsed, "error": str(e)}

        # Run with timeout in separate thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_query_with_timeout)

            try:
                result = future.result(timeout=10)  # 10 second timeout

                if result["success"]:
                    print(f"✅ Query completed in {result['elapsed']:.2f}s: {result['result']}")
                    assert result["elapsed"] < 5, "Query should complete quickly"
                else:
                    pytest.fail(f"Query failed: {result['error']}")

            except TimeoutError:
                pytest.fail("Query timed out - indicates hanging issue")


class TestAirflowConnectionLeaks:
    """Test for connection leaks in Airflow PostgreSQL hooks."""

    def test_connection_cleanup_after_task_failure(self) -> None:
        """Test that connections are properly cleaned up after task failures."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Get initial connection count
        initial_connections = self._get_active_connections(hook)

        # Simulate failed tasks that might leak connections
        for i in range(5):
            try:
                conn = hook.get_conn()
                cursor = conn.cursor()

                # Simulate task work
                cursor.execute("SELECT 1;")

                # Simulate random failure (do not clean up properly)
                if i % 2 == 0:
                    raise RuntimeError(f"Simulated task failure {i}")
                else:
                    cursor.close()
                    conn.close()

            except (RuntimeError, psycopg2.Error, AirflowException):
                # Simulate Airflow task failure without proper cleanup
                pass

        # Wait for cleanup
        time.sleep(2)

        # Check for connection leaks
        final_connections = self._get_active_connections(hook)

        # Allow some variance but shouldn't grow significantly
        connection_growth = final_connections - initial_connections
        assert connection_growth <= 2, f"Too many leaked connections: {connection_growth}"

        print(f"✅ Connection leak test: {initial_connections} -> {final_connections} (growth: {connection_growth})")

    def _get_active_connections(self, hook: PostgresHook) -> int:
        """Get count of active database connections."""
        try:
            result = hook.get_first(
                """
                SELECT COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND state = 'active';
            """
            )
            return result[0] if result else 0
        except (psycopg2.Error, AirflowException):
            return 0


class TestDAGHelperSpecificIssues:
    """Test specific issues found in DAG helpers."""

    def test_assess_records_database_queries(self) -> None:
        """Test the specific database queries from assess_records.py that were hanging."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # These are the queries that were commented out due to hanging
        queries = [
            (
                "stock_dimension_count",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE '%stock%';",
            ),
            (
                "currency_dimension_count",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE '%currency%';",
            ),
            ("fact_stock_count", "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE '%fact%';"),
        ]

        results = {}

        for query_name, query in queries:
            start_time = time.time()
            try:
                result = hook.get_first(query)
                elapsed = time.time() - start_time

                results[query_name] = {"success": True, "value": result[0] if result else 0, "elapsed": elapsed}

                # These queries should complete quickly
                assert elapsed < 5, f"{query_name} took too long: {elapsed:.2f}s"

            except (psycopg2.Error, AirflowException, TimeoutError) as e:
                elapsed = time.time() - start_time
                results[query_name] = {"success": False, "error": str(e), "elapsed": elapsed}

        # All queries should succeed
        failed_queries = [name for name, result in results.items() if not result["success"]]
        assert len(failed_queries) == 0, f"Queries should not fail: {failed_queries}"

        print("✅ assess_records database queries test passed:")
        for name, result in results.items():
            print(f"   • {name}: {result['value']} (elapsed: {result['elapsed']:.2f}s)")

    def test_connection_validator_timeout_behavior(self) -> None:
        """Test connection validator behavior under timeout conditions."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Simulate the connection validation logic from connection_validator.py
        start_time = time.time()

        try:
            # Test connection retrieval (without signal.alarm which can hang)
            conn = hook.get_conn()

            # Test basic connectivity
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

            # Test connection details extraction
            cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
            details = cursor.fetchone()

            cursor.close()
            conn.close()

            elapsed = time.time() - start_time

            assert result[0] == 1, "Basic connectivity test should pass"
            assert details[0] is not None, "Should retrieve database name"
            assert elapsed < 10, f"Connection validation should complete quickly, took {elapsed:.2f}s"

            print(f"✅ Connection validation completed in {elapsed:.2f}s")
            print(f"🔗 Database: {details[0]}, User: {details[1]}")

        except (psycopg2.Error, AirflowException, TimeoutError) as e:
            elapsed = time.time() - start_time
            pytest.fail(f"Connection validation failed after {elapsed:.2f}s: {e}")

    def test_load_raw_to_db_transaction_behavior(self) -> None:
        """Test transaction behavior from load_raw_to_db.py under various conditions."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        test_scenarios = [
            ("quick_transaction", "BEGIN; SELECT 1; COMMIT;"),
            ("rollback_transaction", "BEGIN; SELECT 1; ROLLBACK;"),
            (
                "metadata_query",
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;",
            ),
        ]

        for scenario_name, query in test_scenarios:
            start_time = time.time()

            try:
                if ";" in query and ("BEGIN" in query or "COMMIT" in query or "ROLLBACK" in query):
                    # Handle multi-statement transactions
                    with hook.get_conn() as conn:
                        cursor = conn.cursor()
                        for statement in query.split(";"):
                            if statement.strip():
                                cursor.execute(statement.strip())
                        cursor.close()
                else:
                    # Single query
                    result = hook.get_records(query)

                elapsed = time.time() - start_time
                assert elapsed < 5, f"{scenario_name} should complete quickly, took {elapsed:.2f}s"

                print(f"✅ {scenario_name} completed in {elapsed:.2f}s")

            except (psycopg2.Error, AirflowException, TimeoutError) as e:
                elapsed = time.time() - start_time
                pytest.fail(f"{scenario_name} failed after {elapsed:.2f}s: {e}")
