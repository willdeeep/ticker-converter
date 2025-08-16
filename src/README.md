# Source Code Directory

## Purpose
Contains all Python source code for setting up, tearing down, and running all aspects of the application through the Command Line Interface (CLI). This is the main application code that users interact with directly.

## Directory Structure

### `/src/` (Root)
- **Use Case**: Top-level application source code entry points
- **Git Status**: Tracked
- **Contents**: Main application modules and packages

### `/src/ticker_converter/` (Main Package)
- **Use Case**: Core application functionality organized by domain
- **Git Status**: Tracked
- **Sub-packages**:
  - `api_clients/`: External API integration (Alpha Vantage, etc.)
  - `data_ingestion/`: Data fetching and processing logic
  - `data_models/`: Pydantic models and data validation
  - Main modules: `cli.py`, `cli_ingestion.py`, `config.py`

### Shell Scripts
- **Use Case**: Bash scripts (*.sh) needed for application functionality
- **Git Status**: Tracked
- **Location**: Can be placed in `/src/` root or appropriate subdirectories
- **Examples**: Setup scripts, deployment automation, environment configuration

## Organization Principles

1. **CLI-Focused**: All code should support command-line operations and user workflows
2. **Domain Separation**: Code is organized by business domain (data ingestion, API clients, etc.)
3. **Reusability**: Functions should be modular and reusable across different CLI commands
4. **Configuration Management**: All configuration handling and environment setup
5. **Application Lifecycle**: Setup, operation, and teardown functionality

## Usage Guidelines

- **New Modules**: Add to appropriate subdirectory based on functionality domain
- **CLI Commands**: Main command entry points should be clearly documented
- **Configuration**: Environment and settings management should be centralized
- **Error Handling**: Comprehensive error handling for user-facing operations
- **Logging**: Rich console output and logging for user feedback

## Integration Points

- **CLI Interface**: Main entry point for all user interactions
- **DAG Integration**: Functions may be called by Airflow DAGs in `/dags/`
- **API Usage**: Utilizes API client classes from `/api/` directory
- **Database Operations**: Uses SQL queries from `/dags/sql/` directory
- **Testing**: All functionality tested via `/tests/` directory

## Development Guidelines

- **Type Annotations**: All functions should have comprehensive type hints
- **Documentation**: Clear docstrings for all public functions and classes
- **Error Messages**: User-friendly error messages and help text
- **Progress Feedback**: Rich console output for long-running operations
- **Configuration Validation**: Validate all user inputs and configuration

## Installation & Usage

Install in development mode: `pip install -e .`
Access CLI: `python -m ticker_converter.cli --help`
