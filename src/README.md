# Source Code Directory

## Purpose
Contains all Python source code for the ticker-converter application, organized in a modern package structure with comprehensive CLI, API, and integration capabilities. This is the core application code that provides both command-line and programmatic interfaces.

## Directory Structure

### `/src/` Directory

**Git Status**: Tracked
**Use Case**: Core application code with 69% test coverage and production-ready modules

This directory contains the main application source code organized for scalability and maintainability.

## Detailed Structure
```
src/
├── README.md                      # This file
└── ticker_converter/              # Main application package
    ├── __init__.py               # Package initialization with version info
    ├── cli/                      # Command-line interface modules (97% coverage)
    │   ├── __init__.py
    │   ├── ingestion.py          # Data ingestion commands
    │   └── validation.py         # Data validation utilities
    ├── cli.py                    # Main CLI entry point
    ├── cli_ingestion.py         # Legacy ingestion CLI (being refactored)
    ├── config.py                # Application configuration management
    ├── run_api.py               # FastAPI server launcher
    ├── api_clients/             # External API integration (85% coverage)
    │   ├── __init__.py
    │   ├── alpha_vantage.py     # Alpha Vantage API client
    │   ├── base_client.py       # Base API client with retry logic
    │   └── rate_limiter.py      # API rate limiting utilities
    ├── data_ingestion/          # Data processing pipeline
    │   ├── __init__.py
    │   ├── orchestrator.py      # Main data orchestration (32% coverage - priority)
    │   └── validators.py        # Data validation logic
    ├── data_models/             # Pydantic models (78% coverage)
    │   ├── __init__.py
    │   ├── market_data.py       # Market data models
    │   ├── api_responses.py     # API response models
    │   └── database_models.py   # Database interaction models
    ├── integrations/            # System integrations
    │   ├── __init__.py
    │   ├── database_manager.py  # Database operations (99% coverage)
    │   └── airflow_integration.py # Airflow DAG helpers
    └── py.typed                 # Type hint marker file
```

### Key Modules and Coverage Status

#### High-Coverage Modules (Production Ready)
- **`cli/` (97% coverage)**: Complete command-line interface with comprehensive testing
- **`integrations/database_manager.py` (99% coverage)**: Robust database operations
- **`api_clients/` (85% coverage)**: External API integration with retry logic
- **`data_models/` (78% coverage)**: Pydantic models for type-safe data handling

#### Development Priority Modules
- **`data_ingestion/orchestrator.py` (32% coverage)**: Main orchestration logic - priority for testing
- **Legacy modules**: `cli_ingestion.py` being refactored into modular `cli/` structure

### Module Responsibilities

#### `/src/ticker_converter/cli/` - Command Line Interface
- **Purpose**: Modern CLI implementation with comprehensive coverage
- **Features**: Data ingestion, validation, system inspection
- **Testing**: 97% coverage with full pytest validation
- **Architecture**: Modular command structure with shared utilities

#### `/src/ticker_converter/api_clients/` - External API Integration
- **Purpose**: Robust API client implementations with retry logic
- **Features**: Rate limiting, error handling, response validation
- **Clients**: Alpha Vantage (financial data), extensible base client
- **Testing**: 85% coverage with mock response validation

#### `/src/ticker_converter/data_models/` - Type-Safe Data Models
- **Purpose**: Pydantic models for data validation and serialization
- **Features**: Market data models, API response parsing, database models
- **Type Safety**: Complete type annotations with mypy validation
- **Testing**: 78% coverage with data validation scenarios

#### `/src/ticker_converter/integrations/` - System Integration
- **Purpose**: Database operations and external system integration
- **Features**: PostgreSQL operations, connection pooling, transaction management
- **Quality**: 99% test coverage for database_manager.py
- **Integration**: Airflow DAG helpers and utilities

## Quality Standards and Architecture

### Code Quality Metrics (v3.1.1)
- **Pylint Score**: 10.00/10 across all modules
- **MyPy Compliance**: Full type checking with strict settings
- **Test Coverage**: 69% overall (individual module coverage varies)
- **Black Formatting**: 120-character line length, consistent style
- **Import Organization**: isort with black profile

### Modern Python Patterns
- **Type Annotations**: Comprehensive typing throughout
- **Pydantic Models**: Type-safe data validation and serialization
- **Async Support**: Async/await patterns where appropriate
- **Error Handling**: Comprehensive exception handling with user-friendly messages
- **Configuration**: Environment-based configuration with validation

### Architecture Principles
1. **Modular Design**: Clear separation of concerns across modules
2. **Type Safety**: Full type annotations with mypy validation
3. **Testability**: High test coverage with comprehensive fixtures
4. **CLI-First**: Primary interface through command-line tools
5. **Integration Ready**: Designed for Airflow DAG integration
6. **Configuration-Driven**: Environment-based configuration management

## Usage and Integration

### CLI Interface Access
```bash
# Install in development mode
pip install -e .

# Access main CLI
python -m ticker_converter.cli --help

# Direct module access
python -m ticker_converter.cli_ingestion --help

# FastAPI server launch
python -m ticker_converter.run_api
```

### Integration Points
- **Airflow DAGs**: Modules imported by `dags/helpers/` for workflow orchestration
- **FastAPI Application**: API endpoints use `data_models/` and `integrations/`
- **Testing Framework**: Comprehensive test coverage via `/tests/` directory
- **Quality Pipeline**: Integrated with `make quality` 7-step validation
- **CI/CD**: GitHub Actions integration with `make act-pr` local testing

### Development Workflow
```bash
# Setup development environment
make setup && make install-test

# Run quality checks
make lint-fix && make lint

# Execute tests with coverage
make test

# Start services
make airflow  # Airflow orchestration
make serve    # FastAPI development server
```

## Development Guidelines

### Adding New Modules
1. **Create in appropriate subdirectory** based on functionality domain
2. **Include comprehensive type annotations** for mypy compliance
3. **Add corresponding tests** in `/tests/unit/` mirroring structure
4. **Document public APIs** with clear docstrings
5. **Validate quality** with `make lint` before committing

### Testing Requirements
- **Unit tests**: Mirror source structure in `/tests/unit/`
- **Coverage target**: Aim for 80%+ coverage on new modules
- **Integration tests**: Add to `/tests/integration/` for cross-module functionality
- **Mock external dependencies**: Use fixtures for API responses and database operations

### Type Safety Standards
- **Full annotations**: All function signatures and class attributes
- **MyPy compliance**: No type errors in strict mode
- **Pydantic models**: Use for all data validation and serialization
- **Import organization**: Follow isort + black configuration
