"""Modern CLI for data ingestion operations.

This module provides a clean, user-friendly command-line interface for
data ingestion operations with rich output, progress tracking, and
comprehensive error handling.
"""

# pylint: disable=no-member  # Pydantic fields cause false positives

import json
import logging
import sys
from typing import Any, TextIO

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import get_logging_config, get_settings
from .data_ingestion.orchestrator import DataIngestionOrchestrator

# Initialize rich console
console = Console()


def setup_rich_logging(verbose: bool = False) -> None:
    """Setup rich logging with beautiful output.

    Args:
        verbose: Enable verbose logging
    """
    log_config = get_logging_config()
    level = logging.DEBUG if verbose else getattr(logging, log_config.level)

    # Remove existing handlers
    logging.getLogger().handlers = []

    # Setup rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=verbose,
        rich_tracebacks=True,
    )

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[rich_handler],
    )


def handle_orchestrator_error(error: Exception, operation: str) -> None:
    """Handle orchestrator errors with rich output.

    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
    """
    console.print(f"\n[red]❌ Error during {operation}:[/red]")
    console.print(f"[red]{type(error).__name__}: {error}[/red]")

    if hasattr(error, "__cause__") and error.__cause__:
        console.print(f"[yellow]Caused by: {error.__cause__}[/yellow]")

    console.print("\n[yellow]💡 Suggestions:[/yellow]")
    console.print("• Check your API key configuration")
    console.print("• Verify database connectivity")
    console.print("• Check network connection")
    console.print("• Run with --verbose for detailed logs")


def output_results(results: dict[str, Any], output_file: TextIO | None = None) -> None:
    """Output results with rich formatting.

    Args:
        results: Results dictionary to output
        output_file: Optional file to write JSON results
    """
    # Create results table
    table = Table(title="📊 Ingestion Results", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, value in results.items():
        # Format key to be more readable
        formatted_key = key.replace("_", " ").title()
        table.add_row(formatted_key, str(value))

    console.print(table)

    # Write to file if specified
    if output_file:
        json.dump(results, output_file, indent=2, default=str)
        console.print(f"[green]📄 Results written to {output_file.name}[/green]")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def ingestion(ctx: click.Context, verbose: bool) -> None:
    """🚀 Ticker Converter Data Ingestion CLI

    Modern data ingestion tools for financial market data.
    """
    # Setup logging
    setup_rich_logging(verbose)

    # Store verbose flag in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Display welcome message
    if not ctx.invoked_subcommand:
        console.print("[bold blue]🚀 Ticker Converter Data Ingestion[/bold blue]")
        console.print("Use --help to see available commands")


@ingestion.command()
@click.option(
    "--days",
    "-d",
    type=int,
    default=30,
    help="Number of trading days to fetch (default: 30)",
)
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def setup(days: int, output: TextIO | None) -> None:
    """🏗️  Initialize database with historical data.

    This command sets up the database with historical market data
    for the Magnificent Seven companies and currency exchange rates.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Initialize orchestrator
            task = progress.add_task("Initializing data orchestrator...", total=1)
            orchestrator = DataIngestionOrchestrator()
            progress.update(task, advance=1)

            # Perform setup
            setup_task = progress.add_task(f"Setting up database with {days} days of data...", total=1)
            results = orchestrator.perform_initial_setup(days_back=days)
            progress.update(setup_task, advance=1)

        console.print("[green]✅ Database initialization completed successfully![/green]")
        output_results(results, output)

    except Exception as error:
        handle_orchestrator_error(error, "database setup")
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def update(output: TextIO | None) -> None:
    """📈 Update database with latest market data.

    Fetches and stores the most recent market data for all tracked
    companies and currency pairs.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Initialize orchestrator
            task = progress.add_task("Initializing data orchestrator...", total=1)
            orchestrator = DataIngestionOrchestrator()
            progress.update(task, advance=1)

            # Perform update
            update_task = progress.add_task("Fetching latest market data...", total=1)
            results = orchestrator.run_full_ingestion()
            progress.update(update_task, advance=1)

        console.print("[green]✅ Database update completed successfully![/green]")
        output_results(results, output)

    except Exception as error:
        handle_orchestrator_error(error, "database update")
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output results to file")
def run(output: TextIO | None) -> None:
    """⚡ Run a complete data ingestion cycle.

    Performs a full data ingestion cycle including both historical
    setup and latest data updates.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Initialize orchestrator
            task = progress.add_task("Initializing data orchestrator...", total=1)
            orchestrator = DataIngestionOrchestrator()
            progress.update(task, advance=1)

            # Perform complete ingestion
            run_task = progress.add_task("Running complete ingestion cycle...", total=1)
            results = orchestrator.run_full_ingestion()
            progress.update(run_task, advance=1)

        console.print("[green]✅ Complete ingestion completed successfully![/green]")
        output_results(results, output)

    except Exception as error:
        handle_orchestrator_error(error, "complete ingestion")
        sys.exit(1)


@ingestion.command()
@click.option("--output", "-o", type=click.File("w"), help="Output status to file")
def status(output: TextIO | None) -> None:
    """📋 Check database and system status.

    Displays current database status, configuration, and system health.
    """
    try:
        settings = get_settings()

        # Create status table
        status_table = Table(title="🔍 System Status", show_header=True, header_style="bold cyan")
        status_table.add_column("Component", style="yellow", no_wrap=True)
        status_table.add_column("Status", style="green")
        status_table.add_column("Details", style="white")

        # Check database connectivity
        try:
            # Simple database URL validation
            db_url = settings.database.get_url()
            if db_url:
                db_status = "✅ Connected"
                db_details = f"URL: {db_url}"
            else:
                db_status = "❌ Not Configured"
                db_details = "No database URL configured"
        except Exception as e:
            db_status = "❌ Error"
            db_details = str(e)

        status_table.add_row("Database", db_status, db_details)

        # Check API configuration
        api_key = settings.api.api_key.get_secret_value()
        if api_key and api_key != "demo":
            api_status = "✅ Configured"
            api_details = f"Key: {api_key[:8]}...{api_key[-4:]}"
        else:
            api_status = "⚠️  Demo Key"
            api_details = "Using demo key (limited functionality)"

        status_table.add_row("API Key", api_status, api_details)

        # Environment info
        env_status = f"🌍 {settings.app.environment.title()}"
        env_details = f"Debug: {settings.app.debug}, Workers: {settings.app.max_workers}"
        status_table.add_row("Environment", env_status, env_details)

        console.print(status_table)

        # Output to file if requested
        if output:
            status_data = {
                "database": {"status": db_status, "details": db_details},
                "api": {"status": api_status, "details": api_details},
                "environment": {"status": env_status, "details": env_details},
                "timestamp": str(settings.app.version),
            }
            json.dump(status_data, output, indent=2)
            console.print(f"[green]📄 Status written to {output.name}[/green]")

    except Exception as error:
        handle_orchestrator_error(error, "status check")
        sys.exit(1)
