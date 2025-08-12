"""Main CLI entry point for ticker-converter.

This module provides the main command-line interface that integrates
all CLI commands from different modules.
"""

import click

from .cli_ingestion import ingestion


@click.group()
def main() -> None:
    """Ticker Converter - Financial Market Data Analytics Pipeline."""


# Add the ingestion command group to the main CLI
main.add_command(ingestion)


if __name__ == "__main__":
    main()
