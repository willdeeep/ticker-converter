"""Comprehensive tests for CLI ingestion module.

This module provides comprehensive testing for the CLI ingestion functionality,
covering command parsing, error handling, output formatting, and integration scenarios.
"""

import json
import tempfile
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from src.ticker_converter.cli_ingestion import (
    handle_orchestrator_error,
    ingestion,
    output_results,
    setup_rich_logging,
)


class TestCLIIngestionCommands:
    """Test CLI ingestion command functionality."""

    @staticmethod
    def test_ingestion_group_help() -> None:
        """Test that ingestion group displays help correctly."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["--help"])

        assert result.exit_code == 0
        assert "Ticker Converter Data Ingestion CLI" in result.output
        assert "Modern data ingestion tools" in result.output
        assert "setup" in result.output
        assert "update" in result.output
        assert "run" in result.output
        assert "status" in result.output

    @staticmethod
    def test_ingestion_group_verbose_flag() -> None:
        """Test verbose flag functionality."""
        runner = CliRunner()
        with patch(
            "src.ticker_converter.cli_ingestion.setup_rich_logging"
        ) as mock_logging:
            result = runner.invoke(ingestion, ["--verbose", "status"])

            # When a subcommand is provided, exit code depends on subcommand success
            # We expect it to fail with configuration error since we're not mocking get_settings
            assert result.exit_code in [0, 1]  # Allow either success or failure
            mock_logging.assert_called_once_with(True)

    @staticmethod
    def test_ingestion_group_without_subcommand() -> None:
        """Test ingestion group behavior without subcommand."""
        runner = CliRunner()
        result = runner.invoke(ingestion, [])

        # Click command groups without subcommands exit with status 2 and show usage
        assert result.exit_code == 2
        assert "Ticker Converter Data Ingestion CLI" in result.output
        assert "Modern data ingestion tools" in result.output


class TestSetupCommand:
    """Test the setup command functionality."""

    @staticmethod
    def test_setup_command_help() -> None:
        """Test setup command help output."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["setup", "--help"])

        assert result.exit_code == 0
        assert "Initialize database with historical data" in result.output
        assert "--days" in result.output
        assert "--output" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_setup_command_success(mock_orchestrator_class: Mock) -> None:
        """Test successful setup command execution."""
        # Mock orchestrator instance and results
        mock_orchestrator = MagicMock()
        mock_orchestrator.perform_initial_setup.return_value = {
            "stocks_inserted": 7,
            "currency_rates_inserted": 10,
            "total_records": 17,
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["setup"])

        assert result.exit_code == 0
        assert "Database initialization completed successfully" in result.output
        mock_orchestrator.perform_initial_setup.assert_called_once_with(days_back=30)

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_setup_command_with_custom_days(mock_orchestrator_class: Mock) -> None:
        """Test setup command with custom days parameter."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.perform_initial_setup.return_value = {"total_records": 50}
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["setup", "--days", "60"])

        assert result.exit_code == 0
        mock_orchestrator.perform_initial_setup.assert_called_once_with(days_back=60)

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_setup_command_with_output_file(mock_orchestrator_class: Mock) -> None:
        """Test setup command with output file."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.perform_initial_setup.return_value = {
            "stocks": 7,
            "currencies": 3,
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            result = runner.invoke(ingestion, ["setup", "--output", f.name])

            assert result.exit_code == 0
            # Rich console splits the output across lines with formatting
            assert "Results written to" in result.output
            assert f.name in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_setup_command_orchestrator_error(mock_orchestrator_class: Mock) -> None:
        """Test setup command handling orchestrator errors."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.perform_initial_setup.side_effect = Exception(
            "Database connection failed"
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["setup"])

        assert result.exit_code == 1
        assert "Error during database setup" in result.output
        assert "Database connection failed" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_setup_command_orchestrator_initialization_error(
        mock_orchestrator_class: Mock,
    ) -> None:
        """Test setup command handling orchestrator initialization errors."""
        mock_orchestrator_class.side_effect = ValueError("Invalid configuration")

        runner = CliRunner()
        result = runner.invoke(ingestion, ["setup"])

        assert result.exit_code == 1
        assert "Error during database setup" in result.output
        assert "Invalid configuration" in result.output


class TestUpdateCommand:
    """Test the update command functionality."""

    @staticmethod
    def test_update_command_help() -> None:
        """Test update command help output."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["update", "--help"])

        assert result.exit_code == 0
        assert "Update database with latest market data" in result.output
        assert "--output" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_update_command_success(mock_orchestrator_class: Mock) -> None:
        """Test successful update command execution."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_ingestion.return_value = {
            "updated_stocks": 7,
            "updated_currencies": 3,
            "timestamp": "2025-08-17T10:00:00",
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["update"])

        assert result.exit_code == 0
        assert "Database update completed successfully" in result.output
        mock_orchestrator.run_full_ingestion.assert_called_once()

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_update_command_with_output_file(mock_orchestrator_class: Mock) -> None:
        """Test update command with output file."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_ingestion.return_value = {"status": "success"}
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            result = runner.invoke(ingestion, ["update", "--output", f.name])

            assert result.exit_code == 0
            # Rich console splits the output across lines with formatting
            assert "Results written to" in result.output
            assert f.name in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_update_command_error_handling(mock_orchestrator_class: Mock) -> None:
        """Test update command error handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_ingestion.side_effect = ConnectionError(
            "API unreachable"
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["update"])

        assert result.exit_code == 1
        assert "Error during database update" in result.output
        assert "API unreachable" in result.output


class TestRunCommand:
    """Test the run command functionality."""

    @staticmethod
    def test_run_command_help() -> None:
        """Test run command help output."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["run", "--help"])

        assert result.exit_code == 0
        assert "Run a complete data ingestion cycle" in result.output
        assert "--output" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_run_command_success(mock_orchestrator_class: Mock) -> None:
        """Test successful run command execution."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_ingestion.return_value = {
            "cycle_completed": True,
            "records_processed": 150,
            "duration_seconds": 45,
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["run"])

        assert result.exit_code == 0
        assert "Complete ingestion completed successfully" in result.output
        mock_orchestrator.run_full_ingestion.assert_called_once()

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.DataIngestionOrchestrator")
    def test_run_command_error_handling(mock_orchestrator_class: Mock) -> None:
        """Test run command error handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_full_ingestion.side_effect = RuntimeError(
            "Orchestration failed"
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        runner = CliRunner()
        result = runner.invoke(ingestion, ["run"])

        assert result.exit_code == 1
        assert "Error during complete ingestion" in result.output
        assert "Orchestration failed" in result.output


class TestStatusCommand:
    """Test the status command functionality."""

    @staticmethod
    def test_status_command_help() -> None:
        """Test status command help output."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["status", "--help"])

        assert result.exit_code == 0
        assert "Check database and system status" in result.output
        assert "--output" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_status_command_success(mock_get_settings: Mock) -> None:
        """Test successful status command execution."""
        # Mock settings object
        mock_settings = MagicMock()
        mock_settings.database.get_url.return_value = "sqlite:///test.db"
        mock_settings.api.api_key.get_secret_value.return_value = (
            "test_api_key_1234567890"
        )
        mock_settings.app.environment = "development"
        mock_settings.app.debug = True
        mock_settings.app.max_workers = 4
        mock_settings.app.version = "1.0.0"
        mock_get_settings.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(ingestion, ["status"])

        assert result.exit_code == 0
        assert "System Status" in result.output
        assert "Database" in result.output
        assert "API Key" in result.output
        assert "Environment" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_status_command_with_demo_api_key(mock_get_settings: Mock) -> None:
        """Test status command with demo API key."""
        mock_settings = MagicMock()
        mock_settings.database.get_url.return_value = "sqlite:///test.db"
        mock_settings.api.api_key.get_secret_value.return_value = "demo"
        mock_settings.app.environment = "development"
        mock_settings.app.debug = False
        mock_settings.app.max_workers = 2
        mock_settings.app.version = "1.0.0"
        mock_get_settings.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(ingestion, ["status"])

        assert result.exit_code == 0
        assert "Demo Key" in result.output
        assert "limited functionality" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_status_command_database_error(mock_get_settings: Mock) -> None:
        """Test status command handling database configuration errors."""
        mock_settings = MagicMock()
        mock_settings.database.get_url.side_effect = Exception("Database config error")
        mock_settings.api.api_key.get_secret_value.return_value = "test_key"
        mock_settings.app.environment = "production"
        mock_settings.app.debug = False
        mock_settings.app.max_workers = 8
        mock_settings.app.version = "2.0.0"
        mock_get_settings.return_value = mock_settings

        runner = CliRunner()
        result = runner.invoke(ingestion, ["status"])

        assert result.exit_code == 0
        assert "Error" in result.output
        assert "Database config error" in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_status_command_with_output_file(mock_get_settings: Mock) -> None:
        """Test status command with output file."""
        mock_settings = MagicMock()
        mock_settings.database.get_url.return_value = "postgresql://test"
        mock_settings.api.api_key.get_secret_value.return_value = "real_api_key_123"
        mock_settings.app.environment = "production"
        mock_settings.app.debug = False
        mock_settings.app.max_workers = 16
        mock_settings.app.version = "3.0.0"
        mock_get_settings.return_value = mock_settings

        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            result = runner.invoke(ingestion, ["status", "--output", f.name])

            assert result.exit_code == 0
            # Rich console splits the output across lines with formatting
            assert "Status written to" in result.output
            assert f.name in result.output

    @staticmethod
    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_status_command_general_error(mock_get_settings: Mock) -> None:
        """Test status command handling general errors."""
        mock_get_settings.side_effect = Exception("Configuration loading failed")

        runner = CliRunner()
        result = runner.invoke(ingestion, ["status"])

        assert result.exit_code == 1
        assert "Error during status check" in result.output
        assert "Configuration loading failed" in result.output


class TestHelperFunctions:
    """Test CLI helper functions."""

    @staticmethod
    def test_setup_rich_logging_normal() -> None:
        """Test rich logging setup in normal mode."""
        with (
            patch("src.ticker_converter.cli_ingestion.logging") as mock_logging,
            patch(
                "src.ticker_converter.cli_ingestion.get_logging_config"
            ) as mock_config,
        ):

            mock_config.return_value.level = "INFO"
            setup_rich_logging(verbose=False)

            mock_logging.basicConfig.assert_called_once()
            _, kwargs = mock_logging.basicConfig.call_args
            assert kwargs["level"] == mock_logging.INFO

    @staticmethod
    def test_setup_rich_logging_verbose() -> None:
        """Test rich logging setup in verbose mode."""
        with (
            patch("src.ticker_converter.cli_ingestion.logging") as mock_logging,
            patch(
                "src.ticker_converter.cli_ingestion.get_logging_config"
            ) as mock_config,
        ):

            mock_config.return_value.level = "INFO"
            setup_rich_logging(verbose=True)

            mock_logging.basicConfig.assert_called_once()
            _, kwargs = mock_logging.basicConfig.call_args
            assert kwargs["level"] == mock_logging.DEBUG

    @staticmethod
    def test_handle_orchestrator_error_simple() -> None:
        """Test error handling for simple exceptions."""
        with patch("src.ticker_converter.cli_ingestion.console") as mock_console:
            error = ValueError("Test error message")
            handle_orchestrator_error(error, "test operation")

            # Verify error was displayed
            assert mock_console.print.call_count >= 2
            calls = [call.args[0] for call in mock_console.print.call_args_list]
            error_calls = [
                call for call in calls if "Error during test operation" in call
            ]
            assert len(error_calls) > 0

    @staticmethod
    def test_handle_orchestrator_error_with_cause() -> None:
        """Test error handling for exceptions with causes."""
        with patch("src.ticker_converter.cli_ingestion.console") as mock_console:
            cause = ConnectionError("Network timeout")
            error = RuntimeError("Operation failed")
            error.__cause__ = cause

            handle_orchestrator_error(error, "network operation")

            # Verify both error and cause were displayed
            calls = [call.args[0] for call in mock_console.print.call_args_list]
            cause_calls = [call for call in calls if "Caused by" in call]
            assert len(cause_calls) > 0

    @staticmethod
    def test_output_results_console_only() -> None:
        """Test output results to console only."""
        with patch("src.ticker_converter.cli_ingestion.console") as mock_console:
            results = {
                "stocks_processed": 7,
                "currency_rates_updated": 10,
                "total_time_seconds": 45,
            }

            output_results(results)

            # Verify table was created and printed
            assert mock_console.print.called

    @staticmethod
    def test_output_results_with_file() -> None:
        """Test output results to both console and file."""
        results = {"test_metric": 42, "status": "success"}

        with patch("src.ticker_converter.cli_ingestion.console") as mock_console:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                output_results(results, f)
                f.flush()

                # Verify file was written
                with open(f.name, "r", encoding="utf-8") as read_file:
                    written_data = json.load(read_file)
                    assert written_data == results

                # Verify console output included file confirmation
                calls = [
                    str(call.args[0]) for call in mock_console.print.call_args_list
                ]
                file_calls = [
                    call for call in calls if f"Results written to {f.name}" in call
                ]
                assert len(file_calls) > 0


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    @staticmethod
    def test_cli_chain_setup_then_update() -> None:
        """Test running setup followed by update commands."""
        with patch(
            "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
        ) as mock_orch:
            mock_instance = MagicMock()
            mock_instance.perform_initial_setup.return_value = {"setup": "complete"}
            mock_instance.run_full_ingestion.return_value = {"update": "complete"}
            mock_orch.return_value = mock_instance

            runner = CliRunner()

            # Run setup
            setup_result = runner.invoke(ingestion, ["setup", "--days", "7"])
            assert setup_result.exit_code == 0

            # Run update
            update_result = runner.invoke(ingestion, ["update"])
            assert update_result.exit_code == 0

            # Verify both calls were made
            mock_instance.perform_initial_setup.assert_called_once_with(days_back=7)
            mock_instance.run_full_ingestion.assert_called_once()

    @staticmethod
    def test_cli_error_propagation() -> None:
        """Test that errors are properly propagated through CLI."""
        with patch(
            "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
        ) as mock_orch:
            mock_orch.side_effect = ImportError("Missing dependency")

            runner = CliRunner()
            result = runner.invoke(ingestion, ["run"])

            assert result.exit_code == 1
            assert "Missing dependency" in result.output

    @staticmethod
    def test_cli_verbose_logging_integration() -> None:
        """Test verbose logging integration across commands."""
        with (
            patch(
                "src.ticker_converter.cli_ingestion.setup_rich_logging"
            ) as mock_logging,
            patch(
                "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
            ) as mock_orch,
        ):

            mock_instance = MagicMock()
            mock_instance.run_full_ingestion.return_value = {"status": "ok"}
            mock_orch.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(ingestion, ["--verbose", "run"])

            assert result.exit_code == 0
            mock_logging.assert_called_once_with(True)

    @staticmethod
    def test_cli_output_file_error_handling() -> None:
        """Test CLI behavior when output file cannot be written."""
        with patch(
            "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
        ) as mock_orch:
            mock_instance = MagicMock()
            mock_instance.perform_initial_setup.return_value = {"test": "data"}
            mock_orch.return_value = mock_instance

            runner = CliRunner()
            # Try to write to invalid path
            result = runner.invoke(
                ingestion, ["setup", "--output", "/invalid/path/output.json"]
            )

            # Should fail due to invalid file path
            assert result.exit_code != 0


class TestCLIParameterValidation:
    """Test CLI parameter validation and edge cases."""

    @staticmethod
    def test_setup_days_parameter_validation() -> None:
        """Test days parameter validation in setup command."""
        runner = CliRunner()

        # Test zero days
        with patch(
            "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
        ) as mock_orch:
            mock_instance = MagicMock()
            mock_instance.perform_initial_setup.return_value = {"days": 0}
            mock_orch.return_value = mock_instance

            result = runner.invoke(ingestion, ["setup", "--days", "0"])
            assert result.exit_code == 0
            mock_instance.perform_initial_setup.assert_called_once_with(days_back=0)

    @staticmethod
    def test_invalid_command_handling() -> None:
        """Test handling of invalid subcommands."""
        runner = CliRunner()
        result = runner.invoke(ingestion, ["invalid_command"])

        assert result.exit_code != 0
        assert "No such command" in result.output

    @patch("src.ticker_converter.cli_ingestion.get_settings")
    def test_missing_required_dependencies(self, mock_get_settings: Mock) -> None:
        """Test CLI behavior when required dependencies are missing."""
        # Mock get_settings to raise ImportError before DataIngestionOrchestrator is even accessed
        mock_get_settings.side_effect = ImportError("Required module not found")

        runner = CliRunner()
        result = runner.invoke(ingestion, ["status"])

        assert result.exit_code == 1
        assert "Required module not found" in result.output


class TestCLIOutputFormatting:
    """Test CLI output formatting and presentation."""

    @staticmethod
    def test_progress_display_formatting() -> None:
        """Test that progress displays are properly formatted."""
        with (
            patch(
                "src.ticker_converter.cli_ingestion.DataIngestionOrchestrator"
            ) as mock_orch,
            patch("src.ticker_converter.cli_ingestion.Progress") as mock_progress,
        ):

            mock_instance = MagicMock()
            mock_instance.perform_initial_setup.return_value = {"test": "result"}
            mock_orch.return_value = mock_instance

            # Mock progress context manager
            mock_progress_instance = MagicMock()
            mock_progress.return_value.__enter__ = MagicMock(
                return_value=mock_progress_instance
            )
            mock_progress.return_value.__exit__ = MagicMock(return_value=None)

            runner = CliRunner()
            result = runner.invoke(ingestion, ["setup"])

            assert result.exit_code == 0
            # Verify progress was used
            mock_progress.assert_called()

    @staticmethod
    def test_error_message_formatting() -> None:
        """Test that error messages are properly formatted."""
        with patch("src.ticker_converter.cli_ingestion.console") as mock_console:
            error = ValueError("Test formatting error")
            handle_orchestrator_error(error, "formatting test")

            # Check that rich formatting was used
            assert mock_console.print.call_count >= 4  # Error, suggestions, etc.

            # Verify error formatting includes rich markup
            calls = [call.args[0] for call in mock_console.print.call_args_list]
            error_calls = [call for call in calls if "[red]" in str(call)]
            assert len(error_calls) > 0

    @staticmethod
    def test_results_table_formatting() -> None:
        """Test that results are formatted as proper tables."""
        with (
            patch("src.ticker_converter.cli_ingestion.console") as mock_console,
            patch("src.ticker_converter.cli_ingestion.Table") as mock_table,
        ):

            results = {"stocks_processed": 7, "processing_time": "2.5 seconds"}

            output_results(results)

            # Verify table was created and used
            mock_table.assert_called()
            mock_console.print.assert_called()
