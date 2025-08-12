"""Airflow manager for orchestrating data pipeline operations.

This module handles Apache Airflow initialization, configuration, and lifecycle management
for the data ingestion pipeline, including user management and environment setup.
"""

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AirflowManager:
    """Manages Apache Airflow setup, configuration, and operations."""

    def __init__(self) -> None:
        """Initialize the AirflowManager with environment configuration."""
        self.logger = logging.getLogger(__name__)
        self.airflow_home = os.getenv("AIRFLOW_HOME", str(Path.home() / "airflow"))

        # Admin user configuration from environment
        self.admin_config = {
            "username": os.getenv("AIRFLOW_ADMIN_USERNAME", "admin"),
            "password": os.getenv("AIRFLOW_ADMIN_PASSWORD", "admin123"),
            "email": os.getenv("AIRFLOW_ADMIN_EMAIL", "admin@ticker-converter.local"),
            "firstname": os.getenv("AIRFLOW_ADMIN_FIRSTNAME", "Admin"),
            "lastname": os.getenv("AIRFLOW_ADMIN_LASTNAME", "User"),
        }

    def _run_airflow_command(
        self, command: list[str], capture_output: bool = True
    ) -> dict[str, Any]:
        """Run an Airflow command and return results.

        Args:
            command: List of command arguments (e.g., ['airflow', 'db', 'init'])
            capture_output: Whether to capture stdout/stderr

        Returns:
            Dictionary with command results
        """
        try:
            self.logger.debug("Running command: %s", " ".join(command))

            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                    check=False,
                    env={**os.environ, "AIRFLOW_HOME": self.airflow_home},
                )

                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                # For background processes (like webserver)
                process = subprocess.Popen(
                    command,
                    env={**os.environ, "AIRFLOW_HOME": self.airflow_home},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                return {
                    "success": True,
                    "process": process,
                    "pid": process.pid,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "timeout": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def initialize_airflow_database(self) -> dict[str, Any]:
        """Initialize Airflow database and metadata.

        Returns:
            Dictionary with initialization results
        """
        results = {
            "success": False,
            "operations_completed": [],
            "errors": [],
        }

        try:
            self.logger.info("Initializing Airflow database...")

            # Initialize Airflow database (changed from 'init' to 'migrate' in Airflow 3.0)
            db_init_result = self._run_airflow_command(["airflow", "db", "migrate"])

            if db_init_result.get("success"):
                results["operations_completed"].append("database_initialized")
                self.logger.info("Airflow database initialized successfully")
            else:
                error_msg = f"Database initialization failed: {db_init_result.get('stderr', 'Unknown error')}"
                results["errors"].append(error_msg)
                self.logger.error(error_msg)
                return results

            results["success"] = True

        except Exception as e:
            error_msg = f"Airflow database initialization failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def create_admin_user(self) -> dict[str, Any]:
        """Create Airflow admin user from environment configuration.

        Returns:
            Dictionary with user creation results
        """
        results = {
            "success": False,
            "user_created": False,
            "user_exists": False,
            "errors": [],
        }

        try:
            self.logger.info(
                "Creating Airflow admin user: %s", self.admin_config["username"]
            )

            # Create admin user
            create_user_command = [
                "airflow",
                "users",
                "create",
                "--username",
                self.admin_config["username"],
                "--firstname",
                self.admin_config["firstname"],
                "--lastname",
                self.admin_config["lastname"],
                "--role",
                "Admin",
                "--email",
                self.admin_config["email"],
                "--password",
                self.admin_config["password"],
            ]

            user_result = self._run_airflow_command(create_user_command)

            if user_result.get("success"):
                results["user_created"] = True
                results["success"] = True
                self.logger.info(
                    "Admin user created successfully: %s", self.admin_config["username"]
                )
            else:
                # Check if user already exists
                stderr = user_result.get("stderr", "")
                if "already exists" in stderr.lower():
                    results["user_exists"] = True
                    results["success"] = True
                    self.logger.info(
                        "Admin user already exists: %s", self.admin_config["username"]
                    )
                else:
                    error_msg = f"User creation failed: {stderr}"
                    results["errors"].append(error_msg)
                    self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"Admin user creation failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def start_webserver(
        self, port: int = 8080, background: bool = True
    ) -> dict[str, Any]:
        """Start Airflow webserver.

        Args:
            port: Port to run webserver on
            background: Whether to run in background

        Returns:
            Dictionary with webserver start results
        """
        results = {
            "success": False,
            "webserver_started": False,
            "port": port,
            "errors": [],
        }

        try:
            self.logger.info("Starting Airflow webserver on port %d", port)

            webserver_command = ["airflow", "webserver", "--port", str(port)]

            if background:
                webserver_result = self._run_airflow_command(
                    webserver_command, capture_output=False
                )

                if webserver_result.get("success"):
                    results["webserver_started"] = True
                    results["success"] = True
                    results["pid"] = webserver_result.get("pid")
                    self.logger.info(
                        "Airflow webserver started in background (PID: %s)",
                        results["pid"],
                    )

                    # Give webserver a moment to start
                    time.sleep(2)
                else:
                    error_msg = f"Webserver start failed: {webserver_result.get('error', 'Unknown error')}"
                    results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            else:
                # For foreground execution (blocking)
                webserver_result = self._run_airflow_command(
                    webserver_command, capture_output=True
                )
                results["success"] = webserver_result.get("success", False)
                if not results["success"]:
                    results["errors"].append(
                        webserver_result.get("stderr", "Unknown error")
                    )

        except Exception as e:
            error_msg = f"Webserver start failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def start_scheduler(self, background: bool = True) -> dict[str, Any]:
        """Start Airflow scheduler.

        Args:
            background: Whether to run in background

        Returns:
            Dictionary with scheduler start results
        """
        results = {
            "success": False,
            "scheduler_started": False,
            "errors": [],
        }

        try:
            self.logger.info("Starting Airflow scheduler")

            scheduler_command = ["airflow", "scheduler"]

            if background:
                scheduler_result = self._run_airflow_command(
                    scheduler_command, capture_output=False
                )

                if scheduler_result.get("success"):
                    results["scheduler_started"] = True
                    results["success"] = True
                    results["pid"] = scheduler_result.get("pid")
                    self.logger.info(
                        "Airflow scheduler started in background (PID: %s)",
                        results["pid"],
                    )

                    # Give scheduler a moment to start
                    time.sleep(2)
                else:
                    error_msg = f"Scheduler start failed: {scheduler_result.get('error', 'Unknown error')}"
                    results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            else:
                # For foreground execution (blocking)
                scheduler_result = self._run_airflow_command(
                    scheduler_command, capture_output=True
                )
                results["success"] = scheduler_result.get("success", False)
                if not results["success"]:
                    results["errors"].append(
                        scheduler_result.get("stderr", "Unknown error")
                    )

        except Exception as e:
            error_msg = f"Scheduler start failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def stop_airflow_services(self) -> dict[str, Any]:
        """Stop all Airflow services (webserver and scheduler).

        Returns:
            Dictionary with stop results
        """
        results = {
            "success": False,
            "services_stopped": [],
            "errors": [],
        }

        try:
            self.logger.info("Stopping Airflow services...")

            # Find and stop Airflow processes
            processes_found = []

            # Use ps to find Airflow processes
            try:
                ps_result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                if ps_result.returncode == 0:
                    for line in ps_result.stdout.split("\n"):
                        if "airflow" in line and (
                            "webserver" in line or "scheduler" in line
                        ):
                            parts = line.split()
                            if len(parts) > 1:
                                try:
                                    pid = int(parts[1])
                                    process_type = (
                                        "webserver"
                                        if "webserver" in line
                                        else "scheduler"
                                    )
                                    processes_found.append((pid, process_type))
                                except (ValueError, IndexError):
                                    continue

                # Kill found processes
                for pid, process_type in processes_found:
                    try:
                        subprocess.run(["kill", str(pid)], timeout=5, check=False)
                        results["services_stopped"].append(
                            f"{process_type} (PID: {pid})"
                        )
                        self.logger.info(
                            "Stopped %s process (PID: %d)", process_type, pid
                        )
                    except Exception as e:
                        error_msg = (
                            f"Failed to stop {process_type} (PID: {pid}): {str(e)}"
                        )
                        results["errors"].append(error_msg)
                        self.logger.warning(error_msg)

                results["success"] = True

            except subprocess.TimeoutExpired:
                results["errors"].append("Timeout while finding Airflow processes")

        except Exception as e:
            error_msg = f"Service stop failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def get_airflow_status(self) -> dict[str, Any]:
        """Get current Airflow services status.

        Returns:
            Dictionary with status information
        """
        results = {
            "webserver_running": False,
            "scheduler_running": False,
            "processes": [],
            "airflow_home": self.airflow_home,
            "admin_user": self.admin_config["username"],
        }

        try:
            # Check for running Airflow processes
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if ps_result.returncode == 0:
                for line in ps_result.stdout.split("\n"):
                    if "airflow" in line:
                        if "webserver" in line:
                            results["webserver_running"] = True
                            parts = line.split()
                            if len(parts) > 1:
                                results["processes"].append(
                                    {
                                        "type": "webserver",
                                        "pid": parts[1],
                                        "command": " ".join(parts[10:]),
                                    }
                                )
                        elif "scheduler" in line:
                            results["scheduler_running"] = True
                            parts = line.split()
                            if len(parts) > 1:
                                results["processes"].append(
                                    {
                                        "type": "scheduler",
                                        "pid": parts[1],
                                        "command": " ".join(parts[10:]),
                                    }
                                )

        except Exception as e:
            self.logger.error("Status check failed: %s", str(e))

        return results

    def setup_airflow_complete(self) -> dict[str, Any]:
        """Complete Airflow setup: initialize database, create user, start services.

        Returns:
            Dictionary with complete setup results
        """
        results = {
            "success": False,
            "operations_completed": [],
            "errors": [],
            "database_init": {},
            "user_creation": {},
            "webserver_start": {},
            "scheduler_start": {},
        }

        try:
            self.logger.info("Starting complete Airflow setup")

            # 1. Initialize database
            db_results = self.initialize_airflow_database()
            results["database_init"] = db_results

            if not db_results.get("success"):
                results["errors"].extend(db_results.get("errors", []))
                return results

            results["operations_completed"].extend(
                db_results.get("operations_completed", [])
            )

            # 2. Create admin user
            user_results = self.create_admin_user()
            results["user_creation"] = user_results

            if not user_results.get("success"):
                results["errors"].extend(user_results.get("errors", []))
                return results

            if user_results.get("user_created"):
                results["operations_completed"].append("admin_user_created")
            elif user_results.get("user_exists"):
                results["operations_completed"].append("admin_user_exists")

            # 3. Start webserver
            webserver_results = self.start_webserver(background=True)
            results["webserver_start"] = webserver_results

            if webserver_results.get("success"):
                results["operations_completed"].append("webserver_started")
            else:
                results["errors"].extend(webserver_results.get("errors", []))

            # 4. Start scheduler
            scheduler_results = self.start_scheduler(background=True)
            results["scheduler_start"] = scheduler_results

            if scheduler_results.get("success"):
                results["operations_completed"].append("scheduler_started")
            else:
                results["errors"].extend(scheduler_results.get("errors", []))

            # Overall success if at least database and user setup worked
            results["success"] = db_results.get("success", False) and user_results.get(
                "success", False
            )

            self.logger.info("Airflow setup completed: %s", results["success"])

        except Exception as e:
            error_msg = f"Complete Airflow setup failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def teardown_airflow(self) -> dict[str, Any]:
        """Teardown Airflow: stop services and clean up.

        Returns:
            Dictionary with teardown results
        """
        results = {
            "success": False,
            "operations_completed": [],
            "errors": [],
            "service_stop": {},
        }

        try:
            self.logger.info("Starting Airflow teardown")

            # Stop all services
            stop_results = self.stop_airflow_services()
            results["service_stop"] = stop_results

            if stop_results.get("success"):
                services_stopped = stop_results.get("services_stopped", [])
                if services_stopped:
                    results["operations_completed"].append(
                        f"stopped_services: {', '.join(services_stopped)}"
                    )
                else:
                    results["operations_completed"].append("no_services_running")
            else:
                results["errors"].extend(stop_results.get("errors", []))

            results["success"] = stop_results.get("success", False)
            self.logger.info("Airflow teardown completed: %s", results["success"])

        except Exception as e:
            error_msg = f"Airflow teardown failed: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        return results
