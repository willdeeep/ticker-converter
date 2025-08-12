"""CLI command for data ingestion operations.

This module provides command-line interface for running data ingestion
for the Magnificent Seven companies and USD/GBP currency data.

Supports both Click-based commands and direct argparse-style flags for Makefile integration.
"""

import argparse
import json
import logging
import os
import sys
import typing
from typing import cast

import click
import psycopg2

from .api_clients.api_client import AlphaVantageAPIError
from .data_ingestion.orchestrator import DataIngestionOrchestrator


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def init_database_command(days: int = 30) -> None:
    """Initialize database with historical data for Makefile integration.

    Args:
        days: Number of trading days to fetch historical data for
    """
    print(f"Initializing database with {days} days of historical data...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_initial_setup(days_back=days)

        print("Database initialization completed successfully")
        print(f"Total records inserted: {results.get('total_records_inserted', 0)}")

        if results.get("stock_data"):
            stock_data = results["stock_data"]
            print(
                f"Stock data: {stock_data['records_inserted']} records for {len(stock_data['companies'])} companies"
            )

        if results.get("currency_data"):
            currency_data = results["currency_data"]
            print(
                f"Currency data: {currency_data['records_inserted']} records for {currency_data['currency_pair']}"
            )

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)


def smart_init_database_command() -> None:
    """Smart database initialization that uses local data when available.
    
    Priority:
    1. Real data from raw_data/ (use all)
    2. Dummy data (use one day for testing)
    3. API data (fetch minimal data)
    """
    print("Starting smart database initialization...")
    print("Checking for local data...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_smart_initial_setup()

        print(f"Database initialization completed using: {results.get('data_source', 'unknown')}")
        print(f"Total records inserted: {results.get('total_records_inserted', 0)}")

        if results.get("stock_data"):
            stock_data = results["stock_data"]
            print(f"Stock data: {stock_data['records_inserted']} records (source: {stock_data.get('source', 'unknown')})")
            if 'symbol' in stock_data:
                print(f"  Symbol: {stock_data['symbol']}")

        if results.get("currency_data"):
            currency_data = results["currency_data"]
            print(f"Currency data: {currency_data['records_inserted']} records (source: {currency_data.get('source', 'unknown')})")
            if 'pair' in currency_data:
                print(f"  Pair: {currency_data['pair']}")

        if results.get("errors"):
            print("Warnings/Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Smart database initialization failed: {e}")
        sys.exit(1)


def schema_only_command() -> None:
    """Initialize database schema only (no data loading).
    
    Creates tables, views, indexes, etc. from DDL files but doesn't load any data.
    """
    print("Initializing database schema only (no data)...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_schema_only_setup()

        print(f"Schema initialization completed: {results.get('success', False)}")
        
        schema_info = results.get("schema_creation", {})
        ddl_files = schema_info.get("ddl_files_executed", [])
        if ddl_files:
            print(f"DDL files executed: {', '.join(ddl_files)}")
        
        print(f"Total records inserted: {results.get('total_records_inserted', 0)} (schema only)")

        if results.get("errors"):
            print("Warnings/Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Schema initialization failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)


def teardown_database_command() -> None:
    """Teardown database schema and all objects.
    
    WARNING: This will permanently delete all database tables, views, and data!
    """
    print("WARNING: This will permanently delete all database objects and data!")
    confirmation = input("Type 'yes' to confirm database teardown: ")
    
    if confirmation.lower() != 'yes':
        print("Database teardown cancelled")
        return
    
    print("Starting database teardown...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_database_teardown()

        print(f"Database teardown completed: {results.get('success', False)}")
        
        teardown_info = results.get("schema_teardown", {})
        objects_dropped = teardown_info.get("objects_dropped", [])
        if objects_dropped:
            print(f"Objects dropped: {len(objects_dropped)}")
            for obj in objects_dropped:
                print(f"  - {obj}")
        
        if results.get("errors"):
            print("Warnings/Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Database teardown failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Database teardown failed: {e}", file=sys.stderr)
        sys.exit(1)


def airflow_setup_command() -> None:
    """Setup Apache Airflow with database initialization, user creation, and service startup."""
    print("Starting Apache Airflow setup...")
    print("This will initialize the Airflow database, create admin user, and start services.")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_airflow_setup()

        print(f"Airflow setup completed: {results.get('success', False)}")
        
        airflow_info = results.get("airflow_setup", {})
        services_started = results.get("services_started", [])
        if services_started:
            print(f"Operations completed: {', '.join(services_started)}")
        
        # Show admin user info
        if results.get("success"):
            print("\n=== Airflow Access Information ===")
            print("Webserver URL: http://localhost:8080")
            
            # Try to get admin user info from environment
            admin_username = os.getenv("AIRFLOW_ADMIN_USERNAME", "admin")
            admin_password = os.getenv("AIRFLOW_ADMIN_PASSWORD", "admin123")
            
            print(f"Admin Username: {admin_username}")
            print(f"Admin Password: {admin_password}")
            print("\nNote: Services are running in the background")

        if results.get("errors"):
            print("Warnings/Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Airflow setup failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Airflow setup failed: {e}", file=sys.stderr)
        sys.exit(1)


def airflow_teardown_command() -> None:
    """Teardown Apache Airflow services."""
    print("Stopping Apache Airflow services...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_airflow_teardown()

        print(f"Airflow teardown completed: {results.get('success', False)}")
        
        services_stopped = results.get("services_stopped", [])
        if services_stopped:
            print(f"Operations completed: {', '.join(services_stopped)}")
        else:
            print("No services were running")

        if results.get("errors"):
            print("Warnings/Errors:")
            for error in results["errors"]:
                print(f"  - {error}")

    except (AlphaVantageAPIError, psycopg2.Error) as e:
        print(f"Airflow teardown failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Airflow teardown failed: {e}", file=sys.stderr)
        sys.exit(1)


def airflow_status_command() -> None:
    """Get current Airflow status."""
    print("Checking Airflow status...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.get_airflow_status()

        if results.get("success"):
            status = results.get("airflow_status", {})
            
            print(f"Webserver running: {status.get('webserver_running', False)}")
            print(f"Scheduler running: {status.get('scheduler_running', False)}")
            print(f"Airflow home: {status.get('airflow_home', 'unknown')}")
            print(f"Admin user: {status.get('admin_user', 'unknown')}")
            
            processes = status.get("processes", [])
            if processes:
                print(f"Running processes: {len(processes)}")
                for proc in processes:
                    print(f"  - {proc['type']} (PID: {proc['pid']})")
            else:
                print("No Airflow processes running")
        else:
            print(f"Status check failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Airflow status check failed: {e}", file=sys.stderr)
        sys.exit(1)


def daily_collection_command() -> None:
    """Run daily data collection for Makefile integration."""
    print("Starting daily data collection...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_daily_update()

        print("Daily data collection completed successfully")
        print(f"Total new records: {results.get('total_records_inserted', 0)}")

        if results.get("stock_updates"):
            stock_updates = results["stock_updates"]
            print(f"Stock updates: {stock_updates['records_inserted']} new records")

        if results.get("currency_updates"):
            currency_updates = results["currency_updates"]
            print(
                f"Currency updates: {currency_updates['records_inserted']} new records"
            )

    except Exception as e:
        print(f"Daily data collection failed: {e}", file=sys.stderr)
        sys.exit(1)


def main_argparse() -> None:
    """Main entry point for argparse-style CLI (used by Makefile)."""
    parser = argparse.ArgumentParser(
        description="Ticker Converter Data Ingestion CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

        # Command group - either init, smart-init, schema-only, teardown, airflow commands, or daily
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        "--init", action="store_true", help="Initialize database with historical data from API"
    )
    command_group.add_argument(
        "--smart-init", action="store_true", 
        help="Smart initialization: use local data if available, minimal API fetch otherwise"
    )
    command_group.add_argument(
        "--schema-only", action="store_true",
        help="Initialize database schema only (no data loading)"
    )
    command_group.add_argument(
        "--teardown", action="store_true",
        help="Teardown database schema and all objects (WARNING: deletes all data!)"
    )
    command_group.add_argument(
        "--airflow-setup", action="store_true",
        help="Setup Apache Airflow (database, user, and start services)"
    )
    command_group.add_argument(
        "--airflow-teardown", action="store_true",
        help="Stop Apache Airflow services"
    )
    command_group.add_argument(
        "--airflow-status", action="store_true",
        help="Check Apache Airflow status"
    )
    command_group.add_argument(
        "--daily",
        action="store_true",
        help="Run daily data collection for previous trading day",
    )

    # Options for init command
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of trading days for historical data (default: 30)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute appropriate command
    if args.init:
        init_database_command(args.days)
    elif getattr(args, 'smart_init', False):
        smart_init_database_command()
    elif getattr(args, 'schema_only', False):
        schema_only_command()
    elif getattr(args, 'teardown', False):
        teardown_database_command()
    elif getattr(args, 'airflow_setup', False):
        airflow_setup_command()
    elif getattr(args, 'airflow_teardown', False):
        airflow_teardown_command()
    elif getattr(args, 'airflow_status', False):
        airflow_status_command()
    elif args.daily:
        daily_collection_command()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def ingestion(ctx: click.Context, verbose: bool) -> None:
    """Data ingestion commands for NYSE stocks and currency data."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@ingestion.command()
@click.option(
    "--days", "-d", default=10, help="Number of days of historical data to fetch"
)
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def setup(days: int, output: click.File) -> None:
    """Perform initial database setup with historical data.

    Fetches the specified number of days of historical data for:
    - Magnificent Seven companies (AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA)
    - USD/GBP currency conversion rates
    """
    click.echo(f"Starting initial database setup with {days} days of data...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_initial_setup(days_back=days)

        # Output results
        if output:
            json.dump(results, cast(typing.TextIO, output), indent=2)
            click.echo(f"Results written to {output.name}")
        else:
            click.echo("\n=== Setup Results ===")
            click.echo(f"Success: {results.get('success', False)}")
            click.echo(
                f"Total records inserted: {results.get('total_records_inserted', 0)}"
            )

            if results.get("stock_data"):
                stock_data = results["stock_data"]
                click.echo(
                    f"Stock data: {stock_data['records_inserted']} records for {len(stock_data['companies'])} companies"
                )

            if results.get("currency_data"):
                currency_data = results["currency_data"]
                click.echo(
                    f"Currency data: {currency_data['records_inserted']} records for {currency_data['currency_pair']}"
                )

            if results.get("errors"):
                click.echo(f"Errors: {results['errors']}")

    except (
        AlphaVantageAPIError,
        psycopg2.Error,
        ValueError,
        TypeError,
        OSError,
    ) as e:
        click.echo(f"Setup failed: {e}", err=True)
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def update(output: click.File | None) -> None:
    """Perform daily data update.

    Fetches recent data (last 2-3 days) for:
    - Magnificent Seven companies
    - USD/GBP currency conversion rates
    """
    click.echo("Starting daily data update...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.perform_daily_update()

        # Output results
        if output:
            json.dump(results, cast(typing.TextIO, output), indent=2)
            click.echo(f"Results written to {output.name}")
        else:
            click.echo("\n=== Update Results ===")
            click.echo(f"Success: {results.get('success', False)}")
            click.echo(f"Total new records: {results.get('total_records_inserted', 0)}")

            if results.get("stock_updates"):
                stock_updates = results["stock_updates"]
                click.echo(
                    f"Stock updates: {stock_updates['records_inserted']} new records for {stock_updates['companies_updated']} companies"
                )

            if results.get("currency_updates"):
                currency_updates = results["currency_updates"]
                click.echo(
                    f"Currency updates: {currency_updates['records_inserted']} new records"
                )

            if results.get("errors"):
                click.echo(f"Errors: {results['errors']}")

    except (
        AlphaVantageAPIError,
        psycopg2.Error,
        ValueError,
        TypeError,
        OSError,
    ) as e:
        click.echo(f"Update failed: {e}", err=True)
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def run(output: click.File) -> None:
    """Run complete data ingestion process.

    Automatically determines whether to perform initial setup or daily update
    based on current database state.
    """
    click.echo("Starting full data ingestion process...")

    try:
        orchestrator = DataIngestionOrchestrator()
        results = orchestrator.run_full_ingestion()

        # Output results
        if output:
            json.dump(results, cast(typing.TextIO, output), indent=2)
            click.echo(f"Results written to {output.name}")
        else:
            click.echo("\n=== Ingestion Results ===")
            click.echo(f"Database was empty: {results.get('was_empty', 'unknown')}")
            click.echo(
                f"Operation performed: {results.get('operation_performed', 'none')}"
            )
            click.echo(f"Success: {results.get('success', False)}")

            operation_results = results.get("results", {})
            if operation_results:
                click.echo(
                    f"Total records inserted: {operation_results.get('total_records_inserted', 0)}"
                )

                if operation_results.get("stock_data"):
                    stock_data = operation_results["stock_data"]
                    click.echo(
                        f"Stock data: {stock_data.get('records_inserted', 0)} records"
                    )

                if operation_results.get("currency_data"):
                    currency_data = operation_results["currency_data"]
                    click.echo(
                        f"Currency data: {currency_data.get('records_inserted', 0)} records"
                    )

                if operation_results.get("errors"):
                    click.echo(f"Errors: {operation_results['errors']}")

    except (
        AlphaVantageAPIError,
        psycopg2.Error,
        ValueError,
        TypeError,
        OSError,
    ) as e:
        click.echo(f"Ingestion failed: {e}", err=True)
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output status to file")
def status(output: click.File) -> None:
    """Get current data ingestion status.

    Shows information about:
    - Database health and record counts
    - Data freshness for each company
    - Missing recent data
    """
    click.echo("Checking data ingestion status...")

    try:
        orchestrator = DataIngestionOrchestrator()
        status_info = orchestrator.get_ingestion_status()

        # Output status
        if output:
            json.dump(status_info, cast(typing.TextIO, output), indent=2)
            click.echo(f"Status written to {output.name}")
        else:
            click.echo("\n=== Data Ingestion Status ===")

            # Database Status
            db_health = status_info.get("database_health", {})
            db_status = db_health.get('status', 'unknown')
            if db_status == 'online':
                db_url = db_health.get('database_url', 'unknown')
                click.echo(f"Database status: online ({db_url})")
            elif db_status == 'offline':
                db_url = db_health.get('database_url', 'unknown')
                click.echo(f"Database status: offline ({db_url})")
            else:
                click.echo(f"Database status: {db_status}")
                if 'error' in db_health:
                    click.echo(f"Database error: {db_health['error']}")

            # Airflow Status
            airflow_status = status_info.get("airflow_status", {})
            if airflow_status.get('webserver_running'):
                webserver_url = airflow_status.get('webserver_url', 'http://localhost:8080')
                click.echo(f"Airflow status: online ({webserver_url})")
            else:
                click.echo("Airflow status: offline")
            
            click.echo(f"Stock records: {db_health.get('stock_records', 0)}")
            click.echo(f"Currency records: {db_health.get('currency_records', 0)}")
            click.echo(
                f"Latest stock date: {db_health.get('latest_stock_date', 'none')}"
            )
            click.echo(
                f"Latest currency date: {db_health.get('latest_currency_date', 'none')}"
            )

            companies = status_info.get("companies_tracked", [])
            click.echo(f"Companies tracked: {', '.join(companies)}")

            currency_pair = status_info.get("currency_pair", "unknown")
            click.echo(f"Currency pair: {currency_pair}")

            missing_data = status_info.get("missing_recent_data", {})
            if missing_data:
                click.echo("Missing recent data:")
                for symbol, count in missing_data.items():
                    click.echo(f"  {symbol}: {count} missing days")
            else:
                click.echo("No missing recent data")

    except (
        AlphaVantageAPIError,
        psycopg2.Error,
        ValueError,
        TypeError,
        OSError,
    ) as e:
        click.echo(f"Status check failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    # If called as python -m ticker_converter.cli_ingestion with argparse flags,
    # use argparse interface (for Makefile compatibility)
    argparse_flags = [
        "--init", "--daily", "--smart-init", "--schema-only", "--teardown",
        "--airflow-setup", "--airflow-teardown", "--airflow-status"
    ]
    if any(flag in sys.argv for flag in argparse_flags):
        main_argparse()
    else:
        # Otherwise use Click interface
        ingestion.main(standalone_mode=False)
