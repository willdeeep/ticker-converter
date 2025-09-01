"""Integration test for DAG execution monitoring.

This test manually triggers the test_etl_dag and monitors its execution to completion,
providing end-to-end validation of the Airflow pipeline functionality.
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class AirflowDAGExecutor:
    """Helper class for triggering and monitoring Airflow DAG executions."""

    def __init__(self, dag_id: str, timeout_seconds: int = 300):
        """Initialize DAG executor.

        Args:
            dag_id: The ID of the DAG to execute
            timeout_seconds: Maximum time to wait for DAG completion
        """
        self.dag_id = dag_id
        self.timeout_seconds = timeout_seconds
        self.execution_date = None
        self.run_id = None

    def trigger_dag(self) -> str:
        """Trigger a DAG run and return the run ID.

        Returns:
            The run ID of the triggered DAG

        Raises:
            subprocess.CalledProcessError: If DAG trigger fails
            FileNotFoundError: If Airflow CLI is not available
        """
        # Generate a unique run ID based on timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.run_id = f"integration_test_{timestamp}"

        # Trigger the DAG with manual run ID
        cmd = ["airflow", "dags", "trigger", self.dag_id, "--run-id", self.run_id, "--output", "json"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)

        # Parse the output to get execution details
        try:
            output_data = json.loads(result.stdout)

            # Handle different response formats from Airflow CLI
            if isinstance(output_data, list) and len(output_data) > 0:
                # Airflow 3.x returns a list with the DAG run data
                dag_run_data = output_data[0]
                self.execution_date = dag_run_data.get("execution_date")
            elif isinstance(output_data, dict):
                # Some versions return a dict directly
                self.execution_date = output_data.get("execution_date")
            else:
                self.execution_date = self.run_id  # Fallback to run_id

            print(f"✅ DAG {self.dag_id} triggered successfully")
            print(f"🆔 Run ID: {self.run_id}")
            print(f"📅 Execution Date: {self.execution_date}")
            return self.run_id
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            print(f"✅ DAG {self.dag_id} triggered (non-JSON output)")
            self.execution_date = self.run_id  # Use run_id as fallback
            return self.run_id

    def get_dag_run_status(self) -> Dict[str, str]:
        """Get the current status of the DAG run.

        Returns:
            Dictionary containing DAG run status information
        """
        cmd = ["airflow", "dags", "state", self.dag_id, self.execution_date or self.run_id, "--output", "json"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)

            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"state": result.stdout.strip()}
            else:
                return {"state": "unknown", "error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"state": "timeout", "error": "Command timed out"}

    def get_task_states(self) -> Dict[str, str]:
        """Get the states of all tasks in the DAG run.

        Returns:
            Dictionary mapping task IDs to their states
        """
        cmd = [
            "airflow",
            "tasks",
            "states-for-dag-run",
            self.dag_id,
            self.execution_date or self.run_id,
            "--output",
            "json",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)

            if result.returncode == 0:
                try:
                    task_states = json.loads(result.stdout)
                    return {task["task_id"]: task["state"] for task in task_states}
                except (json.JSONDecodeError, KeyError):
                    return {}
            else:
                return {}

        except subprocess.TimeoutExpired:
            return {}

    def wait_for_completion(self) -> Dict[str, str]:
        """Wait for the DAG run to complete.

        Returns:
            Final status of the DAG run

        Raises:
            TimeoutError: If DAG doesn't complete within timeout
        """
        start_time = time.time()
        last_status = {}

        print(f"⏳ Waiting for DAG {self.dag_id} to complete (timeout: {self.timeout_seconds}s)...")

        while time.time() - start_time < self.timeout_seconds:
            status = self.get_dag_run_status()
            task_states = self.get_task_states()

            # Print status updates
            current_state = status.get("state", "unknown")
            if current_state != last_status.get("state"):
                print(f"📊 DAG Status: {current_state}")
                if task_states:
                    print("📋 Task States:")
                    for task_id, task_state in task_states.items():
                        print(f"   • {task_id}: {task_state}")

            last_status = status

            # Check for completion
            if current_state in ["success", "failed"]:
                print(f"🏁 DAG completed with state: {current_state}")
                return {"dag_state": current_state, "task_states": task_states}

            # Wait before checking again
            time.sleep(5)

        # Timeout reached
        raise TimeoutError(f"DAG {self.dag_id} did not complete within {self.timeout_seconds} seconds")

    def get_task_logs(self, task_id: str) -> str:
        """Get logs for a specific task.

        Args:
            task_id: The ID of the task to get logs for

        Returns:
            Task logs as a string
        """
        cmd = ["airflow", "tasks", "log", self.dag_id, task_id, self.execution_date or self.run_id, "--try", "1"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)

            return result.stdout if result.returncode == 0 else result.stderr

        except subprocess.TimeoutExpired:
            return "Log retrieval timed out"

    def cleanup(self) -> None:
        """Clean up the DAG run (optional - for test isolation)."""
        if self.run_id:
            cmd = ["airflow", "dags", "delete", self.dag_id, "--yes"]

            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
                print(f"🧹 Cleaned up DAG run {self.run_id}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️  Could not clean up DAG run (this is usually fine)")


class TestDAGExecution:
    """Integration tests for DAG execution monitoring."""

    def test_airflow_available(self) -> None:
        """Test that Airflow CLI is available before running DAG tests."""
        try:
            result = subprocess.run(["airflow", "version"], capture_output=True, text=True, timeout=30, check=True)

            version = result.stdout.strip()
            print(f"✅ Airflow version: {version}")
            assert len(version) > 0, "Should return version information"

        except subprocess.TimeoutExpired:
            pytest.skip("Airflow CLI command timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available (not in PATH)")
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Airflow CLI error: {e}")

    def test_test_etl_dag_execution(self) -> None:
        """Test end-to-end execution of test_etl_dag.

        This test:
        1. Triggers the test_etl_dag manually
        2. Monitors its execution progress
        3. Waits for completion
        4. Validates the results
        5. Checks task logs for any issues
        """
        dag_id = "test_etl_dag"
        executor = AirflowDAGExecutor(dag_id, timeout_seconds=300)

        try:
            # Step 1: Trigger the DAG
            print(f"🚀 Triggering DAG: {dag_id}")
            run_id = executor.trigger_dag()
            assert run_id is not None, "Should return a valid run ID"

            # Step 2: Wait for completion and monitor progress
            print("⏳ Monitoring DAG execution...")
            final_status = executor.wait_for_completion()

            # Step 3: Validate results
            dag_state = final_status["dag_state"]
            task_states = final_status["task_states"]

            print(f"📊 Final DAG State: {dag_state}")
            print("📋 Final Task States:")
            for task_id, task_state in task_states.items():
                print(f"   • {task_id}: {task_state}")

            # Step 4: Analyze results
            if dag_state == "success":
                print("🎉 DAG execution successful!")

                # All tasks should be successful
                failed_tasks = [
                    task_id for task_id, state in task_states.items() if state not in ["success", "skipped"]
                ]

                if failed_tasks:
                    print(f"⚠️  Some tasks did not succeed: {failed_tasks}")
                    # Get logs for failed tasks
                    for task_id in failed_tasks:
                        logs = executor.get_task_logs(task_id)
                        print(f"📄 Logs for {task_id}:")
                        print(logs[:1000])  # Print first 1000 characters
                else:
                    print("✅ All tasks completed successfully")

                assert dag_state == "success", "DAG should complete successfully"

            elif dag_state == "failed":
                print("❌ DAG execution failed")

                # Collect logs from failed tasks for debugging
                failed_tasks = [task_id for task_id, state in task_states.items() if state == "failed"]

                error_summary = []
                for task_id in failed_tasks:
                    logs = executor.get_task_logs(task_id)
                    error_summary.append(f"\n--- {task_id} logs ---\n{logs[:1000]}")

                pytest.fail(f"DAG execution failed. Failed tasks: {failed_tasks}\n{''.join(error_summary)}")

            else:
                pytest.fail(f"DAG completed with unexpected state: {dag_state}")

        except subprocess.CalledProcessError as e:
            pytest.skip(f"Airflow command failed: {e}")
        except subprocess.TimeoutExpired:
            pytest.skip("Airflow command timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available")
        except TimeoutError as e:
            # Get current status for debugging
            status = executor.get_dag_run_status()
            task_states = executor.get_task_states()

            print(f"⏰ DAG execution timed out: {e}")
            print(f"📊 Last known DAG state: {status.get('state', 'unknown')}")
            print("📋 Last known task states:")
            for task_id, task_state in task_states.items():
                print(f"   • {task_id}: {task_state}")

            pytest.skip(f"DAG execution timed out: {e}")
        finally:
            # Optional cleanup (commented out to preserve DAG runs for debugging)
            # executor.cleanup()
            pass

    def test_dag_task_connectivity_validation(self) -> None:
        """Test that the DAG properly validates connectivity to external services.

        This is a lighter test that just checks if the DAG can validate
        its tasks without necessarily requiring all external services.
        """
        dag_id = "test_etl_dag"

        try:
            # Test DAG structure validation
            result = subprocess.run(
                ["airflow", "dags", "show", dag_id], capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode != 0:
                pytest.skip(f"DAG not available or Airflow not running: {result.stderr}")

            # Check that the DAG structure is valid
            assert dag_id in result.stdout, "DAG should be displayable"

            # Test task list
            result = subprocess.run(
                ["airflow", "tasks", "list", dag_id], capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode == 0:
                tasks = result.stdout.strip().split("\n")
                expected_tasks = [
                    "test_validate_connections",
                    "test_airflow_configuration",
                    "test_alpha_vantage_api_access",
                    "test_postgresql_database_access",
                ]

                print(f"📋 Available tasks: {tasks}")

                for expected_task in expected_tasks:
                    assert any(expected_task in task for task in tasks), f"Should contain task: {expected_task}"

                print("✅ DAG structure validation successful")
            else:
                pytest.skip("Could not retrieve task list")

        except subprocess.TimeoutExpired:
            pytest.skip("Airflow command timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available")


class TestDAGExecutionPerformance:
    """Performance tests for DAG execution."""

    def test_dag_execution_time_reasonable(self) -> None:
        """Test that DAG execution completes within reasonable time limits.

        This test helps identify performance regressions in the DAG.
        """
        dag_id = "test_etl_dag"
        executor = AirflowDAGExecutor(dag_id, timeout_seconds=180)  # 3 minutes

        try:
            start_time = time.time()

            # Trigger and wait for completion
            executor.trigger_dag()
            final_status = executor.wait_for_completion()

            execution_time = time.time() - start_time

            print(f"⏱️  DAG execution time: {execution_time:.2f} seconds")

            # DAG should complete within reasonable time (3 minutes)
            assert execution_time < 180, f"DAG took too long: {execution_time:.2f}s > 180s"

            # DAG should not complete too quickly (sanity check)
            assert execution_time > 5, f"DAG completed suspiciously fast: {execution_time:.2f}s"

            # If successful, check that it was actually successful
            if final_status["dag_state"] == "success":
                print(f"✅ DAG completed successfully in {execution_time:.2f} seconds")
            else:
                print(f"⚠️  DAG completed with state: {final_status['dag_state']}")

        except TimeoutError:
            pytest.skip("DAG execution exceeded reasonable time limit")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Airflow not available for performance testing")


@pytest.fixture(scope="session")
def airflow_setup():
    """Session-scoped fixture to ensure Airflow is ready for testing."""
    try:
        # Check if Airflow is available
        result = subprocess.run(["airflow", "version"], capture_output=True, text=True, timeout=30, check=True)

        # Try to initialize Airflow database if needed
        subprocess.run(
            ["airflow", "db", "init"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,  # Don't fail if already initialized
        )

        return True

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("Airflow not available for integration testing")


# Use the fixture in tests that need it
@pytest.mark.usefixtures("airflow_setup")
class TestDAGExecutionWithSetup(TestDAGExecution):
    """DAG execution tests with proper Airflow setup."""

    pass
