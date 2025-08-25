"""
Airflow Management Script - Refactored Version

This script handles all Airflow operations including setup, start, stop, and teardown.
All configuration is loaded from .env file - no hardcoded values.

Usage:
    python scripts/airflow.py setup    # Initialize Airflow (DB migration, user creation)
    python scripts/airflow.py start    # Start Airflow services (scheduler + API server)
    python scripts/airflow.py stop     # Stop Airflow services
    python scripts/airflow.py teardown # Stop and remove all Airflow files
    python scripts/airflow.py status   # Check Airflow service status
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import psutil


@dataclass(frozen=True)
class AirflowConfig:
    """Immutable configuration for Airflow operations"""
    home: Path
    dags_folder: Path
    database_url: str
    admin_username: str
    admin_password: str
    admin_email: str
    admin_firstname: str
    admin_lastname: str
    jwt_secret: str
    project_dags: List[str]


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"


def print_status(message: str, color: str = Colors.NC) -> None:
    """Print a status message with color"""
    print(f"{color}{message}{Colors.NC}")


def print_success(message: str) -> None:
    """Print a success message"""
    print_status(f"✓ {message}", Colors.GREEN)


def print_warning(message: str) -> None:
    """Print a warning message"""
    print_status(f"⚠️  {message}", Colors.YELLOW)


def print_error(message: str) -> None:
    """Print an error message"""
    print_status(f"✗ {message}", Colors.RED)


def print_info(message: str) -> None:
    """Print an info message"""
    print_status(f"ℹ️  {message}", Colors.YELLOW)


class EnvironmentLoader:
    """Loads and validates environment variables from .env file"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.project_root = Path.cwd()

    def load_config(self) -> AirflowConfig:
        """Load and validate Airflow configuration from environment"""
        if not self.env_file.exists():
            raise FileNotFoundError(f"Environment file {self.env_file} not found. Run 'make setup' first.")

        print_status(f"Loading environment variables from {self.env_file}...", Colors.YELLOW)
        
        # Load environment variables
        env_vars = self._load_env_variables()
        
        # Validate required variables
        self._validate_required_variables(env_vars)
        
        # Create configuration object
        config = self._create_config(env_vars)
        
        print_success(f"Loaded {len(env_vars)} environment variables")
        return config

    def _load_env_variables(self) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        
        with open(self.env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse key=value pairs
                if "=" not in line:
                    continue
                    
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Expand ${PWD} references
                value = value.replace("${PWD}", str(self.project_root))
                
                env_vars[key] = value
                os.environ[key] = value
        
        return env_vars

    def _validate_required_variables(self, env_vars: Dict[str, str]) -> None:
        """Validate required Airflow environment variables"""
        required_vars = [
            "AIRFLOW_HOME",
            "AIRFLOW__CORE__DAGS_FOLDER", 
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
            "AIRFLOW_ADMIN_USERNAME",
            "AIRFLOW_ADMIN_PASSWORD",
            "AIRFLOW_ADMIN_EMAIL",
            "AIRFLOW_ADMIN_FIRSTNAME",
            "AIRFLOW_ADMIN_LASTNAME",
            "AIRFLOW__API_AUTH__JWT_SECRET",
        ]
        
        missing_vars = [var for var in required_vars if var not in env_vars or not env_vars[var]]
        
        if missing_vars:
            print_error("Missing required environment variables:")
            for var in missing_vars:
                print_status(f"  - {var}", Colors.RED)
            raise ValueError(f"Missing {len(missing_vars)} required environment variables")
        
        print_success("All required Airflow environment variables present")

    def _create_config(self, env_vars: Dict[str, str]) -> AirflowConfig:
        """Create AirflowConfig from environment variables"""
        return AirflowConfig(
            home=Path(env_vars["AIRFLOW_HOME"]),
            dags_folder=Path(env_vars["AIRFLOW__CORE__DAGS_FOLDER"]),
            database_url=env_vars["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"],
            admin_username=env_vars["AIRFLOW_ADMIN_USERNAME"],
            admin_password=env_vars["AIRFLOW_ADMIN_PASSWORD"],
            admin_email=env_vars["AIRFLOW_ADMIN_EMAIL"],
            admin_firstname=env_vars["AIRFLOW_ADMIN_FIRSTNAME"],
            admin_lastname=env_vars["AIRFLOW_ADMIN_LASTNAME"],
            jwt_secret=env_vars["AIRFLOW__API_AUTH__JWT_SECRET"],
            project_dags=["ticker_converter_daily_etl", "ticker_converter_manual_backfill", "test_etl_dag"]
        )


class AirflowCommandRunner:
    """Handles running Airflow commands with proper environment setup"""

    def __init__(self, config: AirflowConfig):
        self.config = config
        self.project_root = Path.cwd()
        self._validate_venv()

    def _validate_venv(self) -> None:
        """Ensure virtual environment exists"""
        venv_python = self.project_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            raise FileNotFoundError("Virtual environment not found. Run 'make setup' first.")
        self.venv_python = venv_python

    def run_command(self, args: List[str], wait: bool = True) -> Optional[subprocess.Popen]:
        """Run an airflow command with proper environment setup"""
        cmd = [str(self.venv_python), "-m", "airflow"] + args
        env = self._prepare_environment()
        
        if wait:
            subprocess.run(cmd, check=True, capture_output=False, env=env)
            return None
        else:
            return subprocess.Popen(cmd, env=env)

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for subprocess"""
        env = os.environ.copy()
        
        # Verify critical environment variables are set
        required_vars = {
            'AIRFLOW_HOME': str(self.config.home),
            'AIRFLOW__CORE__DAGS_FOLDER': str(self.config.dags_folder),
            'AIRFLOW__DATABASE__SQL_ALCHEMY_CONN': self.config.database_url,
        }
        
        for var, expected_value in required_vars.items():
            actual_value = env.get(var)
            if actual_value != expected_value:
                print_error(f"Environment variable mismatch: {var}")
                print_error(f"  Expected: {expected_value}")
                print_error(f"  Actual: {actual_value}")
                raise RuntimeError(f"Environment variable {var} not properly set")
        
        return env


class AirflowProcessManager:
    """Manages Airflow processes (start/stop/status)"""

    @staticmethod
    def find_airflow_processes() -> List[psutil.Process]:
        """Find all running Airflow processes"""
        processes = []
        for process in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(process.info["cmdline"] or [])
                if "airflow" in cmdline and any(
                    keyword in cmdline for keyword in ["scheduler", "api_server", "api-server"]
                ):
                    processes.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    @classmethod
    def is_running(cls) -> bool:
        """Check if any Airflow processes are running"""
        return len(cls.find_airflow_processes()) > 0

    @classmethod
    def stop_all(cls) -> int:
        """Stop all Airflow processes and return count stopped"""
        processes = cls.find_airflow_processes()
        stopped_count = 0
        
        for process in processes:
            try:
                print_status(f"Stopping process {process.pid}: {process.name()}", Colors.YELLOW)
                process.terminate()
                stopped_count += 1
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    print_warning(f"Force killing process {process.pid}")
                    process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return stopped_count

    @classmethod
    def get_status(cls) -> List[str]:
        """Get status of running Airflow processes"""
        processes = cls.find_airflow_processes()
        status_list = []
        
        for process in processes:
            try:
                cmdline = " ".join(process.cmdline())
                if "scheduler" in cmdline:
                    status_list.append(f"Scheduler (PID: {process.pid})")
                elif "api_server" in cmdline or "api-server" in cmdline:
                    status_list.append(f"API Server (PID: {process.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return status_list


class AirflowManager:
    """Main Airflow management operations"""

    def __init__(self, config: AirflowConfig):
        self.config = config
        self.runner = AirflowCommandRunner(config)
        self.process_manager = AirflowProcessManager()

    def setup(self) -> None:
        """Initialize Airflow: database migration and user creation"""
        print_status("Setting up Apache Airflow...", Colors.BLUE)
        
        print_status(f"Airflow Home: {self.config.home}", Colors.YELLOW)
        print_status(f"DAGs Folder: {self.config.dags_folder}", Colors.YELLOW)
        print_status(f"Database: {self.config.database_url}", Colors.YELLOW)
        
        # Ensure airflow home directory exists
        self.config.home.mkdir(parents=True, exist_ok=True)
        
        # Database migration
        self._migrate_database()
        
        # Create admin user
        self._create_admin_user()
        
        print_success("Airflow setup completed")

    def _migrate_database(self) -> None:
        """Run database migration"""
        print_status("Running database migration...", Colors.YELLOW)
        self.runner.run_command(["db", "migrate"])
        print_success("Database migration completed")

    def _create_admin_user(self) -> None:
        """Create admin user if not exists"""
        print_status("Creating admin user (if not exists)...", Colors.YELLOW)
        
        user_cmd = [
            "users", "create",
            "--username", self.config.admin_username,
            "--firstname", self.config.admin_firstname,
            "--lastname", self.config.admin_lastname,
            "--role", "Admin",
            "--email", self.config.admin_email,
            "--password", self.config.admin_password,
        ]
        
        try:
            self.runner.run_command(user_cmd)
            print_success("Admin user created")
        except subprocess.CalledProcessError:
            print_info(f"Admin user {self.config.admin_username} already exists")

    def start(self) -> None:
        """Start Airflow services: scheduler and API server"""
        print_status("Starting Apache Airflow services...", Colors.BLUE)
        
        # Check if already running
        if self.process_manager.is_running():
            print_warning("Airflow services are already running")
            self.status()
            return
        
        # Start services
        self._start_scheduler()
        time.sleep(3)  # Allow scheduler to start
        self._unpause_dags()
        self._start_api_server()

    def _start_scheduler(self) -> None:
        """Start Airflow scheduler in background"""
        print_status("Starting Airflow scheduler...", Colors.YELLOW)
        self.runner.run_command(["scheduler", "--daemon"], wait=False)

    def _unpause_dags(self) -> None:
        """Unpause project DAGs"""
        for dag_id in self.config.project_dags:
            try:
                self.runner.run_command(["dags", "unpause", dag_id])
                print_success(f"Unpaused DAG: {dag_id}")
            except subprocess.CalledProcessError:
                print_info(f"DAG {dag_id} not found or already active")

    def _start_api_server(self) -> None:
        """Start API server (foreground)"""
        print_status("Starting Airflow API server...", Colors.YELLOW)
        print_status("Airflow will be available at: http://localhost:8080", Colors.CYAN)
        print_success(f"Username: {self.config.admin_username} | Password: {self.config.admin_password}")
        print_status("Press Ctrl+C to stop Airflow", Colors.CYAN)
        
        try:
            self.runner.run_command(["api-server", "--port", "8080"])
        except KeyboardInterrupt:
            print_status("\nStopping Airflow services...", Colors.YELLOW)
            self.stop()

    def stop(self) -> None:
        """Stop all Airflow services"""
        print_status("Stopping Airflow services...", Colors.BLUE)
        
        stopped_count = self.process_manager.stop_all()
        
        if stopped_count > 0:
            print_success(f"Stopped {stopped_count} Airflow processes")
        else:
            print_info("No Airflow processes were running")

    def teardown(self) -> None:
        """Stop Airflow and remove all Airflow files"""
        if not self._confirm_teardown():
            print_status("Teardown cancelled", Colors.YELLOW)
            return
        
        print_status("Tearing down Airflow...", Colors.BLUE)
        
        # Stop services first
        self.stop()
        
        # Remove airflow directory
        self._remove_airflow_files()
        
        print_success("Airflow teardown completed")

    def _confirm_teardown(self) -> bool:
        """Confirm teardown operation"""
        print_error("WARNING: This will stop Airflow and delete all airflow/ files")
        response = input(f"{Colors.YELLOW}Are you sure? (y/N): {Colors.NC}")
        return response.lower() == "y"

    def _remove_airflow_files(self) -> None:
        """Remove Airflow files"""
        if self.config.home.exists():
            print_status(f"Removing {self.config.home}...", Colors.YELLOW)
            shutil.rmtree(self.config.home)
            print_success("Airflow files removed")
        else:
            print_info("Airflow directory does not exist")

    def status(self) -> None:
        """Check and display Airflow service status"""
        print_status("Checking Airflow service status...", Colors.BLUE)
        
        processes = self.process_manager.get_status()
        
        if processes:
            print_success("Airflow services running:")
            for proc in processes:
                print_status(f"  • {proc}", Colors.CYAN)
            
            # Check if API server is in the list
            if any("API Server" in proc for proc in processes):
                print_success("Web UI should be available at: http://localhost:8080")
        else:
            print_info("No Airflow services are running")


def create_airflow_manager() -> AirflowManager:
    """Factory function to create configured AirflowManager"""
    env_loader = EnvironmentLoader()
    config = env_loader.load_config()
    return AirflowManager(config)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Airflow Management Script")
    parser.add_argument(
        "command", 
        choices=["setup", "start", "stop", "teardown", "status"], 
        help="Command to execute"
    )

    args = parser.parse_args()

    try:
        airflow_manager = create_airflow_manager()
        
        # Execute command with early return pattern
        if args.command == "setup":
            airflow_manager.setup()
        elif args.command == "start":
            airflow_manager.setup()  # Ensure setup is done first
            airflow_manager.start()
        elif args.command == "stop":
            airflow_manager.stop()
        elif args.command == "teardown":
            airflow_manager.teardown()
        elif args.command == "status":
            airflow_manager.status()

    except KeyboardInterrupt:
        print_status("\nOperation cancelled by user", Colors.YELLOW)
        sys.exit(130)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
