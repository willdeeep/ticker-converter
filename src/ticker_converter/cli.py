"""Command-line interface for the ticker converter."""

import click
from ticker_converter import __version__


@click.command()
@click.version_option(version=__version__)
def main() -> None:
    """Financial Market Data Analytics Pipeline CLI."""
    click.echo(f"Ticker Converter v{__version__}")
    click.echo("Financial Market Data Analytics Pipeline for SCSK")


if __name__ == "__main__":
    main()
