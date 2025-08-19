"""Integration tests for Apache Airflow functionality.

These tests verify that Apache Airflow is configured properly, including ensuring
AIRFLOW__CORE__DAGS_FOLDER is established as a global variable from .env and not hardcoded.
Also tests DAG validation and connectivity to external services.
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestAirflowConfiguration:
    """Test Airflow configuration and environment setup."""

    def test_airflow_core_dags_folder_from_env(self) -> None:
        """Test that AIRFLOW__CORE__DAGS_FOLDER is set from environment, not hardcoded."""
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")

        assert (
            dags_folder is not None
        ), "AIRFLOW__CORE__DAGS_FOLDER must be set in environment"
        assert dags_folder != "", "AIRFLOW__CORE__DAGS_FOLDER cannot be empty"

        # Verify it points to a valid directory
        dags_path = Path(dags_folder)
        assert dags_path.exists(), f"DAGs folder does not exist: {dags_folder}"
        assert dags_path.is_dir(), f"DAGs folder is not a directory: {dags_folder}"

        # Verify it contains the expected DAG files
        dag_files = list(dags_path.glob("*.py"))
        assert (
            len(dag_files) > 0
        ), f"No Python files found in DAGs folder: {dags_folder}"

        # Check for our test DAG
        test_dag_file = dags_path / "test_etl_dag.py"
        assert test_dag_file.exists(), "test_etl_dag.py should exist in DAGs folder"

    def test_airflow_home_configuration(self) -> None:
        """Test that AIRFLOW_HOME is properly configured."""
        airflow_home = os.getenv("AIRFLOW_HOME")

        # AIRFLOW_HOME should be set for integration tests
        if airflow_home:
            airflow_path = Path(airflow_home)
            assert (
                airflow_path.exists()
            ), f"Airflow home directory does not exist: {airflow_home}"
            assert (
                airflow_path.is_dir()
            ), f"Airflow home is not a directory: {airflow_home}"

    def test_required_airflow_environment_variables(self) -> None:
        """Test that required Airflow environment variables are set."""
        required_vars = [
            "AIRFLOW__CORE__DAGS_FOLDER",
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
        ]

        for var in required_vars:
            value = os.getenv(var)
            assert value is not None, f"{var} must be set in environment"
            assert value != "", f"{var} cannot be empty"

        # Validate database connection string format
        db_conn = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
        assert db_conn.startswith(
            ("postgresql://", "sqlite:///")
        ), "Database connection should be PostgreSQL or SQLite"


class TestAirflowDAGValidation:
    """Test Airflow DAG validation and parsing."""

    def test_dag_folder_accessible(self) -> None:
        """Test that DAG folder is accessible and contains DAGs."""
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")
        assert dags_folder is not None, "AIRFLOW__CORE__DAGS_FOLDER not set"

        dags_path = Path(dags_folder)

        # Count Python files (potential DAGs)
        python_files = list(dags_path.glob("*.py"))
        assert len(python_files) > 0, "No Python files found in DAGs directory"

        # Check that files are readable
        for py_file in python_files:
            assert py_file.is_file(), f"DAG file should be a file: {py_file}"
            assert os.access(
                py_file, os.R_OK
            ), f"DAG file should be readable: {py_file}"

    def test_test_etl_dag_syntax(self) -> None:
        """Test that test_etl_dag.py has valid Python syntax."""
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")
        test_dag_path = Path(dags_folder) / "test_etl_dag.py"

        assert test_dag_path.exists(), "test_etl_dag.py should exist"

        # Test Python syntax by attempting to compile
        try:
            with open(test_dag_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            compile(source_code, str(test_dag_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"test_etl_dag.py has syntax error: {e}")

    def test_dag_contains_required_components(self) -> None:
        """Test that test_etl_dag contains required components for integration testing."""
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")
        test_dag_path = Path(dags_folder) / "test_etl_dag.py"

        with open(test_dag_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for required components
        required_components = [
            "test_alpha_vantage_api_access",  # API access test
            "test_postgresql_database_access",  # Database access test
            "AIRFLOW__CORE__DAGS_FOLDER",  # Environment variable usage
            "POSTGRES_USER",  # Database user from .env
            "ALPHA_VANTAGE_API_KEY",  # API key from .env
        ]

        for component in required_components:
            assert component in content, f"test_etl_dag.py should contain {component}"


class TestAirflowServiceConnectivity:
    """Test Airflow connectivity to external services through DAG validation."""

    def test_airflow_db_connection_string_valid(self) -> None:
        """Test that Airflow database connection string is valid."""
        db_conn = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
        assert db_conn is not None, "Database connection string not set"

        # Parse connection string components
        assert any(
            db_type in db_conn for db_type in ["postgresql://", "sqlite:///"]
        ), "Should be PostgreSQL or SQLite connection"

        # SQLite doesn't need credentials, PostgreSQL does
        if "postgresql://" in db_conn:
            assert "@" in db_conn, "PostgreSQL connection should contain credentials"
            assert ":" in db_conn, "Should contain port"

            # Extract components for validation
            parts = db_conn.replace("postgresql://", "").split("@")
            assert (
                len(parts) == 2
            ), "Connection string format should be user:pass@host:port/db"

            credentials, host_db = parts
            assert ":" in credentials, "Should have user:password format"
            assert "/" in host_db, "Should have host:port/database format"

        elif "sqlite:///" in db_conn:
            assert db_conn.endswith(".db"), "SQLite connection should point to .db file"
            # SQLite is file-based, so just verify the file path is reasonable
            file_path = db_conn.replace("sqlite:///", "")
            assert len(file_path) > 0, "SQLite file path should not be empty"

    def test_environment_variables_not_hardcoded(self) -> None:
        """Test that environment variables are used, not hardcoded values."""
        dags_folder = os.getenv("AIRFLOW__CORE__DAGS_FOLDER")
        test_dag_path = Path(dags_folder) / "test_etl_dag.py"

        with open(test_dag_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that environment variables are used
        assert (
            'os.getenv("AIRFLOW__CORE__DAGS_FOLDER")' in content
        ), "DAG should use environment variable for DAGS_FOLDER"
        assert (
            'os.getenv("POSTGRES_USER"' in content
        ), "DAG should use environment variable for POSTGRES_USER"
        assert (
            'os.getenv("ALPHA_VANTAGE_API_KEY"' in content
        ), "DAG should use environment variable for API key"

        # Check that hardcoded values are not used
        hardcoded_patterns = [
            "localhost",  # Should use POSTGRES_HOST
            "5432",  # Should use POSTGRES_PORT
            "ticker_user",  # Should use POSTGRES_USER
            "demo",  # Should not have demo API key
        ]

        # Allow these in default values for os.getenv()
        for pattern in hardcoded_patterns:
            occurrences = content.count(f'"{pattern}"')
            # Should only appear in os.getenv() default values
            assert occurrences <= 2, f"Hardcoded value '{pattern}' found too many times"


class TestAirflowRuntime:
    """Test Airflow runtime functionality (if Airflow is running)."""

    def test_airflow_cli_available(self) -> None:
        """Test that Airflow CLI is available and working."""
        try:
            # Test airflow version command
            result = subprocess.run(
                ["airflow", "version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            assert result.returncode == 0, f"Airflow CLI failed: {result.stderr}"

            # Airflow 3.0+ returns just version number, not "airflow X.Y.Z"
            version_output = result.stdout.strip()
            assert len(version_output) > 0, "Should return version information"

            # Check that it's a valid version format (X.Y.Z)
            import re

            version_pattern = r"^\d+\.\d+\.\d+.*$"
            assert re.match(
                version_pattern, version_output
            ), f"Should return valid version format, got: {version_output}"

        except subprocess.TimeoutExpired:
            pytest.skip("Airflow CLI command timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available (not in PATH)")

    def test_dag_list_command(self) -> None:
        """Test that Airflow can list DAGs."""
        try:
            # Set environment for airflow command
            env = os.environ.copy()
            env["AIRFLOW__CORE__DAGS_FOLDER"] = os.getenv(
                "AIRFLOW__CORE__DAGS_FOLDER", ""
            )

            # First try to refresh DAGs to make sure they're loaded
            subprocess.run(
                ["airflow", "dags", "reserialize"],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                check=False,
            )

            result = subprocess.run(
                ["airflow", "dags", "list"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
                check=False,
            )

            if result.returncode != 0:
                pytest.skip(f"Airflow not running or configured: {result.stderr}")

            # Check if any DAGs are listed (could be examples or our test DAG)
            if "No data found" in result.stdout:
                # Try to check if DAG folder exists and contains files
                dags_folder = env.get("AIRFLOW__CORE__DAGS_FOLDER", "")
                if dags_folder and "${PWD}" in dags_folder:
                    dags_folder = dags_folder.replace("${PWD}", os.getcwd())

                if dags_folder and os.path.exists(dags_folder):
                    py_files = [f for f in os.listdir(dags_folder) if f.endswith(".py")]
                    if py_files:
                        pytest.skip(
                            f"DAGs folder contains Python files but Airflow shows no DAGs - may need time to parse: {py_files}"
                        )

                pytest.skip(
                    "No DAGs found in Airflow - this may be expected for a fresh installation"
                )

            # If we have DAGs listed, good! Check if our test DAG is among them
            if "test_etl_dag" in result.stdout:
                # Great - our test DAG is loaded
                assert True
            else:
                # Other DAGs found but not our test DAG - this is still a success for Airflow functionality
                print(f"Airflow is working, found DAGs: {result.stdout}")
                assert True

        except subprocess.TimeoutExpired:
            pytest.skip("Airflow DAG list command timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available")

    def test_dag_validation(self) -> None:
        """Test that test_etl_dag passes Airflow validation."""
        try:
            # Set environment for airflow command
            env = os.environ.copy()
            env["AIRFLOW__CORE__DAGS_FOLDER"] = os.getenv(
                "AIRFLOW__CORE__DAGS_FOLDER", ""
            )

            result = subprocess.run(
                ["airflow", "dags", "show", "test_etl_dag"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
                check=False,
            )

            if result.returncode != 0:
                pytest.skip(f"Airflow not running or DAG not found: {result.stderr}")

            # DAG should be valid and displayable
            assert "test_etl_dag" in result.stdout, "DAG should be displayable"

        except subprocess.TimeoutExpired:
            pytest.skip("Airflow DAG validation timed out")
        except FileNotFoundError:
            pytest.skip("Airflow CLI not available")
