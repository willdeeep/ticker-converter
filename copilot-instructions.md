# Project Coding Instructions

This file provides GitHub Copilot with specific guidelines for this repository, which contains **Python packages for ETL (Extract, Transform, Load) pipelines orchestrated by Apache Airflow**, interacting with **SQL databases**, and tested with **Pytest**. Following these instructions will help Copilot generate more accurate, relevant, and compliant code suggestions, reducing errors and speeding up development.

## Project Overview

This repository develops and manages **ETL pipelines** using **Python** and **Apache Airflow**. Data transformations and loading often involve direct interaction with **SQL databases**. The project's primary goal is to reliably move and process data between various systems.

*   **Project Type**: Data Engineering, ETL Pipelines
*   **Languages**: Python, SQL (PostgreSQL, SQLite)
*   **Frameworks/Tools**: Apache Airflow, FastAPI, Pytest
*   **Target Runtimes**: Python 3.11.12 (exactly)
*   **Key Architectural Patterns**: Airflow DAGs define workflows, with modular Python functions handling ETL logic and SQL scripts managing data transformations within databases

## Directory Organization Strategy

**CRITICAL**: Always consult directory README files to understand proper placement of new files and functionality. This project uses a strict directory organization to maintain clean, coherent structure.

### Directory Use Cases

Each main directory has a specific purpose and README file that **MUST** be consulted before adding any new content:

#### `/dags/` - Airflow Orchestration
- **Purpose**: All Airflow DAG Python scripts and supporting resources
- **README**: `/dags/README.md`
- **Key Point**: Contains `/dags/sql/` - the single source of truth for ALL SQL queries used anywhere in the project

#### `/src/` - Main Application Source
- **Purpose**: All Python source code for CLI operations, application setup/teardown, and core business logic  
- **README**: `/src/README.md`
- **Key Point**: CLI-focused code that users interact with directly

#### `/api/` - API Components
- **Purpose**: Both external API client classes AND internal FastAPI endpoint definitions
- **README**: `/api/README.md`
- **Key Point**: Handles both consuming external APIs and serving internal APIs

#### `/tests/` - Testing Infrastructure
- **Purpose**: All tests organized by type (unit, integration) with fixtures and configuration
- **README**: `/tests/README.md`
- **Key Point**: Mirrors `/src/` structure for easy navigation, no hardcoded test data

#### `/docs/` - Project Documentation
- **Purpose**: Organized markdown documentation referenced in root README "Further Reading"
- **README**: `/docs/README.md`
- **Key Point**: Authoritative project documentation organized by subject

#### `/scripts/` - Temporary Development Scripts
- **Purpose**: **TEMPORARY** diagnostic and proof-of-concept scripts that can be deleted without breaking anything
- **README**: `/scripts/README.md`
- **Key Point**: Nothing vital should live here - it's a workspace, not a destination

#### `/my_docs/` - Untracked Working Drafts
- **Purpose**: **UNTRACKED** temporary documentation and feature-branch work plans
- **README**: `/my_docs/README.md` (untracked)
- **Key Point**: Git-ignored staging area for drafts before moving to `/docs/`

### File Placement Protocol

**Before creating any new file:**

1. **Read the relevant directory README** to understand the use case
2. **Check for existing functionality** to avoid duplication
3. **Place in appropriate directory** based on purpose, not convenience
4. **Use subdirectories** as outlined in directory READMEs
5. **Update documentation** if adding new functionality

### Avoiding Duplication

- **SQL Queries**: All go in `/dags/sql/` regardless of where they're used
- **Python Utilities**: Check `/src/` before creating new utility functions
- **API Clients**: Check both `/api/` and `/src/ticker_converter/api_clients/`
- **Test Data**: Use `/tests/fixtures/` rather than hardcoding
- **Documentation**: Check `/docs/` before creating guides

## Important Project Documentation References

*   **Project Overview**: See [`overview.md`](docs/architecture/overview.md) for the target simplified SQL-centric pipeline architecture and directory structure.
*   **Directory Organization**: Each directory has a README.md explaining its purpose and organization principles.

## Build and Validation Instructions

To ensure efficient operation and successful validation, follow these steps for setting up, building, testing, and linting the project.

### Environment Setup & Dependencies

1.  **Install Python dependencies**: `pip install -e .[dev]` (development mode with dev dependencies)
2.  **Initialize Airflow DB (if local development)**: `airflow db migrate`
3.  **Start Airflow components (for local development/testing)**:
    *   `airflow webserver`
    *   `airflow scheduler`
    *   Ensure Airflow connections are configured correctly for local/dev databases

### Testing

**All code changes must be accompanied by relevant tests and pass existing test suites.**

*   **Run Unit/Integration Tests**: Use **Pytest** for all Python module and DAG component tests
    *   Command: `pytest`
    *   Ensure all tests pass before committing
    *   To run specific tests: `pytest tests/path/to/your_test_file.py`
    *   Current Status: 108/108 tests passing (100% success rate)
*   **Coverage Requirements**: Maintain test coverage above 50% (currently 54.27%)
*   **Local CI Validation**: Use the **`act` CLI tool** to run GitHub Actions workflows locally
    *   Ensure **Docker is running** before using `act`
    *   Run all jobs: `act`
    *   Run a specific job: `act --job <your-pytest-job-name>`

### Code Quality

*   **Lint Python Code**: Use `pylint` and `mypy`
    *   Command: `python -m pylint src/`
    *   Command: `python -m mypy src/`
*   **Format Python Code**: Use `black`
    *   Command: `black src/`

## Codebase Layout and Architecture

The repository follows a structured layout to organize ETL components, Python logic, and SQL assets.

*   **Root Directory (`/`)**: Contains project-level configurations and documentation.
    *   `copilot-instructions.md`: This file, providing Copilot's instructions
    *   `pyproject.toml`: Python package configuration and dependencies
    *   `README.md`: Project overview and setup instructions
*   **Airflow DAGs (`dags/`)**:
    *   Contains all Airflow DAG definitions (e.g., `daily_etl_dag.py`)
    *   `dags/sql/`: **Single source of truth for ALL SQL queries** (DDL, ETL, queries)
*   **Python Source Code (`src/`)**:
    *   `src/ticker_converter/`: Main Python package containing all application modules
    *   `src/ticker_converter/api_clients/`: External API integration modules
    *   `src/ticker_converter/data_ingestion/`: Data fetching and processing logic  
    *   `src/ticker_converter/data_models/`: Pydantic models for data validation
*   **API Components (`api/`)**:
    *   FastAPI application setup and endpoints
    *   Database connection and session management
    *   API models and dependencies
*   **Tests (`tests/`)**:
    *   `tests/unit/`: Unit tests mirroring `src/` structure
    *   `tests/integration/`: Integration tests for DAGs and database interactions
    *   `tests/fixtures/`: Test data fixtures and mock objects
*   **Documentation (`docs/`)**:
    *   `docs/architecture/`: Technical design documents
    *   `docs/deployment/`: Operations and deployment guides
    *   `docs/user_guides/`: End-user documentation

## Coding Standards and Conventions

Adherence to these standards ensures code consistency, readability, and maintainability across the project.

### Python Standards

*   **PEP 8 Compliance**: Follow PEP 8 for code style and naming conventions
*   **Type Hinting**: Use Python type hints consistently for all functions
*   **Docstrings**: All functions, classes, and modules should have clear docstrings
*   **Error Handling**: Use comprehensive error handling with meaningful messages
*   **Modularity**: Break down complex logic into small, reusable functions
*   **Logging**: Use lazy % formatting for logging (not f-strings)

### Airflow DAG Standards

*   **DAG Naming**: `dag_id` should be `kebab-case` and descriptive
*   **Task Naming**: Task IDs should be `snake_case` and action-oriented
*   **Operator Usage**: Prefer built-in Airflow operators and TaskFlow API
*   **Idempotency**: Design ETL tasks to be idempotent for safe re-runs
*   **Templating**: Utilize Jinja templating for dynamic parameters
*   **Dependencies**: Explicitly define task dependencies

### SQL Standards

*   **Naming Conventions**: Use `snake_case` for all database objects
*   **Parameterized Queries**: **Always use parameterized queries** to prevent SQL injection
*   **Idempotent Scripts**: Write DDL/DML to be safely re-runnable
*   **Readability**: Use clear aliases, proper indentation, and comments
*   **Transaction Management**: Employ transactions for atomic operations

## Security Considerations

Security is paramount for ETL pipelines handling financial data.

*   **Input Sanitization**: Sanitize all external data before processing
*   **SQL Injection Prevention**: Use parameterized queries exclusively
*   **Secrets Management**: Use environment variables and proper secrets backends
*   **Least Privilege**: Configure minimal necessary permissions
*   **Logging Security**: Log operations but never sensitive data
*   **Access Control**: Enforce proper RBAC for all systems

## Git Workflow Integration

The project uses a **Feature Branch Workflow** with Pull Requests for code review.

*   **Branching**: Create feature branches from `main` with descriptive names
*   **Commit Messages**: Follow Conventional Commits standard
*   **Pull Requests**: Mandatory for all merges with comprehensive review
*   **Testing**: All tests must pass before merge
*   **Documentation**: Update relevant documentation with changes

---

**Important Notes for Copilot:**

*   **Directory First**: Always check directory README files before creating new content
*   **Avoid Duplication**: Check existing functionality before implementing new features  
*   **Follow Structure**: Respect the established directory organization and patterns
*   **Test Coverage**: Maintain comprehensive test coverage for all new functionality
*   **Documentation**: Update documentation when adding new features or changing behavior
*   **Security**: Always consider security implications, especially for financial data handling
*   **NO EMOJIS**: Never use emojis in any responses, comments, or code suggestions
