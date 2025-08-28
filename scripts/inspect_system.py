#!/usr/bin/env python3
"""System inspection script for development diagnostics."""

import json
import os
import platform
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ticker_converter.config import get_settings
except ImportError:
    print("❌ Could not import settings - check your Python environment")
    sys.exit(1)


def inspect_system(detailed: bool = False) -> dict:
    """Inspect system components and return diagnostics."""
    diagnostics = {"timestamp": platform.node(), "detailed": detailed, "components": {}}

    print("🔍 Running system diagnostics...")

    # Check database configuration and connectivity
    try:
        settings = get_settings()

        # Check PostgreSQL (Business Data Database) - using POSTGRES_ env vars directly
        postgres_password = os.getenv("POSTGRES_PASSWORD")
        postgres_user = os.getenv("POSTGRES_USER", "postgres")
        postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("POSTGRES_DB", "ticker_converter")

        if postgres_password:
            try:
                import psycopg2

                pg_url = (
                    f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
                )
                connection = psycopg2.connect(pg_url)
                connection.close()
                diagnostics["components"]["postgresql"] = {
                    "status": "✅ Connected",
                    "details": "PostgreSQL (business data) connection successful",
                }
            except ImportError:
                diagnostics["components"]["postgresql"] = {
                    "status": "❌ Driver Missing",
                    "details": "PostgreSQL driver (psycopg2) not available",
                }
            except Exception as conn_err:
                diagnostics["components"]["postgresql"] = {
                    "status": "❌ Unavailable",
                    "details": f"PostgreSQL connection failed: {str(conn_err)}",
                }
        else:
            diagnostics["components"]["postgresql"] = {
                "status": "⚠️  Not Configured",
                "details": "PostgreSQL credentials not configured in environment",
            }

        # Check Airflow SQLite Database (Separate from business data)
        try:
            import sqlite3

            airflow_db_path = "airflow/airflow.db"  # Default Airflow SQLite location
            if os.path.exists(airflow_db_path):
                connection = sqlite3.connect(airflow_db_path)
                connection.execute("SELECT 1")  # Simple test query
                connection.close()
                diagnostics["components"]["airflow_db"] = {
                    "status": "✅ Connected",
                    "details": "Airflow SQLite database accessible",
                }
            else:
                diagnostics["components"]["airflow_db"] = {
                    "status": "❌ Missing",
                    "details": "Airflow database file not found (run 'make airflow' to initialize)",
                }
        except Exception as airflow_err:
            diagnostics["components"]["airflow_db"] = {
                "status": "❌ Error",
                "details": f"Airflow database error: {str(airflow_err)}",
            }

    except Exception as e:
        diagnostics["components"]["database"] = {"status": "❌ Error", "details": f"Configuration error: {str(e)}"}

    # Check API configuration and connectivity
    try:
        api_key = settings.api.api_key.get_secret_value()  # pylint: disable=no-member
        if not api_key or api_key == "your_alpha_vantage_api_key_here":
            diagnostics["components"]["api"] = {
                "status": "⚠️  Missing",
                "details": "API key not configured (using demo/dummy data)",
            }
        else:
            # Test actual API connectivity (optional, only if detailed mode)
            if detailed:
                try:
                    import requests

                    base_url = settings.api.base_url  # pylint: disable=no-member
                    test_url = f"{base_url}?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={api_key}&outputsize=compact"
                    response = requests.get(test_url, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        if "Error Message" in data:
                            diagnostics["components"]["api"] = {
                                "status": "❌ Invalid Key",
                                "details": "API key authentication failed",
                            }
                        elif "Note" in data:
                            diagnostics["components"]["api"] = {
                                "status": "⚠️  Rate Limited",
                                "details": "API key valid but rate limited",
                            }
                        else:
                            diagnostics["components"]["api"] = {
                                "status": "✅ Connected",
                                "details": "API key valid and responsive",
                            }
                    else:
                        diagnostics["components"]["api"] = {
                            "status": "⚠️  Service Issue",
                            "details": f"API responded with status {response.status_code}",
                        }
                except ImportError:
                    diagnostics["components"]["api"] = {
                        "status": "✅ Configured",
                        "details": "API key configured (requests module not available for testing)",
                    }
                except Exception as api_err:
                    diagnostics["components"]["api"] = {
                        "status": "✅ Configured",
                        "details": f"API key configured (connectivity test failed: {str(api_err)})",
                    }
            else:
                diagnostics["components"]["api"] = {
                    "status": "✅ Configured",
                    "details": "API key configured (use --detailed for connectivity test)",
                }
    except Exception as e:
        diagnostics["components"]["api"] = {"status": "❌ Error", "details": f"API configuration error: {str(e)}"}

    # Environment information
    env = os.getenv("ENVIRONMENT", "development")
    diagnostics["components"]["environment"] = {
        "status": "✅ Development" if env == "development" else "🚀 Production",
        "details": f"Environment: {env}",
    }

    if detailed:
        # Add detailed system information
        diagnostics["system_info"] = {
            "platform": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "node": platform.node(),
        }

    return diagnostics


def main():
    """Main inspection function."""
    detailed = "--detailed" in sys.argv

    try:
        diagnostics = inspect_system(detailed)

        # Print results
        print("\n📋 System Component Status:")
        print("=" * 50)

        for component, info in diagnostics["components"].items():
            print(f"{component.title():.<20} {info['status']}")
            if detailed:
                print(f"  └─ {info['details']}")

        if detailed and "system_info" in diagnostics:
            print("\n🖥️  System Information:")
            print("=" * 50)
            for key, value in diagnostics["system_info"].items():
                print(f"{key.title():.<20} {value}")

        print("\n✅ System diagnostics completed")
        print("💡 Use 'make help' for available operations")

        # Write JSON output if requested
        if "--json" in sys.argv:
            output_file = "system_diagnostics.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(diagnostics, f, indent=2)
            print(f"📄 JSON output written to {output_file}")

    except Exception as error:
        print(f"❌ Diagnostic error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
