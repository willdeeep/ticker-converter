# Makefile Target Reference

This document provides comprehensive reference for all available Makefile targets in the ticker-converter project.

## Command Categories

- [Help](#help)
- [Setup and Install](#setup-and-install)
- [Run and Inspect](#run-and-inspect)
- [Testing](#testing)
- [Shutdown and Clean](#shutdown-and-clean)
- [Teardown](#teardown)

## Help

### `make help`
Display comprehensive help with all available commands organized by category.

```bash
make help
```

**Output**: Formatted help text with color-coded categories and descriptions.

---

## Setup and Install

### `make setup`
Complete project setup with guided environment customization.

```bash
make setup
```

**Process**:
1. Prompts for environment customization
2. Copies `.env.example` to `.env` (if needed)
3. Validates environment variables
4. Sets up Python virtual environment
5. Installs all dependencies

**Environment Variables Used**:
- All variables from `.env` file
- Validates required variables before proceeding

### `make install`
Install core project dependencies.

```bash
make install
```

**Dependencies Installed**:
- Core application dependencies
- API framework (FastAPI, SQLAlchemy)
- Data processing tools (pandas, requests)

### `make install-dev`
Install development dependencies including quality tools.

```bash
make install-dev
```

**Additional Dependencies**:
- Testing framework (pytest, pytest-cov)
- Code quality tools (Black, isort, Pylint, MyPy)
- Development utilities

### `make install-quality`
Install quality assurance tools only.

```bash
make install-quality
```

**Quality Tools**:
- `sqlfluff` - SQL linting
- `checkmake` - Makefile validation
- Python quality tools

### `make init-db`
Initialize PostgreSQL database using environment configuration.

```bash
make init-db
```

**Environment Variables Required**:
- `POSTGRES_HOST`
- `POSTGRES_PORT` 
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

**Process**:
1. Validates PostgreSQL service status
2. Creates database if it doesn't exist
3. Runs database migrations
4. Verifies connectivity

---

## Run and Inspect

### `make run`
Execute the data pipeline or trigger specific Airflow DAGs.

```bash
# Run default data pipeline
make run

# Trigger specific DAG
make run DAG_NAME=manual_backfill

# Run with custom parameters
make run DAG_NAME=daily_etl_dag RUN_DATE=2024-01-15
```

**Environment Variables Used**:
- `AIRFLOW_HOME`
- `AIRFLOW__CORE__DAGS_FOLDER`
- Airflow configuration variables

### `make inspect`
Perform system diagnostics and health checks.

```bash
# Basic diagnostics
make inspect

# Detailed system information
make inspect DETAILED=1

# Export to JSON file
make inspect JSON=1

# Both detailed and JSON output
make inspect DETAILED=1 JSON=1
```

**Diagnostic Information**:
- Python environment status
- Database connectivity
- Service health checks
- Configuration validation
- Available disk space and memory

### `make airflow`
Start Apache Airflow web server and scheduler.

```bash
make airflow
```

**Environment Variables Required**:
- `AIRFLOW_HOME`
- `AIRFLOW__CORE__DAGS_FOLDER`
- `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`
- `AIRFLOW_ADMIN_USERNAME`
- `AIRFLOW_ADMIN_PASSWORD`

**Services Started**:
- Airflow web server (port 8080)
- Airflow scheduler
- Database initialization (if needed)

### `make api`
Start the FastAPI development server.

```bash
make api
```

**Features**:
- Automatic reload on code changes
- Interactive API documentation at `/docs`
- Health check endpoints
- Database connection pooling

---

## Testing

### `make test`
Run the complete test suite with coverage reporting.

```bash
make test
```

**Environment Variables Used**:
- `TEST_DATABASE_URL`
- `PYTEST_COVERAGE_THRESHOLD`
- `PYTEST_EXTRA_ARGS`

**Process**:
1. Sets API key to mock value for testing
2. Runs all unit tests
3. Generates coverage report
4. Validates coverage threshold
5. Creates HTML coverage report

### `make test-int`
Run integration tests (requires external services).

```bash
make test-int
```

**Requirements**:
- PostgreSQL service running
- Airflow configured
- API services accessible
- Valid environment configuration

**Note**: Integration tests are excluded from coverage calculation.

### `make test-ci`
Run CI/CD optimized test suite.

```bash
make test-ci
```

**Optimizations**:
- Minimal output for CI environments
- Fast execution mode
- Environment-specific configurations

### `make quality`
Run comprehensive 7-stage quality validation pipeline.

```bash
make quality
```

**Stages**:
1. **Makefile Linting** - Structure validation
2. **SQL Quality** - Database query standards
3. **Black Formatting** - Code formatting
4. **Import Sorting** - isort validation
5. **Code Quality** - Pylint analysis
6. **Type Checking** - MyPy validation
7. **Test Suite** - Coverage validation

### `make lint`
Run Python code quality checks.

```bash
make lint
```

**Tools Used**:
- Black (formatting)
- isort (import sorting)
- Pylint (code quality)
- MyPy (type checking)

### `make lint-fix`
Automatically fix formatting and import issues.

```bash
make lint-fix
```

**Auto-fixes**:
- Code formatting with Black
- Import sorting with isort
- Basic Pylint auto-fixes

### Individual Lint Targets

```bash
make lint-black      # Black formatting only
make lint-isort      # Import sorting only
make lint-pylint     # Pylint analysis only
make lint-mypy       # MyPy type checking only
make lint-sql        # SQL quality validation
make lint-makefile   # Makefile structure validation
```

### `make act-pr`
Run GitHub Actions CI/CD pipeline locally using act.

```bash
make act-pr
```

**Requirements**:
- Docker running
- `act` CLI installed

**Process**:
- Simulates GitHub Actions environment
- Runs complete CI/CD pipeline
- Validates all quality gates

---

## Shutdown and Clean

### `make airflow-close`
Stop Airflow services gracefully.

```bash
make airflow-close
```

**Process**:
1. Stops web server
2. Stops scheduler
3. Cleans up process files

### `make api-close`
Stop FastAPI development server.

```bash
make api-close
```

### `make clean`
Clean temporary files and caches.

```bash
make clean
```

**Removes**:
- Python cache files (`__pycache__`, `*.pyc`)
- Test artifacts (`.pytest_cache`, `.coverage`)
- Build artifacts (`*.egg-info`, `dist/`)
- Temporary files

### `make clean-db`
Clean database-related temporary files.

```bash
make clean-db
```

**Removes**:
- SQLite database files (development)
- Database migration logs
- Connection cache files

---

## Teardown

### `make teardown-dev`
Complete development environment teardown.

```bash
make teardown-dev
```

**Process**:
1. Stops all services
2. Removes virtual environment
3. Cleans all temporary files
4. Preserves configuration files

### `make teardown-all`
Complete project teardown (use with caution).

```bash
make teardown-all
```

**Process**:
1. Stops all services
2. Removes virtual environment
3. Removes all generated files
4. Removes database files
5. Preserves only source code and documentation

**Warning**: This cannot be undone. Backup important data first.

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALPHA_VANTAGE_API_KEY` | Financial data API key | `your_api_key_here` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `ticker_converter_dev` |
| `POSTGRES_USER` | Database user | `ticker_user` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TEST_DATABASE_URL` | Test database URL | `sqlite:///test.db` |
| `PYTEST_COVERAGE_THRESHOLD` | Minimum coverage | `50` |
| `API_TEST_HOST` | API test host | `http://localhost:8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG_MODE` | Debug mode flag | `false` |

### Airflow Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRFLOW_HOME` | Airflow home directory | `${PWD}/airflow` |
| `AIRFLOW__CORE__DAGS_FOLDER` | DAGs directory | `${PWD}/dags` |
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | Airflow database | `sqlite:///${AIRFLOW_HOME}/airflow.db` |
| `AIRFLOW_ADMIN_USERNAME` | Admin username | `admin` |
| `AIRFLOW_ADMIN_PASSWORD` | Admin password | `admin123` |

---

## Advanced Usage

### Custom Environment Files

```bash
# Use custom environment file
ENV_FILE=.env.production make setup
```

### Parallel Execution

```bash
# Run tests in parallel
PYTEST_EXTRA_ARGS="-n auto" make test
```

### Debug Mode

```bash
# Enable debug output
DEBUG=1 make run
```

### Custom Python Interpreter

```bash
# Use specific Python version
PYTHON=/usr/local/bin/python3.11 make setup
```

---

## Troubleshooting

### Common Command Failures

#### Environment Not Loaded
```
Error: Required variable not set
```
**Solution**: Run `make _validate_env` to check configuration.

#### Service Already Running
```
Error: Address already in use
```
**Solution**: Use appropriate `-close` command first.

#### Permission Issues
```
Error: Permission denied
```
**Solution**: Ensure write permissions in project directory.

### Quality Gate Failures

#### Pylint Score Below 10.00
**Solution**: Run `make lint-fix` or address specific issues.

#### Test Coverage Below Threshold
**Solution**: Add tests or adjust `PYTEST_COVERAGE_THRESHOLD`.

#### Type Checking Errors
**Solution**: Add type annotations or configure MyPy exclusions.

---

## Integration with IDEs

### VS Code Integration

Add to `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Quality Pipeline",
            "type": "shell",
            "command": "make quality",
            "group": "build"
        }
    ]
}
```

### PyCharm Integration

1. Add external tools for common make targets
2. Configure run configurations for testing
3. Set up pre-commit hooks

---

## Performance Tips

1. **Use parallel testing**: `PYTEST_EXTRA_ARGS="-n auto" make test`
2. **Cache dependencies**: Virtual environment caching
3. **Skip integration tests**: Use `make test` instead of `make test-int`
4. **Use fast linting**: Individual lint targets for specific checks

---

## Security Considerations

1. **Never commit `.env` files**
2. **Use strong database passwords**
3. **Rotate API keys regularly**
4. **Review security scan results**: `make security-scan`
5. **Keep dependencies updated**: `make install-dev`

---

**Last Updated**: August 2025 | **Version**: 1.0.0 | **Complete Reference**
