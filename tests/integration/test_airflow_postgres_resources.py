"""Integration tests for Airflow 3.x resource management and cleanup.

This module tests resource exhaustion scenarios and cleanup behavior
that can cause hanging in Airflow 3.x PostgreSQL operations.
"""

import gc
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError

import psutil
import psycopg2
import pytest
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestPostgreSQLResourceManagement:
    """Test PostgreSQL resource management in Airflow 3.x context."""

    def test_postgres_hook_memory_usage(self) -> None:
        """Test PostgreSQL hook memory usage patterns."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        hooks = []
        try:
            # Create multiple hooks and monitor memory
            for i in range(20):
                hook = PostgresHook(postgres_conn_id="postgres_default")
                hooks.append(hook)

                # Execute query to establish connection
                result = hook.get_first("SELECT %s;", parameters=(i,))
                assert result[0] == i

                # Check memory usage every 5 iterations
                if i % 5 == 0:
                    current_memory = process.memory_info().rss
                    memory_growth = current_memory - initial_memory

                    # Memory growth should be reasonable (less than 50MB per hook)
                    max_expected_growth = 50 * 1024 * 1024 * (i + 1)  # 50MB per hook
                    assert (
                        memory_growth < max_expected_growth
                    ), f"Excessive memory growth: {memory_growth / 1024 / 1024:.1f}MB after {i+1} hooks"

        finally:
            # Cleanup hooks
            for hook in hooks:
                try:
                    if hasattr(hook, "get_conn"):
                        conn = hook.get_conn()
                        conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

            # Force garbage collection
            gc.collect()

            # Check final memory usage
            time.sleep(2)
            final_memory = process.memory_info().rss
            memory_cleanup = initial_memory - final_memory

            # Memory should be mostly cleaned up (allow 20MB overhead)
            memory_overhead = final_memory - initial_memory
            assert (
                memory_overhead < 20 * 1024 * 1024
            ), f"Memory not cleaned up properly: {memory_overhead / 1024 / 1024:.1f}MB overhead"

    def test_postgres_connection_limit_handling(self) -> None:
        """Test behavior when approaching PostgreSQL connection limits."""
        hooks = []
        connections = []

        try:
            # Create connections until we approach limit
            for i in range(15):  # Conservative number to avoid hitting actual limits
                hook = PostgresHook(postgres_conn_id="postgres_default")
                hooks.append(hook)

                conn = hook.get_conn()
                connections.append(conn)

                # Test connection is working
                cursor = conn.cursor()
                cursor.execute("SELECT %s as connection_num;", (i,))
                result = cursor.fetchone()
                cursor.close()

                assert result[0] == i, f"Connection {i} should work"

                # Check connection count
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND datname = current_database()
                    AND pid != pg_backend_pid();
                """
                )
                active_connections = cursor.fetchone()[0]
                cursor.close()

                # Should not exceed reasonable connection count
                assert active_connections <= 20, f"Too many active connections: {active_connections}"

        finally:
            # Cleanup all connections
            for conn in connections:
                try:
                    conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

    def test_postgres_hook_file_descriptor_usage(self) -> None:
        """Test PostgreSQL hook file descriptor usage."""
        import resource

        # Get initial file descriptor count
        initial_fds = len(os.listdir("/proc/self/fd/")) if os.path.exists("/proc/self/fd/") else 0

        hooks = []
        try:
            # Create multiple hooks
            for i in range(10):
                hook = PostgresHook(postgres_conn_id="postgres_default")
                hooks.append(hook)

                # Use the hook
                result = hook.get_first("SELECT 1;")
                assert result[0] == 1

                # Check file descriptor usage
                if os.path.exists("/proc/self/fd/"):
                    current_fds = len(os.listdir("/proc/self/fd/"))
                    fd_growth = current_fds - initial_fds

                    # File descriptor growth should be reasonable
                    assert fd_growth <= 30, f"Excessive file descriptor usage: {fd_growth} additional FDs"

        finally:
            # Cleanup
            for hook in hooks:
                try:
                    if hasattr(hook, "get_conn"):
                        conn = hook.get_conn()
                        conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

    def test_postgres_hook_long_running_transaction(self) -> None:
        """Test PostgreSQL hook behavior with long-running transactions."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        def long_transaction():
            """Function that holds a long transaction."""
            conn = hook.get_conn()
            cursor = conn.cursor()

            try:
                # Start transaction
                cursor.execute("BEGIN;")

                # Do some work in transaction
                for i in range(5):
                    cursor.execute("SELECT pg_sleep(0.1);")  # 100ms sleep
                    cursor.execute("SELECT %s;", (i,))
                    result = cursor.fetchone()
                    assert result[0] == i

                # Commit transaction
                cursor.execute("COMMIT;")
                return "transaction_completed"

            finally:
                cursor.close()
                conn.close()

        # Execute long transaction with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(long_transaction)

            try:
                result = future.result(timeout=10)
                assert result == "transaction_completed"

            except ConcurrentTimeoutError:
                pytest.fail("Long-running transaction timed out - indicates hanging issue")

    def test_postgres_hook_connection_recovery_after_timeout(self) -> None:
        """Test PostgreSQL hook recovery after connection timeout."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # First, establish connection
        result1 = hook.get_first("SELECT 'initial' as status;")
        assert result1[0] == "initial"

        # Force connection to timeout by closing it
        try:
            conn = hook.get_conn()
            conn.close()
        except (psycopg2.Error, AttributeError):
            # psycopg2.Error for database errors, AttributeError for None connections
            pass

        # Wait a moment
        time.sleep(1)

        # Try to use hook again - should recover
        start_time = time.time()
        try:
            result2 = hook.get_first("SELECT 'recovered' as status;")
            elapsed = time.time() - start_time

            assert result2[0] == "recovered", "Hook should recover after timeout"
            assert elapsed < 10, f"Recovery should be fast, took {elapsed:.2f}s"

        except Exception as e:
            pytest.fail(f"PostgreSQL hook should recover after connection timeout: {e}")


class TestPostgreSQLCleanupBehavior:
    """Test PostgreSQL cleanup behavior in Airflow 3.x."""

    def test_postgres_hook_automatic_cleanup(self) -> None:
        """Test that PostgreSQL hooks clean up automatically."""
        initial_connections = self._count_active_connections()

        # Create hooks in a scope that will be garbage collected
        def create_and_use_hooks():
            hooks = []
            for i in range(5):
                hook = PostgresHook(postgres_conn_id="postgres_default")
                hooks.append(hook)

                result = hook.get_first("SELECT %s;", parameters=(i,))
                assert result[0] == i

            return len(hooks)

        hook_count = create_and_use_hooks()
        assert hook_count == 5

        # Force garbage collection
        gc.collect()
        time.sleep(3)  # Allow time for cleanup

        # Check that connections were cleaned up
        final_connections = self._count_active_connections()
        connection_growth = final_connections - initial_connections

        assert connection_growth <= 1, f"Connections not cleaned up properly: {connection_growth} extra connections"

    def test_postgres_hook_explicit_cleanup(self) -> None:
        """Test explicit PostgreSQL hook cleanup."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Use the hook
        result = hook.get_first("SELECT 'test' as value;")
        assert result[0] == "test"

        # Get connection for explicit cleanup
        conn = hook.get_conn()
        connection_id = id(conn)

        # Explicitly close connection
        conn.close()

        # Verify connection is closed
        assert conn.closed, "Connection should be closed"

        # Hook should still be usable (should create new connection)
        result2 = hook.get_first("SELECT 'after_cleanup' as value;")
        assert result2[0] == "after_cleanup"

        # New connection should have different ID
        new_conn = hook.get_conn()
        new_connection_id = id(new_conn)

        assert new_connection_id != connection_id, "Should create new connection after cleanup"
        new_conn.close()

    def test_postgres_hook_exception_cleanup(self) -> None:
        """Test PostgreSQL hook cleanup after exceptions."""
        hook = PostgresHook(postgres_conn_id="postgres_default")

        initial_connections = self._count_active_connections()

        # Cause an exception during database operation
        try:
            hook.get_first("SELECT 1/0;")  # Division by zero
            pytest.fail("Should raise exception")
        except Exception:
            pass  # Expected

        # Wait for cleanup
        time.sleep(2)

        # Hook should still be usable after exception
        result = hook.get_first("SELECT 'after_exception' as status;")
        assert result[0] == "after_exception"

        # Check connection count hasn't grown significantly
        final_connections = self._count_active_connections()
        connection_growth = final_connections - initial_connections

        assert connection_growth <= 1, f"Exception should not leak connections: {connection_growth} extra connections"

    def test_postgres_hook_context_manager_cleanup(self) -> None:
        """Test PostgreSQL hook cleanup when used as context manager."""
        initial_connections = self._count_active_connections()

        hook = PostgresHook(postgres_conn_id="postgres_default")

        # Use connection as context manager
        with hook.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 'context_manager' as test;")
            result = cursor.fetchone()
            cursor.close()

            assert result[0] == "context_manager"

        # Connection should be automatically closed
        time.sleep(1)

        # Check that connection was cleaned up
        final_connections = self._count_active_connections()
        connection_growth = final_connections - initial_connections

        assert (
            connection_growth <= 0
        ), f"Context manager should clean up connection: {connection_growth} extra connections"

    def _count_active_connections(self) -> int:
        """Helper method to count active PostgreSQL connections."""
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


class TestPostgreSQLStressScenarios:
    """Test PostgreSQL stress scenarios that could cause hanging."""

    def test_postgres_hook_rapid_connection_cycling(self) -> None:
        """Test rapid connection creation and destruction."""
        start_time = time.time()

        try:
            for i in range(50):
                hook = PostgresHook(postgres_conn_id="postgres_default")
                result = hook.get_first("SELECT %s;", parameters=(i,))
                assert result[0] == i

                # Force connection cleanup
                try:
                    conn = hook.get_conn()
                    conn.close()
                except (psycopg2.Error, AttributeError):
                    # psycopg2.Error for database errors, AttributeError for None connections
                    pass

            elapsed = time.time() - start_time

            # Should complete within reasonable time
            assert elapsed < 60, f"Rapid connection cycling took too long: {elapsed:.2f}s"

        except Exception as e:
            pytest.fail(f"Rapid connection cycling failed: {e}")

    def test_postgres_hook_concurrent_stress(self) -> None:
        """Test PostgreSQL hook under concurrent stress."""
        results = []
        exceptions = []

        def stress_worker(worker_id):
            try:
                hook = PostgresHook(postgres_conn_id="postgres_default")

                # Perform multiple operations per worker
                for i in range(10):
                    result = hook.get_first("SELECT %s as worker, %s as iteration;", parameters=(worker_id, i))
                    results.append((worker_id, i, result))

                    # Small delay to simulate real work
                    time.sleep(0.01)

            except Exception as e:
                exceptions.append(f"Worker {worker_id}: {str(e)}")

        # Run multiple workers concurrently
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=stress_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=60)
            if thread.is_alive():
                pytest.fail("Stress test worker did not complete - indicates hanging")

        # Verify results
        assert len(exceptions) == 0, f"Stress test should not have exceptions: {exceptions}"
        assert len(results) == 50, "All stress test operations should complete"  # 5 workers * 10 operations

        # Verify result integrity
        for worker_id, iteration, result in results:
            assert result[0] == worker_id, f"Worker ID mismatch: expected {worker_id}, got {result[0]}"
            assert result[1] == iteration, f"Iteration mismatch: expected {iteration}, got {result[1]}"

    def test_postgres_hook_memory_pressure(self) -> None:
        """Test PostgreSQL hook behavior under memory pressure."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        large_results = []
        try:
            hook = PostgresHook(postgres_conn_id="postgres_default")

            # Generate some memory pressure with large query results
            for i in range(10):
                # Create a query that returns a reasonable amount of data
                result = hook.get_records(
                    """
                    SELECT
                        generate_series(1, 1000) as num,
                        'data_' || generate_series(1, 1000) as text_data,
                        current_timestamp as ts
                    LIMIT 1000;
                """
                )

                large_results.append(len(result))

                # Check memory usage
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory

                # Should not exceed 200MB memory growth
                assert memory_growth < 200 * 1024 * 1024, f"Excessive memory usage: {memory_growth / 1024 / 1024:.1f}MB"

            # Verify all queries returned data
            assert all(
                count == 1000 for count in large_results
            ), "All large queries should return expected number of rows"

        finally:
            # Force cleanup
            large_results.clear()
            gc.collect()
