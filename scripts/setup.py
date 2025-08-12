#!/usr/bin/env python3
"""Interactive setup script for ticker-converter application.

This script guides users through the initial configuration process:
1. Creates .env file from .env.example
2. Prompts for Alpha Vantage API key
3. Sets up database credentials
4. Configures Airflow admin user
"""

import sys
from pathlib import Path
from typing import Optional


def get_user_input(
    prompt: str, default: Optional[str] = None, required: bool = True
) -> str:
    """Get user input with optional default value.

    Args:
        prompt: The prompt to display to the user
        default: Default value if user provides no input
        required: Whether input is required

    Returns:
        User input or default value
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    while True:
        value = input(full_prompt).strip()

        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please provide a value.")


def main():
    """Main setup function."""
    print("🚀 Welcome to Ticker Converter Setup!")
    print("=" * 50)
    print()
    print("This script will help you configure your environment for the")
    print("Financial Market Data Analytics Pipeline.")
    print()

    # Check if .env already exists
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_example.exists():
        print("❌ Error: .env.example file not found!")
        print("Please make sure you're running this from the project root directory.")
        sys.exit(1)

    if env_file.exists():
        overwrite = (
            input("⚠️  .env file already exists. Overwrite? [y/N]: ").strip().lower()
        )
        if overwrite not in ["y", "yes"]:
            print("Setup cancelled. Existing .env file preserved.")
            return

    print("📝 Setting up your configuration...")
    print()

    # Read the example file
    with open(env_example, "r", encoding="utf-8") as f:
        env_content = f.read()

    # Alpha Vantage API Key (required)
    print("🔑 Alpha Vantage API Configuration")
    print("   Get your free API key at: https://www.alphavantage.co/support/#api-key")
    api_key = get_user_input("Enter your Alpha Vantage API key", required=True)
    env_content = env_content.replace("your_alpha_vantage_api_key_here", api_key)
    print("✅ Alpha Vantage API key configured")
    print()

    # Database Configuration
    print("🗄️  PostgreSQL Database Configuration")
    db_host = get_user_input("Database host", default="localhost")
    db_port = get_user_input("Database port", default="5432")
    db_name = get_user_input("Database name", default="ticker_converter")
    db_user = get_user_input("Database user", default="postgres")
    db_password = get_user_input("Database password", required=True)

    env_content = env_content.replace(
        "POSTGRES_HOST=localhost", f"POSTGRES_HOST={db_host}"
    )
    env_content = env_content.replace("POSTGRES_PORT=5432", f"POSTGRES_PORT={db_port}")
    env_content = env_content.replace(
        "POSTGRES_DB=ticker_converter", f"POSTGRES_DB={db_name}"
    )
    env_content = env_content.replace(
        "POSTGRES_USER=postgres", f"POSTGRES_USER={db_user}"
    )
    env_content = env_content.replace("your_postgres_password_here", db_password)
    print("✅ Database configuration set")
    print()

    # Airflow Configuration
    print("🌬️  Apache Airflow Configuration")
    airflow_username = get_user_input("Airflow admin username", default="admin")
    airflow_password = get_user_input("Airflow admin password", default="admin123")
    airflow_email = get_user_input(
        "Airflow admin email", default="admin@ticker-converter.local"
    )

    env_content = env_content.replace(
        "AIRFLOW_ADMIN_USERNAME=admin", f"AIRFLOW_ADMIN_USERNAME={airflow_username}"
    )
    env_content = env_content.replace(
        "AIRFLOW_ADMIN_PASSWORD=admin123", f"AIRFLOW_ADMIN_PASSWORD={airflow_password}"
    )
    env_content = env_content.replace(
        "AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.local",
        f"AIRFLOW_ADMIN_EMAIL={airflow_email}",
    )
    print("✅ Airflow configuration set")
    print()

    # Write the .env file
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("🎉 Configuration complete!")
    print(f"✅ Created {env_file}")
    print()
    print("Next steps:")
    print("1. Initialize the database:     make init-db")
    print("2. Start Airflow:              make airflow")
    print("3. Start the API server:       make serve")
    print()
    print("📖 For more information, see README.md")
    print()
    print(
        "⚠️  Remember to keep your .env file secure and never commit it to version control!"
    )


if __name__ == "__main__":
    main()
