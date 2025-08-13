"""Tests for CLI module."""

from click.testing import CliRunner

from ticker_converter.cli import main


class TestCLI:
    """Test CLI functionality."""

    def test_main_command_exists(self) -> None:
        """Test that main command exists and responds."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Ticker Converter" in result.output

    def test_main_command_has_ingestion_subcommand(self) -> None:
        """Test that ingestion subcommand is available."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ingestion" in result.output

    def test_ingestion_subcommand_exists(self) -> None:
        """Test that ingestion subcommand can be invoked."""
        runner = CliRunner()
        result = runner.invoke(main, ["ingestion", "--help"])
        assert result.exit_code == 0
