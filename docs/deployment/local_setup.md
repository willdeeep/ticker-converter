# Local Development Environment Setup

## Executive Summary

This guide provides comprehensive instructions for setting up the ticker-converter development environment on macOS, Linux, and Windows. The setup emphasizes **Python 3.11.12 standardization**, **Make-based workflow automation**, and **consistent development environments** to minimize onboarding time and ensure reproducible builds across all development machines.

**Setup Value Proposition**: By following this guide, developers can establish a fully functional development environment in under 30 minutes with automated quality gates, comprehensive testing, and production-like local services.

## Prerequisites and System Requirements

### Python Version Requirement: 3.11.12

**Why Python 3.11.12 Specifically**:
- **Performance**: 10-60% speed improvements over Python 3.10 for async and analytical workloads
- **Modern Syntax**: Union type syntax (`X | Y`) improves code readability and maintainability
- **Error Messages**: Significantly enhanced error messages accelerate debugging and development
- **asyncio Performance**: Critical improvements for FastAPI and database async operations
- **Stability**: 3.11.12 is a stable patch release with essential security fixes and bug corrections

**Verification Command**:
```bash
python --version
# Expected output: Python 3.11.12
```

### System Dependencies

#### macOS Requirements
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required system packages
brew install postgresql@15 git make curl

# Install Python 3.11.12 via pyenv (recommended)
brew install pyenv
pyenv install 3.11.12
pyenv local 3.11.12
```

#### Ubuntu/Debian Requirements
```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y postgresql-15 postgresql-contrib git make curl build-essential \
    libpq-dev python3.11 python3.11-dev python3.11-venv python3-pip

# Verify Python version
python3.11 --version
```

#### Windows Requirements (PowerShell)
```powershell
# Install via Chocolatey (recommended package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required packages
choco install postgresql git make python311

# Verify installation
python --version
```

## Step-by-Step Setup Process

### Phase 1: Repository Setup and Environment Creation

#### 1.1 Clone Repository
```bash
# Clone the repository
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Verify you're on the correct branch
git branch -a
git checkout dev  # or main, depending on current development branch
```

#### 1.2 Python Environment Setup
```bash
# Create virtual environment (Python 3.11.12 required)
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Verify Python version in virtual environment
python --version
# Should output: Python 3.11.12

# Upgrade pip to latest version
pip install --upgrade pip
```

#### 1.3 Environment Configuration
```bash
# Create environment configuration from template
make setup

# This creates .env file with default values
# Edit .env file to add your Alpha Vantage API key:
# ALPHA_VANTAGE_API_KEY=your_api_key_here
```

**Manual .env Configuration** (if make setup doesn't work):
```bash
# Copy template and edit
cp .env.example .env

# Edit .env file with your preferred editor
# Required: Add Alpha Vantage API key
# Optional: Customize database connection settings
```

### Phase 2: Dependency Installation

#### 2.1 Choose Installation Profile

**For Production Use Only**:
```bash
make install
# Installs core dependencies only (FastAPI, PostgreSQL drivers, Airflow)
```

**For Development with Testing** (Recommended):
```bash
make install-dev
# Installs everything: core + testing + code quality tools
# Includes: pytest, pylint, black, isort, mypy, pre-commit
```

**For Testing Environment Only**:
```bash
make install-test
# Installs core + testing dependencies without development tools
```

#### 2.2 Verify Installation
```bash
# Check installed packages
pip list

# Verify key dependencies
python -c "import fastapi, psycopg2, pandas; print('Core dependencies installed')"
python -c "import pytest, pylint; print('Testing tools installed')" # if using install-dev
```

### Phase 3: Database Initialization

#### 3.1 PostgreSQL Service Setup

**macOS (Homebrew)**:
```bash
# Start PostgreSQL service
brew services start postgresql@15

# Create database and user
createdb ticker_converter
psql ticker_converter -c "CREATE USER willhuntleyclarke WITH SUPERUSER;"
```

**Ubuntu/Debian**:
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createdb ticker_converter
sudo -u postgres psql -c "CREATE USER willhuntleyclarke WITH SUPERUSER;"
```

**Windows**:
```powershell
# PostgreSQL should be running as a Windows service
# Open Command Prompt as Administrator
createdb -U postgres ticker_converter
psql -U postgres -c "CREATE USER willhuntleyclarke WITH SUPERUSER;"
```

#### 3.2 Database Schema and Data Initialization
```bash
# Initialize database with schema and sample data
make init-db

# This command:
# 1. Creates all database tables (dimensions, facts, views)
# 2. Loads the last 30 trading days of stock data
# 3. Loads corresponding currency exchange rates
# 4. Creates analytical views for API endpoints
```

**Alternative Database Setup Options**:
```bash
# Schema only (no data loading)
make init-schema

# Smart initialization (uses local data if available)
make smart-init-db

# Manual initialization with specific days
python -m ticker_converter.cli_ingestion --init --days 7
```

### Phase 4: Service Verification

#### 4.1 Start Airflow Services
```bash
# Start Apache Airflow (webserver + scheduler)
make airflow

# Airflow will be available at:
# URL: http://localhost:8080
# Username: admin
# Password: admin123
```

#### 4.2 Start FastAPI Development Server
```bash
# In a separate terminal window (keep Airflow running)
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Start FastAPI development server
make serve

# API will be available at:
# URL: http://localhost:8000
# Documentation: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

#### 4.3 Verify Services are Running
```bash
# Check all services
make status

# Or check individually:
make airflow-status  # Check Airflow scheduler and webserver
curl http://localhost:8000/health  # Check FastAPI health endpoint
```

### Phase 5: Development Workflow Verification

#### 5.1 Run Test Suite
```bash
# Execute full test suite with coverage
make test

# Expected output: All tests pass with >40% coverage
# Coverage report generated in htmlcov/index.html
```

#### 5.2 Code Quality Checks
```bash
# Run all code quality tools
make lint

# This runs:
# - pylint (code analysis)
# - black (formatting check)
# - isort (import sorting check)
# - mypy (type checking)

# Auto-fix formatting issues
make lint-fix
```

#### 5.3 Test Data Pipeline
```bash
# Run daily ETL pipeline manually
make run

# This executes:
# 1. Fetches latest stock data from Alpha Vantage API
# 2. Fetches latest USD/GBP exchange rates
# 3. Transforms data using SQL operations
# 4. Updates analytical views
```

## Makefile Command Reference

### Installation Commands
- `make setup` - Create .env file with default configuration
- `make install` - Install production dependencies only
- `make install-test` - Install production + testing dependencies
- `make install-dev` - Install full development environment (recommended)

### Database Commands
- `make init-db` - Initialize database with last 30 trading days of data
- `make init-schema` - Create database schema without loading data
- `make smart-init-db` - Intelligent initialization with local data priority
- `make teardown-db` - **DANGER**: Completely remove database and all data

### Service Management
- `make airflow` - Start Apache Airflow (webserver + scheduler)
- `make airflow-stop` - Stop all Airflow services
- `make airflow-status` - Check Airflow service status
- `make serve` - Start FastAPI development server
- `make status` - Check all service statuses

### Development Workflow
- `make run` - Execute daily ETL pipeline
- `make test` - Run test suite with coverage reporting
- `make lint` - Run all code quality checks
- `make lint-fix` - Auto-fix code formatting issues
- `make clean` - Clean build artifacts and cache files

### CI/CD Commands
- `make act-pr` - Test GitHub Actions locally (requires act)
- `make help` - Display all available commands with descriptions

## Configuration Details

### Environment Variables (.env)

**Required Configuration**:
```bash
# Alpha Vantage API (REQUIRED)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://willhuntleyclarke@localhost:5432/ticker_converter

# Alternative individual database settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ticker_converter
POSTGRES_USER=willhuntleyclarke
POSTGRES_PASSWORD=  # Leave empty for local development
```

**Optional Configuration**:
```bash
# Airflow Admin User
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin123
AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.local

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# Development Settings
LOG_LEVEL=INFO
DEBUG=True
```

### Alpha Vantage API Key Setup

1. **Get Free API Key**:
   - Visit: https://www.alphavantage.co/support/#api-key
   - Sign up for free account
   - Copy your API key

2. **Add to Environment**:
   ```bash
   # Edit .env file
   ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
   ```

3. **Verify API Key**:
   ```bash
   # Test API connectivity
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(f'API Key configured: {bool(os.getenv(\"ALPHA_VANTAGE_API_KEY\"))}')"
   ```

## Development Tools and IDE Setup

### VS Code Configuration (Recommended)

**Required Extensions**:
- Python (ms-python.python)
- Pylint (ms-python.pylint)
- Black Formatter (ms-python.black-formatter)
- isort (ms-python.isort)
- PostgreSQL (ckolkman.vscode-postgres)

**Workspace Settings** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".mypy_cache": true
    }
}
```

### Pre-commit Hooks Setup

```bash
# Install pre-commit hooks (included in make install-dev)
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files

# Pre-commit will now run automatically on git commit
```

## Troubleshooting Common Issues

### Python Version Problems

**Symptom**: ImportError or syntax errors with modern Python features
```bash
# Verify Python version
python --version

# If not 3.11.12, install correct version:
# macOS with pyenv:
pyenv install 3.11.12
pyenv local 3.11.12

# Ubuntu:
sudo apt install python3.11 python3.11-venv

# Recreate virtual environment
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
```

### Database Connection Issues

**Symptom**: Connection refused or authentication failed
```bash
# Check PostgreSQL service status
# macOS:
brew services list | grep postgresql

# Ubuntu:
sudo systemctl status postgresql

# Test database connection
psql postgresql://willhuntleyclarke@localhost:5432/ticker_converter

# If connection fails, recreate database:
make teardown-db
createdb ticker_converter
make init-db
```

### Airflow Issues

**Symptom**: Airflow web UI not accessible or DAGs not appearing
```bash
# Check Airflow processes
make airflow-status

# Reset Airflow (nuclear option)
make teardown-airflow
make airflow

# Check DAG syntax
python dags/daily_etl_dag.py

# View Airflow logs
tail -f ~/airflow/logs/scheduler/latest/*.log
```

### API Import Errors

**Symptom**: Module not found errors when starting FastAPI
```bash
# Ensure you're in virtual environment
source .venv/bin/activate

# Verify installation
pip list | grep fastapi

# Reinstall dependencies
make install-dev

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Permission Issues

**Symptom**: Permission denied errors on macOS/Linux
```bash
# Fix virtual environment permissions
chmod -R 755 .venv/

# Fix database permissions
sudo chown -R $(whoami) ~/airflow/

# Fix PostgreSQL permissions (if needed)
sudo -u postgres psql -c "ALTER USER willhuntleyclarke CREATEDB;"
```

### Make Command Issues

**Symptom**: Make targets fail or command not found
```bash
# Install make on macOS
xcode-select --install

# Install make on Ubuntu
sudo apt install build-essential

# Run make targets directly if make not available
cat Makefile  # View targets and run commands manually
```

## Performance Optimization for Development

### Database Configuration

**Local PostgreSQL Optimization** (`postgresql.conf`):
```ini
# Memory settings for development
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Connection settings
max_connections = 20
listen_addresses = 'localhost'

# Logging for development
log_statement = 'all'
log_duration = on
log_min_duration_statement = 100ms
```

### Python Development Optimization

**Virtual Environment Optimization**:
```bash
# Use faster pip operations
pip install --upgrade pip setuptools wheel

# Cache pip downloads
pip config set global.cache-dir ~/.pip-cache

# Parallel installation when possible
pip install --use-feature=parallel-installs
```

### IDE Performance Tips

**VS Code Optimization**:
- Exclude unnecessary directories from indexing
- Use workspace-specific Python interpreter
- Enable only required extensions for Python development
- Configure appropriate file watchers and exclusions

## Next Steps After Setup

### 1. Explore the API
```bash
# Open API documentation
open http://localhost:8000/docs  # macOS
# or visit http://localhost:8000/docs in browser

# Test endpoints
curl http://localhost:8000/api/stocks/top-performers
curl http://localhost:8000/api/stocks/AAPL/prices?limit=5
```

### 2. Examine Airflow DAGs
```bash
# Open Airflow web UI
open http://localhost:8080  # macOS
# Username: admin, Password: admin123

# Explore DAG structure
ls dags/
cat dags/daily_etl_dag.py
```

### 3. Review Database Schema
```bash
# Connect to PostgreSQL
psql ticker_converter

# Explore schema
\dt  # List tables
\dv  # List views
SELECT * FROM dim_stocks;
SELECT * FROM fact_stock_prices LIMIT 5;
```

### 4. Run Development Workflow
```bash
# Make code changes, then run quality checks
make lint-fix  # Auto-fix formatting
make test      # Run tests
make run       # Test ETL pipeline
```

## Related Documentation

- [Database Design](../architecture/database_design.md) - PostgreSQL schema details and optimization
- [Airflow Setup](../architecture/airflow_setup.md) - Apache Airflow 3.0.4 configuration and DAG design
- [CLI Usage](../user_guides/cli_usage.md) - Command-line interface reference
- [Production Deployment](production.md) - Production configuration and deployment guide

---

**Last Updated**: August 2025 | **Version**: 1.1.0 | **Setup Time**: ~30 minutes
