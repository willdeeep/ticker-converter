# Makefile Target Reference (v3.1.1)

This document provides comprehensive reference for all available Makefile targets in the ticker-converter project, updated for the latest refactoring with helper functions and enhanced quality pipeline.

## Command Categories

- [Help](#help)
- [Setup and Install](#setup-and-install)
- [Run and Inspect](#run-and-inspect)
- [Testing and Quality](#testing-and-quality)
- [Shutdown and Clean](#shutdown-and-clean)
- [Teardown](#teardown)

## Help

### `make all` (Default Target)
Complete development workflow combining setup, testing dependencies, and quality validation.

```bash
make all    # or just 'make'
```

**Process**:
1. Run `make setup` - Environment configuration
2. Run `make install-test` - Install testing dependencies
3. Run `make quality` - Full 7-step quality pipeline

**Use Case**: New developer onboarding or complete environment validation.

### `make help`
Display comprehensive help with all available commands organized by category.

```bash
make help
```

**Output**: Color-coded help with organized categories and descriptions.

---

## Setup and Install

### `make setup`
Complete project setup with guided environment customization and helper function architecture.

```bash
make setup
```

**Helper Functions Used**:
- `_setup_header`: Display setup introduction
- `_setup_steps`: Execute configuration steps  
- `_setup_footer`: Display completion summary

**Process**:
1. Display setup header and progress information
2. Create `.env` from `.env.example` (if needed)
3. Validate all required environment variables
4. Setup Python 3.11.12 virtual environment
5. Display next steps and completion summary

**Environment Variables Validated**:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `AIRFLOW_ADMIN_*` variables for admin user
- `AIRFLOW__API_AUTH__JWT_SECRET`
- `ALPHA_VANTAGE_API_KEY`

### `make install`
Install core project dependencies for production runtime.

```bash
make install
```

**Helper Functions Used**:
- `_install_header`: Display installation intro
- `_install_deps`: Execute dependency installation

**Dependencies Installed**:
- FastAPI, uvicorn (web framework)
- PostgreSQL drivers (psycopg2-binary, asyncpg)
- Data processing (pandas, requests, aiohttp)
- Apache Airflow 3.0.4 (workflow orchestration)

### `make install-test`
Install everything needed for testing and validation (recommended for development).

```bash
make install-test
```

**Additional Dependencies**:
- Testing framework (pytest, pytest-cov, pytest-asyncio)
- Code quality tools (Black >=23.0.0, isort, Pylint >=3.0.0, MyPy)
- Development utilities (ipython, jupyter, pre-commit)
- Optional quality tools installed via `_install_quality_tools`

**Quality Tools Configuration**:
- Graceful degradation for optional tools (checkmake)
- Error handling for upstream repository issues
- Cross-platform compatibility (brew, go, manual installation)

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
Execute the data pipeline or trigger specific Airflow DAGs using helper functions.

```bash
# Run default data pipeline
make run

# Trigger specific DAG
make run DAG_NAME=daily_etl_pipeline
```

**Helper Functions Used**:
- `_run_pipeline`: Execute main data ingestion pipeline
- `_run_dag`: Trigger specific Airflow DAG

**Environment Variables Required**:
- `AIRFLOW_HOME`, `AIRFLOW__CORE__DAGS_FOLDER`
- Complete Airflow configuration from `.env`

### `make airflow`
Start Apache Airflow 3.0.4 instance with project configuration.

```bash
make airflow
```

**Features**:
- Modern Airflow 3.0.4 with @dag and @task decorators
- Project-local configuration (airflow/ directory)
- Default admin user from environment variables
- PostgreSQL metadata backend
- DAG validation and error checking

### `make inspect`
Perform system diagnostics and health checks.

```bash
# Basic diagnostics
make inspect

# Detailed system information
make inspect DETAILED=1

# Export to JSON
make inspect JSON=1
```

**Diagnostic Coverage**:
- Python virtual environment status (.venv/bin/python)
- PostgreSQL connectivity and permissions
- Airflow service health and DAG validation
- API endpoint availability and responses
- File system permissions and disk space

---

## Testing and Quality

### `make quality` 
Run the comprehensive 7-stage quality validation pipeline using helper functions.

```bash
make quality
```

**Helper Functions Used**:
- `_quality_steps`: Execute all validation stages
- `_quality_summary`: Display final results

**Complete 7-Stage Pipeline**:
1. **Makefile Linting** - checkmake validation with graceful degradation
2. **SQL Quality** - sqlfluff with PostgreSQL dialect standards
3. **Black Formatting** - Code formatting verification (120-char line length)
4. **Import Sorting** - isort validation with black profile
5. **Code Quality** - Pylint analysis (10.00/10 requirement)
6. **Type Checking** - MyPy validation with strict settings
7. **Test Suite** - Full test execution with 69% coverage validation

### `make test`
Run complete test suite with coverage reporting.

```bash
make test
```

**Current Status (v3.1.1)**:
- **245+ tests passing** (100% success rate)
- **69% test coverage** (above 50% requirement)
- HTML coverage report in `htmlcov/index.html`
- XML coverage for CI/CD integration
- Comprehensive module coverage analysis

### `make lint`
Run comprehensive Python code quality checks using helper functions.

```bash
make lint
```

**Helper Functions Used**:
- `_lint_pipeline`: Execute all linting steps sequentially

**Quality Tools Executed**:
- Black formatting verification
- isort import sorting validation  
- Pylint static analysis (10.00/10 target)
- MyPy type checking with strict mode

### `make lint-fix`
Automatically fix code formatting and import issues.

```bash
make lint-fix
```

**Auto-fixes Applied**:
- Black code formatting (120-character line length)
- isort import sorting (black profile)
- Safe, non-destructive formatting only

### Individual Quality Targets

```bash
make lint-makefile  # Makefile structure validation with checkmake
make lint-sql       # SQL quality with sqlfluff (PostgreSQL dialect)
make lint-black     # Black formatting check only
make lint-isort     # Import sorting check only  
make lint-pylint    # Pylint analysis only (10.00/10 target)
make lint-mypy      # MyPy type checking only
```

### `make act-pr`
Run GitHub Actions CI/CD pipeline locally using act.

```bash
make act-pr
```

**Requirements**:
- Docker running for act environment
- `act` CLI tool installed
- Simulates complete GitHub Actions workflow

**Process**:
- Pull request workflow simulation
- Full quality pipeline execution
- CI/CD environment validation
- Docker-based isolation

---

## Shutdown and Clean

### `make clean`
Clean temporary files and caches using helper functions.

```bash
make clean
```

**Helper Functions Used**:
- `_clean_artifacts`: Remove build artifacts and cache files

**Files Removed**:
- Python cache files (`__pycache__`, `*.pyc`)
- Test artifacts (`.pytest_cache`, `.coverage`)  
- Build artifacts (`*.egg-info`, `dist/`)
- MyPy cache (`.mypy_cache`)
- HTML coverage reports (`htmlcov/`)

**Safe Operation**: Preserves source code, configuration, and virtual environment.

### `make airflow-close`
Stop Airflow services gracefully.

```bash
make airflow-close
```

**Process**:
1. Terminate Airflow webserver process
2. Stop Airflow scheduler process
3. Clean up PID files and locks
4. Graceful shutdown with process cleanup

### `make db-close`
Stop PostgreSQL service.

```bash
make db-close
```

**Platform Support**:
- macOS: `brew services stop postgresql`
- Linux: `systemctl stop postgresql` 
- Manual process termination as fallback

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
