# CLI Usage Guide

## Executive Summary

This guide provides comprehensive documentation for all command-line interfaces available in the ticker-converter project. The CLI system emphasizes **environment-driven configuration**, **7-stage quality pipeline**, and **zero hardcoded values** through Make-based commands, Python CLI tools, and git-based development workflows.

**CLI Value Proposition**: Master the complete command-line workflow to reduce development time, ensure consistent quality through comprehensive validation, and automate complex operational tasks across development, testing, and production environments with environment-driven configuration management.

## Make Command Reference (Primary Interface)

### Command Categories Overview

The ticker-converter project uses **GNU Make** as the primary interface for all development and operational tasks. All commands are designed to be self-documenting, fail-safe, and work consistently across macOS, Linux, and Windows (WSL) environments.

```bash
# Display all available commands with descriptions
make help
```

**For detailed command reference**: See [Makefile Target Reference](makefile_reference.md) for comprehensive documentation of all available targets, parameters, and environment variables.

### Setup and Installation Commands

#### Environment Setup
```bash
# Guided environment configuration with validation
make setup
# - Creates .env from .env.example with guided customization
# - Validates required environment variables
# - Provides helpful prompts for configuration
# - Safe to run multiple times (preserves existing .env)

# Example interactive setup:
# Setting up ticker-converter environment...
# Alpha Vantage API key required. Get one at: https://www.alphavantage.co/support/#api-key
# Enter your API key: [user input]
# PostgreSQL configuration...
# Database host [localhost]: [user input or default]
# Environment configured successfully!
```

#### Dependency Installation
```bash
# Install production dependencies only
make install
# - Upgrades pip to latest version
# - Installs core dependencies: FastAPI, PostgreSQL drivers, Pandas
# - Suitable for production deployment
# - Estimated time: 30-60 seconds

# Install production + testing dependencies
make install-test
# - Everything in 'install' plus testing tools
# - Includes: pytest, coverage, factory-boy
# - Suitable for CI/CD environments
# - Estimated time: 45-75 seconds

# Install full development environment (recommended)
make install-dev
# - Everything in 'install-test' plus development tools
# - Includes: black, isort, pylint, mypy, pre-commit
# - Suitable for local development
# - Estimated time: 60-90 seconds
```

### Database Management Commands

#### Database Initialization
```bash
# Initialize PostgreSQL database with default configuration
make init-db
# - Starts PostgreSQL service (macOS: brew services, Linux: systemctl)
# - Creates database user and database
# - Executes schema creation scripts from sql/ddl/
# - Loads sample data for development
# - Estimated time: 2-3 minutes

# Database initialization process:
# 1. Check PostgreSQL service status
# 2. Start PostgreSQL if not running
# 3. Create user 'willhuntleyclarke' with superuser privileges
# 4. Create database 'ticker_converter'
# 5. Execute DDL scripts in order:
#    - 001_create_dimensions.sql
#    - 002_create_facts.sql  
#    - 003_create_views.sql
#    - 004_create_indexes.sql
# 6. Verify database connectivity
```

#### Alternative Database Commands
```bash
# Schema-only initialization (no data loading)
make init-schema
# - Creates database structure without loading sample data
# - Faster initialization for testing environments

# Smart initialization (uses local data if available)
make smart-init-db
# - Checks for existing local data files
# - Uses cached data to speed up initialization
# - Falls back to API fetching if no local data
```

### Service Management Commands

#### Airflow Operations
```bash
# Start Apache Airflow with project-local configuration
make airflow
# - Sets AIRFLOW_HOME to ./airflow (project-local)
# - Sets DAGs folder to ./dags
# - Disables example DAGs for cleaner interface
# - Uses PostgreSQL as Airflow metadata database
# - Creates default admin user (admin/admin123)
# - Starts scheduler and webserver
# - Available at: http://localhost:8080

# Airflow startup process:
# 1. Load environment variables from .env
# 2. Set project-local Airflow configuration
# 3. Initialize Airflow metadata database
# 4. Create admin user if not exists
# 5. Start scheduler in background
# 6. Start webserver (blocking process)

# Fix Airflow 3.0.4 configuration deprecation warnings
make airflow-config
# - Updates deprecated configuration settings
# - Ensures compatibility with Airflow 3.0.4
# - Fixes authentication backend configuration
```

#### FastAPI Development Server
```bash
# Start FastAPI development server (separate terminal required)
make serve
# - Starts uvicorn development server
# - Hot-reload enabled for development
# - Available at: http://localhost:8000
# - API documentation: http://localhost:8000/docs
# - Health check: http://localhost:8000/health

# Note: Run this in a separate terminal while Airflow is running
```

#### Service Status and Control
```bash
# Check status of all services
make status
# - Checks Airflow scheduler and webserver processes
# - Tests FastAPI health endpoint
# - Verifies PostgreSQL connectivity
# - Reports service health and availability

# Stop Airflow services
make airflow-close
# - Terminates all Airflow processes (scheduler, webserver)
# - Clean shutdown with process cleanup
# - Safe to run multiple times

# Stop PostgreSQL service
make db-close
# - Stops PostgreSQL service (macOS: brew services, Linux: systemctl)
# - Graceful shutdown of database connections
# - Safe to run multiple times
```

### Testing and Quality Commands

#### Test Execution
```bash
# Run complete test suite with coverage
make test
# - Executes all unit and integration tests
# - Generates coverage report (HTML and terminal)
# - Coverage report saved to htmlcov/index.html
# - Target coverage: 70%+ (current: 70% maintained consistently)
# - 245+ tests passing, 0 failing maintained across development
# - Estimated time: 2-5 minutes

# Test execution includes:
# - Unit tests: src/ module testing with comprehensive coverage
# - Integration tests: database and API testing
# - Coverage analysis: line and branch coverage
# - Quality validation: Ensures 70%+ coverage threshold
# - HTML report generation for detailed analysis

# Run CI-compatible tests
make test-ci
# - Same as 'test' but with XML coverage output
# - Environment-driven configuration for CI/CD pipelines
# - Configurable coverage thresholds via PYTEST_COVERAGE_THRESHOLD
# - Machine-readable output formats
```

#### Code Quality Commands
```bash
# Run comprehensive 7-stage quality pipeline
make quality
# - Stage 1: Makefile structure validation (checkmake)
# - Stage 2: SQL quality standards (sqlfluff)
# - Stage 3: Code formatting verification (Black)
# - Stage 4: Import sorting verification (isort)
# - Stage 5: Code analysis and style checking (Pylint 10.00/10)
# - Stage 6: Static type checking (MyPy)
# - Stage 7: Test suite execution with coverage validation
# - Reports all issues without fixing

# Individual quality checks
make lint           # Python code quality only
make lint-sql       # SQL quality validation
make lint-makefile  # Makefile structure validation

# Code quality tools configuration:
# - Black: 88 character line length, Python 3.11+ target
# - isort: Black-compatible import sorting
# - Pylint: 10.00/10 perfect score requirement
# - MyPy: Strict type checking with gradual adoption
# - sqlfluff: PostgreSQL dialect, uppercase keywords

# Auto-fix code quality issues
make lint-fix
# - Black: Auto-format all Python files
# - isort: Auto-sort imports in all files
# - Non-destructive: only fixes formatting, not logic
# - Safe to run before commits
```

#### GitHub Actions Local Testing
```bash
# Run GitHub Actions workflow locally using act
make act-pr
# - Requires 'act' tool installation
# - Runs pull request workflow locally
# - Tests CI/CD pipeline before pushing
# - Supports both x86_64 and ARM64 architectures
# - Estimated time: 5-10 minutes

# Prerequisites for act:
# macOS: brew install act
# Linux: Download from GitHub releases
# Windows: Use WSL2 with Linux installation
```

### Data Pipeline Commands

#### ETL Pipeline Execution
```bash
# Execute daily ETL pipeline manually
make run
# - Fetches latest stock data from Alpha Vantage API
# - Fetches latest USD/GBP exchange rates
# - Transforms data using SQL operations
# - Updates analytical views and aggregations
# - Validates data quality and completeness
# - Estimated time: 3-5 minutes (depending on API response)

# ETL pipeline stages:
# 1. Data extraction: Stock prices and currency rates
# 2. Data validation: Quality checks and schema validation
# 3. Data transformation: SQL-based processing
# 4. Data loading: Insert into dimensional tables
# 5. View refresh: Update analytical views
# 6. Quality verification: Post-load data checks
```

### Cleanup and Maintenance Commands

#### Regular Cleanup
```bash
# Clean build artifacts and cache files
make clean
# - Removes __pycache__ directories
# - Removes .pytest_cache directories
# - Removes .mypy_cache directories
# - Removes build artifacts (.egg-info, dist/)
# - Removes coverage reports
# - Preserves virtual environment and source code
# - Safe to run regularly
```

#### Comprehensive Teardown Commands
```bash
# Remove all cache and temporary files
make teardown-cache
# - Everything in 'clean' plus additional caches
# - Removes .ruff_cache, .tox directories
# - Removes all .pyc files
# - Deep cleanup for troubleshooting
# - Safe and reversible

# Remove environment configuration (DESTRUCTIVE)
make teardown-env
# - Prompts for confirmation (y/N)
# - Removes .env file
# - Removes .venv/ directory
# - Requires complete setup after running
# - Use for clean slate development

# Remove Airflow installation (DESTRUCTIVE)
make teardown-airflow
# - Prompts for confirmation (y/N)
# - Stops all Airflow processes
# - Removes airflow/ directory
# - Removes all Airflow metadata and logs
# - Use for Airflow troubleshooting

# Remove database (DESTRUCTIVE)
make teardown-db
# - Prompts for confirmation (y/N)
# - Stops PostgreSQL service
# - Database files preserved (system-level removal required)
# - Use for database troubleshooting
```

## Python CLI Tools

### Direct Python Module Execution

#### Data Ingestion CLI
```bash
# Execute data ingestion with custom parameters
python -m ticker_converter.cli_ingestion --help

# Initialize database with specific days of data
python -m ticker_converter.cli_ingestion --init --days 7

# Fetch data for specific stocks
python -m ticker_converter.cli_ingestion --stocks AAPL,MSFT --days 30

# Run data quality checks only
python -m ticker_converter.cli_ingestion --validate-only

# Verbose output with debug logging
python -m ticker_converter.cli_ingestion --verbose --days 5
```

#### Database Management CLI
```bash
# Database schema management
python scripts/setup_database.py --help

# Create schema only (no data)
python scripts/setup_database.py --schema-only

# Reset database (drops and recreates)
python scripts/setup_database.py --reset

# Production initialization
python scripts/setup_database.py --production
```

#### Data Validation CLI
```bash
# Comprehensive data validation
python scripts/data_validation.py --help

# Check database connectivity
python scripts/data_validation.py --check-connection

# Validate data freshness
python scripts/data_validation.py --check-freshness

# Full data quality audit
python scripts/data_validation.py --full-check

# Test API endpoints
python scripts/data_validation.py --test-api
```

### Utility Scripts

#### Demo and Testing Scripts
```bash
# Demonstrate pipeline capabilities
python scripts/demo_capabilities.py
# - Shows end-to-end data flow
# - Displays sample API responses
# - Tests all major components
# - Generates summary report

# Test complete workflow
python scripts/test_workflow.py
# - Automated testing of full workflow
# - Database → ETL → API → Validation
# - Performance benchmarking
# - Error simulation and recovery
```

## Development Workflow Integration

### Git Workflow with Make Commands

#### Complete Development Cycle
```bash
# 1. Setup new development environment
make setup
make install-dev
make init-db

# 2. Start development services
make airflow          # Terminal 1
make serve           # Terminal 2

# 3. Development cycle
# ... make code changes ...

# 4. Quality checks before commit
make lint-fix        # Auto-fix formatting
make quality         # Run comprehensive 7-stage quality pipeline
make test           # Run tests (70%+ coverage maintained)

# 5. Test changes
make run            # Test ETL pipeline
curl http://localhost:8000/health  # Test API

# 6. Commit and push
git add .
git commit -m "feat: implement new feature"
git push origin feature-branch
```

#### CI/CD Integration
```bash
# Local CI/CD testing
make act-pr         # Test GitHub Actions locally
make test-ci        # CI-compatible test execution  
make quality        # Complete 7-stage quality pipeline

# Production deployment preparation
make clean          # Clean environment
make install        # Production dependencies only
make quality        # Final quality validation
make test-ci        # Final test execution
```

### Environment Management

#### Development Environment Switching
```bash
# Switch to production environment
cp .env.example .env.production
# Edit .env.production with production values
export ENV_FILE=.env.production

# Switch back to development
export ENV_FILE=.env

# Verify current environment
python -c "import os; print(f'Environment: {os.getenv(\"ENVIRONMENT\", \"development\")}')"
```

#### Multiple Environment Support
```bash
# Development environment
make setup                    # Creates .env
make install-dev             # Full development tools

# Testing environment  
cp .env .env.test            # Copy and modify for testing
make install-test            # Testing dependencies only

# Production environment
cp .env .env.production      # Copy and modify for production
make install                 # Production dependencies only
```

## Advanced Usage Patterns

### Automation and Scripting

#### Automated Setup Script
```bash
#!/bin/bash
# Complete automated setup
make setup
make install-dev
make init-db
make airflow &
sleep 30
make serve &
echo "Development environment ready!"
echo "Airflow: http://localhost:8080 (admin/admin123)"
echo "API: http://localhost:8000/docs"
```

#### Scheduled Operations
```bash
# Daily data refresh (crontab entry)
0 6 * * 1-5 cd /opt/ticker-converter && make run

# Weekly full refresh
0 2 * * 0 cd /opt/ticker-converter && make teardown-cache && make init-db

# Daily quality checks
0 8 * * * cd /opt/ticker-converter && python scripts/data_validation.py --full-check
```

### Performance Optimization

#### Development Performance
```bash
# Fast development restart
make airflow-close
make airflow &
# Airflow restart without full teardown

# Quick data refresh
python -m ticker_converter.cli_ingestion --days 1
# Single day update instead of full refresh

# Targeted testing
python -m pytest tests/unit/specific_test.py -v
# Run specific tests instead of full suite
```

#### Production Performance
```bash
# Production deployment with minimal downtime
make clean
make install
make test-ci
# Gradual service restart with health checks
```

## Error Handling and Troubleshooting

### Common Error Patterns

#### Database Connection Errors
```bash
# Diagnosis
make status                  # Check service status
psql -h localhost -U willhuntleyclarke -d ticker_converter

# Resolution
make db-close
make init-db                # Reinitialize database
```

#### Airflow Issues
```bash
# Diagnosis
make airflow-status         # Check Airflow processes
tail -f airflow/logs/scheduler/latest/*.log

# Resolution
make teardown-airflow       # Complete Airflow reset
make airflow                # Fresh start
```

#### API Connection Issues
```bash
# Diagnosis
curl http://localhost:8000/health
python scripts/test_api.py

# Resolution
make serve                  # Restart FastAPI server
make lint-fix && make test  # Fix code issues
```

### Diagnostic Commands

#### System Health Check
```bash
# Complete system diagnosis
echo "=== System Health Check ==="
make status
python scripts/data_validation.py --check-connection
curl -f http://localhost:8000/health
curl -f http://localhost:8080/health
echo "=== Health Check Complete ==="
```

#### Performance Diagnostics
```bash
# Performance analysis
time make test              # Test execution time
time make run              # ETL pipeline performance
python scripts/demo_capabilities.py  # End-to-end performance
```

## Best Practices and Tips

### Development Best Practices
1. **Always use make commands**: Consistent, documented, and reliable
2. **Run make lint-fix before commits**: Automated code formatting
3. **Use make test regularly**: Catch issues early in development
4. **Start with make setup**: Consistent environment initialization
5. **Check make status**: Monitor service health during development

### Production Best Practices
1. **Use make install for production**: Minimal dependencies
2. **Run make test-ci before deployment**: Comprehensive validation
3. **Monitor with make status**: Regular health checks
4. **Backup before make teardown-***: Destructive operations
5. **Document environment-specific configurations**: Production vs development

### Performance Best Practices
1. **Use make clean regularly**: Remove build artifacts
2. **Run make smart-init-db**: Faster initialization with cached data
3. **Use targeted testing**: Specific tests during development
4. **Monitor resource usage**: During make airflow and make serve

This comprehensive CLI guide provides complete command-line mastery for efficient development, testing, and operational workflows in the ticker-converter project.

---

**Last Updated**: August 2025 | **Version**: 2.0.0 | **Mastery Level**: Expert CLI Usage
