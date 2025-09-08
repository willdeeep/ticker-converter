#!/usr/bin/env python3
"""
Create Airflow admin user - Simple approach for Airflow 3.0+
Based on the original working implementation from scripts/airflow.py
"""

import os
import subprocess
import sys
from pathlib import Path


def print_status(message: str, color: str = "") -> None:
    """Print status message with optional color"""
    print(f"{color}{message}\033[0m" if color else message)


def load_env_variables() -> dict:
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if not env_file.exists():
        raise FileNotFoundError(".env file not found. Run 'make setup' first.")
    
    env_vars = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().replace("${PWD}", str(Path.cwd()))
                env_vars[key] = value
                os.environ[key] = value
    
    return env_vars


def main():
    """Create Airflow admin user using the working approach"""
    try:
        # Load environment variables
        env_vars = load_env_variables()
        
        # Get required variables
        username = env_vars.get("AIRFLOW_ADMIN_USERNAME")
        password = env_vars.get("AIRFLOW_ADMIN_PASSWORD")
        email = env_vars.get("AIRFLOW_ADMIN_EMAIL")
        firstname = env_vars.get("AIRFLOW_ADMIN_FIRSTNAME")
        lastname = env_vars.get("AIRFLOW_ADMIN_LASTNAME")
        
        if not all([username, password, email, firstname, lastname]):
            print_status("Error: Missing required admin user variables in .env", "\033[0;31m")
            return 1
        
        # Set up environment for Airflow command
        airflow_env = os.environ.copy()
        airflow_env.update({
            "AIRFLOW_HOME": env_vars.get("AIRFLOW_HOME", f"{Path.cwd()}/airflow"),
            "AIRFLOW__CORE__DAGS_FOLDER": env_vars.get("AIRFLOW__CORE__DAGS_FOLDER", f"{Path.cwd()}/dags"),
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": env_vars.get("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"),
            "AIRFLOW__CORE__AUTH_MANAGER": "airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager",
        })
        
        # Use the original working command structure
        user_cmd = [
            sys.executable, "-m", "airflow", "users", "create",
            "--username", username,
            "--firstname", firstname,
            "--lastname", lastname,
            "--role", "Admin",
            "--email", email,
            "--password", password,
        ]
        
        print_status(f"Creating admin user: {username}", "\033[0;33m")
        
        # Run the command
        result = subprocess.run(
            user_cmd,
            env=airflow_env,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_status(f"✓ Admin user '{username}' created successfully", "\033[0;32m")
            return 0
        else:
            # Check if user already exists
            if "already exists" in result.stderr or "already exists" in result.stdout:
                print_status(f"⚠ Admin user '{username}' already exists", "\033[0;33m")
                return 0
            else:
                print_status(f"Error creating user: {result.stderr}", "\033[0;31m")
                print_status(f"Command output: {result.stdout}", "\033[0;31m")
                return 1
                
    except Exception as e:
        print_status(f"Error: {e}", "\033[0;31m")
        return 1


if __name__ == "__main__":
    sys.exit(main())
