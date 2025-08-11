# Project Coding Instructions

This file provides GitHub Copilot with specific guidelines for this repository, which contains **Python packages for ETL (Extract, Transform, Load) pipelines orchestrated by Apache Airflow**, interacting with **SQL databases**, and tested with **Pytest**. Following these instructions will help Copilot generate more accurate, relevant, and compliant code suggestions, reducing errors and speeding up development [1-4].

## Project Overview

This repository develops and manages **ETL pipelines** using **Python** and **Apache Airflow**. Data transformations and loading often involve direct interaction with **SQL databases**. The project's primary goal is to reliably move and process data between various systems [Conversation History, 15, 17, 24].

*   **Project Type**: Data Engineering, ETL Pipelines [3, 4].
*   **Languages**: Python, SQL (e.g., PostgreSQL, MySQL, Snowflake-specific SQL) [3-5].
*   **Frameworks/Tools**: Apache Airflow, Pytest [3-5].
*   **Target Runtimes**: Python 3.9+ [3, 6].
*   **Key Architectural Patterns**: Airflow DAGs define workflows, with modular Python functions handling ETL logic and SQL scripts managing data transformations within databases [6, 7].

### Important Project Documentation References

*   **Project Structure**: See [`docs/FINAL_PROJECT_STRUCTURE.md`](docs/FINAL_PROJECT_STRUCTURE.md) for the target simplified SQL-centric pipeline architecture and directory structure.
*   **Refactoring Guidelines**: Follow the refactoring best practices outlined in [`docs/python-refactoring.md`](docs/python-refactoring.md) when making code improvements or simplifications.

## Build and Validation Instructions

To ensure efficient operation and successful validation, follow these steps for setting up, building, testing, and linting the project [3, 5-7].

### Environment Setup & Dependencies

1.  **Install Python dependencies**: `pip install -r requirements.txt` [3, 6].
2.  **Initialize Airflow DB (if local development)**: `airflow db migrate` [3, 6].
3.  **Start Airflow components (for local development/testing)**:
    *   `airflow webserver`
    *   `airflow scheduler`
    *   Ensure Airflow connections are configured correctly for local/dev databases [3, 6].

### Testing

**All code changes must be accompanied by relevant tests and pass existing test suites.** [3, 6]

*   **Run Unit/Integration Tests**: Use **Pytest** for all Python module and DAG component tests [8].
    *   Command: `pytest` [8].
    *   Ensure all tests pass before committing [3, 6, 9].
    *   To run specific tests: `pytest tests/path/to/your_test_file.py` [3, 6].
*   **Local CI Validation**: Use the **`act` CLI tool** to run GitHub Actions workflows locally, which is especially useful for validating Airflow DAGs or Python packages that have CI checks [10-12].
    *   Ensure **Docker is running** before using `act` [10, 13].
    *   Run all jobs: `act` [14].
    *   Run a specific job (e.g., a Pytest job): `act --job <your-pytest-job-name>` [15].
    *   Refer to GitHub Actions workflow files located in `.github/workflows/` [6, 8, 16].

### Linting & Formatting

*   **Lint Python Code**: Use `flake8` or `ruff` (preferred) [3, 6].
    *   Command: `ruff check src/`
*   **Format Python Code**: Use `black` [3, 6].
    *   Command: `black src/`

## Codebase Layout and Architecture

The repository follows a structured layout to organize ETL components, Python logic, and SQL assets [5-7].

*   **Root Directory (`/`)**: Contains project-level configurations and documentation.
    *   `.github/copilot-instructions.md`: This very file, providing Copilot's instructions [17-21].
    *   `requirements.txt`: Python package dependencies [8].
    *   `README.md`: Project overview and setup instructions [7, 22, 23].
*   **Airflow DAGs (`dags/`)**:
    *   Contains all Airflow DAG definitions (e.g., `my_etl_dag.py`) [6, 7].
    *   Each DAG should be a self-contained unit orchestrating specific ETL workflows.
*   **Python Source Code (`src/`)**:
    *   `src/etl_modules/`: Core Python modules containing reusable ETL functions, data transformations, and business logic.
    *   `src/data_models/`: Python classes or Pydantic models defining data structures for ETL processes.
    *   `src/utils/`: Generic utility functions used across the project [21].
*   **SQL Scripts (`sql/`)**:
    *   `sql/ddl/`: Data Definition Language (DDL) scripts for creating or modifying database schemas.
    *   `sql/dml/`: Data Manipulation Language (DML) scripts for data insertion, updates, and deletions.
    *   `sql/stored_procedures/`: Definitions for database stored procedures or functions.
*   **Tests (`tests/`)**:
    *   `tests/unit/`: Unit tests for individual Python functions and classes in `src/`.
    *   `tests/integration/`: Integration tests for Airflow DAGs and their interaction with SQL databases [16].
*   **Configuration (`config/`)**:
    *   Contains environment-specific configuration files or templates.
*   **CI/CD Workflows (`.github/workflows/`)**:
    *   YAML files defining GitHub Actions workflows for continuous integration and deployment, including **automated testing with Pytest** [8, 9, 16, 24].

## Coding Standards and Conventions

Adherence to these standards ensures code consistency, readability, and maintainability across the project [5, 21, 25, 26].

### Python Standards

*   **PEP 8 Compliance**: Follow PEP 8 for code style and naming conventions (e.g., `snake_case` for variables and functions, `PascalCase` for classes) [25].
*   **Type Hinting**: Use Python type hints consistently for function arguments and return values to improve readability and catch errors [25].
*   **Docstrings**: All functions, classes, and modules should have clear docstrings (Google or NumPy style preferred) explaining their purpose, arguments, and return values [21, 26].
*   **Error Handling**: Use `try-except` blocks for robust error handling, especially for API calls, database interactions, and external service calls. Provide meaningful exception messages [21, 25].
*   **Modularity**: Break down complex logic into small, reusable functions and modules [25].
*   **Logging**: Implement structured logging within Python code to capture ETL pipeline events, errors, and progress [21].

### Airflow DAG Standards

*   **DAG Naming**: `dag_id` should be `kebab-case` and descriptive of its purpose.
*   **Task Naming**: Task IDs should be `snake_case` and clearly indicate the task's action (e.g., `extract_data`, `transform_records`, `load_to_warehouse`).
*   **Operator Usage**: Prefer built-in Airflow operators when possible. For custom Python logic, use `PythonOperator` or `TaskFlow API` decorators. For SQL execution, use `SqlOperator` or database-specific operators (e.g., `PostgresOperator`).
*   **Idempotency**: Design ETL tasks to be idempotent where possible, allowing safe re-runs without adverse effects on data [158 (general principle)].
*   **Templating**: Utilize Jinja templating for dynamic SQL queries and other Airflow parameters.
*   **Dependencies**: Explicitly define task dependencies using `>>` or `<<` operators.

### SQL Standards

*   **Naming Conventions**: Use consistent naming for tables, columns, views, and stored procedures (e.g., `snake_case` for all).
*   **Parameterized Queries**: **Always use parameterized queries** to prevent SQL injection vulnerabilities when constructing SQL statements from dynamic values. Avoid f-strings or direct string concatenation for SQL queries [21].
*   **Idempotent DDL/DML**: Write DDL and DML scripts to be idempotent (e.g., `CREATE TABLE IF NOT EXISTS`, `INSERT OR REPLACE`).
*   **Readability**: Use clear aliases, proper indentation, and comments for complex queries.
*   **Transaction Management**: Employ transactions for atomic SQL operations.

### General Code Style

*   **Formatting**: Use `black` for Python code formatting and ensure consistent SQL formatting.
*   **Code Quality Tools**: Ensure code passes `flake8`/`ruff` checks.

## Security Considerations

Security is paramount for ETL pipelines handling sensitive data [21].

*   **Input Sanitization**: **Sanitize all user inputs and external data** thoroughly before processing in ETL pipelines [21].
*   **Database Query Parameterization**: **Strictly use parameterized queries** to prevent SQL injection attacks. Avoid f-strings or direct string concatenation for SQL queries with dynamic values [21].
*   **Secrets Management**: Never hardcode sensitive information (e.g., database credentials, API keys) directly in code. Utilize Airflow Connections, Airflow Variables, or a dedicated secrets backend (e.g., AWS Secrets Manager, HashiCorp Vault) [158 (general principle of access control)].
*   **Least Privilege**: Configure database users and Airflow connections with the minimum necessary permissions (principle of least privilege) [21].
*   **Detailed Logging**: Implement comprehensive logging of ETL runs, including success/failure, data volume, and performance metrics, but **never log sensitive data** [21].
*   **Access Control**: Ensure proper role-based access control (RBAC) is enforced for Airflow UI, API, and underlying data sources [21].

## Git Workflow Integration (Context for Copilot Agent)

The project uses a **Feature Branch Workflow** for development and relies heavily on **Pull Requests** for code review and integration [24, 27-31].

*   **Branching**: All new features or bug fixes are developed on dedicated feature branches (e.g., `feat/new-pipeline-task`, `fix/dag-bug`). Branches are created off the `dev` branch [24, 31, 32].
*   **Commit Messages**: Follow the **Conventional Commits standard** (`type(scope): subject`) for clear and consistent commit history [12, 33].
*   **Pull Requests (PRs)**: PRs are mandatory for all code merges into `dev` or `main`. They facilitate code review and ensure code quality. **Copilot Code Review** is enabled and uses these instructions [27, 28, 30, 34].
    *   **Self-review**: Authors should self-review their code and ensure tests pass locally before requesting review [30].
    *   **Reviewers**: Reviewers should check code quality, functionality, documentation, and security [35].

---

**Important Notes for Copilot:**

*   **Trust these instructions**: Prioritize the information provided in this file. Only search or explore if information in these instructions is explicitly incomplete or found to be in error [4, 22].
*   **Be specific**: When generating code, be as specific as possible about requirements and provide examples if needed [26, 36].
*   **Validate suggestions**: Always assume a human will review and validate the generated code for functionality, security, readability, and maintainability [37].
*   **Keep responses concise**: While detailed, aim for short, self-contained statements that are broadly applicable. Avoid overly long responses or internal loops, as very long instruction files (e.g., 9,000 tokens) can lead to slower responses and unexpected behavior [1, 38, 39].
*   **Modular Instructions (VS Code Specific)**: If your IDE supports it (e.g., VS Code), you can consider using multiple `.instructions.md` files within a `.github/instructions` directory, with `applyTo` frontmatter, to provide context relevant to specific files or directories [18-20, 40]. This can help manage context for very large codebases [39].
