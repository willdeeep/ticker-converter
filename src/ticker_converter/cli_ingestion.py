"""CLI command for data ingestion operations.

This module provides command-line interface for running data ingestion
for the Magnificent Seven companies and USD/GBP currency data.
"""

import json
import logging
import sqlite3
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
        sqlite3.Error,
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
        sqlite3.Error,
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
        sqlite3.Error,
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

            db_health = status_info.get("database_health", {})
            click.echo(f"Database status: {db_health.get('status', 'unknown')}")
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
        sqlite3.Error,
        psycopg2.Error,
        ValueError,
        TypeError,
        OSError,
    ) as e:
        click.echo(f"Status check failed: {e}", err=True)
        sys.exit(1)
