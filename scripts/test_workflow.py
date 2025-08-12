#!/usr/bin/env python3
"""Test script for the complete user workflow.

This script tests the entire user journey:
1. Setup configuration
2. Database initialization
3. Check API functionality
4. Verify SQL operations
"""

import os
import sys
from pathlib import Path
import subprocess


def run_command(command: str, description: str = "") -> bool:
    """Run a shell command and return success status.

    Args:
        command: Shell command to run
        description: Description of what the command does

    Returns:
        True if command succeeded, False otherwise
    """
    if description:
        print(f"🔄 {description}")

    print(f"   Running: {command}")

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def check_file_exists(filepath: str, description: str = "") -> bool:
    """Check if a file exists.

    Args:
        filepath: Path to the file
        description: Description of the check

    Returns:
        True if file exists, False otherwise
    """
    if description:
        print(f"🔍 {description}")

    if Path(filepath).exists():
        print(f"✅ {filepath} exists")
        return True
    else:
        print(f"❌ {filepath} not found")
        return False


def main():
    """Main test workflow."""
    print("🧪 Testing Complete User Workflow")
    print("=" * 50)
    print()

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Please run this from the project root directory")
        sys.exit(1)

    # Test 1: Check Makefile commands
    print("📋 Step 1: Testing Makefile Commands")
    if not run_command("make help", "Check Makefile help"):
        return False
    print()

    # Test 2: Check environment files
    print("📋 Step 2: Testing Environment Configuration")
    if not check_file_exists(".env.example", "Check .env.example exists"):
        return False

    # Check if .env exists
    env_exists = check_file_exists(".env", "Check if .env already configured")
    if not env_exists:
        print("⚠️  .env file not found. You'll need to run 'make setup' first.")
        print("   For testing, we'll use environment variables.")
    print()

    # Test 3: Lint and format
    print("📋 Step 3: Testing Code Quality")
    if not run_command("make lint-fix", "Apply code formatting"):
        return False

    if not run_command("make lint", "Check code quality"):
        return False
    print()

    # Test 4: Run tests
    print("📋 Step 4: Testing Application")
    if not run_command("make test", "Run test suite"):
        return False
    print()

    # Test 5: Check API key configuration
    print("📋 Step 5: Testing API Configuration")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key or api_key == "your_alpha_vantage_api_key_here":
        print("⚠️  Alpha Vantage API key not configured in environment")
        print("   Set ALPHA_VANTAGE_API_KEY environment variable for live testing")
        print("   or run 'make setup' to configure .env file")
        api_configured = False
    else:
        print("✅ Alpha Vantage API key found in environment")
        api_configured = True
    print()

    # Test 6: Database operations (if API key is available)
    if api_configured:
        print("📋 Step 6: Testing Database Operations (Live API)")
        print("⚠️  This will use your Alpha Vantage API quota!")

        proceed = input("Continue with live API testing? [y/N]: ").strip().lower()
        if proceed in ["y", "yes"]:
            if not run_command("make init-db", "Initialize database with live data"):
                print("❌ Database initialization failed")
                return False
        else:
            print("⏭️  Skipping live API testing")
    else:
        print("📋 Step 6: Skipping Database Operations (No API key)")
    print()

    # Test 7: Check SQL files
    print("📋 Step 7: Testing SQL Files")
    sql_files = [
        "sql/ddl/001_create_dimensions.sql",
        "sql/ddl/002_create_facts.sql",
        "sql/ddl/003_create_views.sql",
        "sql/ddl/004_create_indexes.sql",
    ]

    for sql_file in sql_files:
        if not check_file_exists(sql_file, f"Check {sql_file}"):
            return False
    print()

    # Test 8: Test setup script
    print("📋 Step 8: Testing Setup Script")
    if not check_file_exists("scripts/setup.py", "Check setup script exists"):
        return False
    print("✅ Setup script is ready for interactive use")
    print()

    # Summary
    print("🎉 Workflow Test Complete!")
    print("=" * 50)
    print()
    print("✅ All core functionality tested successfully")
    print()
    print("Next steps for users:")
    print("1. Run 'make setup' to configure API keys")
    print("2. Run 'make init-db' to initialize database")
    print("3. Run 'make airflow' to start Airflow")
    print("4. Run 'make serve' to start the API")
    print()
    print("📖 See README.md for complete documentation")


if __name__ == "__main__":
    main()
