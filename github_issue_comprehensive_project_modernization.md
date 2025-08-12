# Project Modernization: Makefile Workflow, pyproject.toml Migration & Development Environment Enhancement

## Summary

Modernize the ticker-converter project with a comprehensive Makefile-based workflow, migrate from requirements.txt to pyproject.toml, and enhance the development environment with advanced tooling. This consolidates project setup, simplifies operations, and improves developer experience.

## Goals

1. **Simplify Project Operations**: Replace complex manual commands with intuitive `make` targets
2. **Modernize Dependency Management**: Migrate from requirements.txt to pyproject.toml with dependency groups
3. **Enhance Code Quality**: Implement comprehensive linting, formatting, and testing tools
4. **Improve Developer Experience**: Standardize setup, operations, and quality gates

## Technical Requirements

### Part 1: Makefile-Based Workflow

#### Core Installation Commands
```makefile
install: ## Install production dependencies only
install-test: ## Install production + testing dependencies  
install-dev: ## Install full development environment
```

#### Core Operational Commands
```makefile
init-db: ## Initialize database with last 30 trading days of data
run: ## Run daily data collection for previous trading day
airflow: ## Start Apache Airflow instance with default user
serve: ## Start FastAPI development server
```

#### Quality & Testing Commands
```makefile
test: ## Run test suite with coverage
lint: ## Run all code quality checks
lint-fix: ## Auto-fix code quality issues
clean: ## Clean build artifacts and cache files
```

### Part 2: pyproject.toml Migration

#### Dependency Groups Structure
```toml
[project]
dependencies = [
    # Core production dependencies
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "psycopg2-binary>=2.9.7",
    "pandas>=2.1.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.4.0",
    "sqlalchemy>=2.0.0",
    "apache-airflow>=2.7.0"
]

[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.24.0"
]
dev = [
    "ticker-converter[test]",
    "pylint>=3.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0"
]
```

### Part 3: Development Environment Enhancement

#### Code Quality Tools Configuration
- **pylint**: Comprehensive static analysis with custom rules
- **black**: Code formatting with 88-character line length
- **isort**: Import sorting with black compatibility
- **mypy**: Static type checking
- **pre-commit**: Automated quality gates

#### Testing Infrastructure
- **pytest**: Modern testing framework with async support
- **pytest-cov**: Coverage reporting with minimum thresholds
- **pytest-asyncio**: FastAPI endpoint testing support

## Acceptance Criteria

### Makefile Implementation
- [ ] All installation commands work correctly (`install`, `install-test`, `install-dev`)
- [ ] Operational commands function properly (`init-db`, `run`, `airflow`, `serve`)
- [ ] `make airflow` displays connection details and creates default user
- [ ] `make serve` displays all FastAPI endpoint URLs
- [ ] Quality commands execute without errors (`test`, `lint`, `lint-fix`)
- [ ] Cross-platform compatibility (macOS, Linux, Windows with WSL)

### pyproject.toml Migration
- [ ] All requirements.txt files removed
- [ ] Dependencies properly categorized in pyproject.toml groups
- [ ] Makefile install commands use pip with pyproject.toml groups
- [ ] No dependency conflicts or missing packages
- [ ] Version constraints maintained from original requirements

### Development Environment
- [ ] pylint achieves 10/10 scores across all modules
- [ ] black formatting applied consistently
- [ ] isort import organization implemented
- [ ] pre-commit hooks configured and functional
- [ ] pytest runs all tests with coverage reporting
- [ ] mypy type checking passes

### Documentation Updates
- [ ] README.md updated with new Makefile-based workflow
- [ ] Installation section reflects new commands
- [ ] Development setup simplified to `make install-dev`
- [ ] Operational workflow documented with make commands
- [ ] Code quality section updated with new tools

## Implementation Notes

### README.md Documentation Requirements
The README.md must be updated to reflect the new Makefile-based workflow:

#### Installation Section
```markdown
## Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Install based on your needs:
make install       # Production pipeline only
make install-test  # Production + testing tools  
make install-dev   # Full development environment
```

### 2. Database Initialization
```bash
# Initialize with last 30 trading days of data
make init-db
```

### 3. Running the Application
```bash
# Daily data collection
make run

# Start services
make airflow  # Apache Airflow (prints connection details)
make serve    # FastAPI endpoints (prints available URLs)
```

### 4. Development Commands
```bash
make test      # Run test suite
make lint      # Code quality checks
make lint-fix  # Auto-fix issues
```
```

#### Core Operational Commands Implementation
```makefile
init-db: ## Initialize database with last 30 trading days of data
	@echo "$(BLUE)Initializing database with historical data...$(NC)"
	@echo "$(YELLOW)This will fetch the last 30 trading days from Alpha Vantage API$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --init --days=30
	@echo "$(GREEN)Database initialized successfully$(NC)"

run: ## Run daily data collection for previous trading day
	@echo "$(BLUE)Running daily data collection...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --daily
	@echo "$(GREEN)Daily data collection completed$(NC)"

airflow: ## Start Apache Airflow instance with default user
	@echo "$(BLUE)Starting Apache Airflow...$(NC)"
	@echo "$(YELLOW)Setting up Airflow database...$(NC)"
	airflow db init
	@echo "$(YELLOW)Creating default admin user...$(NC)"
	airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@ticker-converter.local \
		--password admin123 2>/dev/null || echo "User already exists"
	@echo "$(GREEN)Starting Airflow webserver...$(NC)"
	@echo "$(CYAN)=== AIRFLOW CONNECTION DETAILS ===$(NC)"
	@echo "$(GREEN)URL: http://localhost:8080$(NC)"
	@echo "$(GREEN)Username: admin$(NC)" 
	@echo "$(GREEN)Password: admin123$(NC)"
	@echo "$(CYAN)=================================$(NC)"
	airflow webserver --port 8080

serve: ## Start FastAPI development server
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	@echo "$(CYAN)=== API ENDPOINT URLS ===$(NC)"
	@echo "$(GREEN)Health Check: http://localhost:8000/health$(NC)"
	@echo "$(GREEN)API Docs: http://localhost:8000/docs$(NC)"
	@echo "$(GREEN)Top Performers: http://localhost:8000/api/stocks/top-performers$(NC)"
	@echo "$(GREEN)Performance Details: http://localhost:8000/api/stocks/performance-details$(NC)"
	@echo "$(CYAN)========================$(NC)"
	$(PYTHON) run_api.py
```

### Complete Makefile Structure
```makefile
# Variables
SHELL := /bin/bash
PYTHON := python3
PACKAGE_NAME := ticker_converter
VENV_NAME := .venv

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
CYAN := \033[0;36m
NC := \033[0m

.PHONY: help install install-test install-dev init-db run airflow serve test lint lint-fix clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2}'

# Installation commands
install: ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install -e .
	@echo "$(GREEN)Production installation complete$(NC)"

install-test: ## Install production + testing dependencies
	@echo "$(BLUE)Installing production and testing dependencies...$(NC)"
	pip install -e ".[test]"
	@echo "$(GREEN)Testing environment installation complete$(NC)"

install-dev: ## Install full development environment
	@echo "$(BLUE)Installing full development environment...$(NC)"
	pip install -e ".[dev]"
	pre-commit install
	@echo "$(GREEN)Development environment installation complete$(NC)"

# Operational commands
init-db: ## Initialize database with last 30 trading days of data
	@echo "$(BLUE)Initializing database with historical data...$(NC)"
	@echo "$(YELLOW)This will fetch the last 30 trading days from Alpha Vantage API$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --init --days=30
	@echo "$(GREEN)Database initialized successfully$(NC)"

run: ## Run daily data collection for previous trading day
	@echo "$(BLUE)Running daily data collection...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --daily
	@echo "$(GREEN)Daily data collection completed$(NC)"

airflow: ## Start Apache Airflow instance with default user
	@echo "$(BLUE)Starting Apache Airflow...$(NC)"
	@echo "$(YELLOW)Setting up Airflow database...$(NC)"
	airflow db init
	@echo "$(YELLOW)Creating default admin user...$(NC)"
	airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@ticker-converter.local \
		--password admin123 2>/dev/null || echo "User already exists"
	@echo "$(GREEN)Starting Airflow webserver...$(NC)"
	@echo "$(CYAN)=== AIRFLOW CONNECTION DETAILS ===$(NC)"
	@echo "$(GREEN)URL: http://localhost:8080$(NC)"
	@echo "$(GREEN)Username: admin$(NC)" 
	@echo "$(GREEN)Password: admin123$(NC)"
	@echo "$(CYAN)=================================$(NC)"
	airflow webserver --port 8080

serve: ## Start FastAPI development server
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	@echo "$(CYAN)=== API ENDPOINT URLS ===$(NC)"
	@echo "$(GREEN)Health Check: http://localhost:8000/health$(NC)"
	@echo "$(GREEN)API Docs: http://localhost:8000/docs$(NC)"
	@echo "$(GREEN)Top Performers: http://localhost:8000/api/stocks/top-performers$(NC)"
	@echo "$(GREEN)Performance Details: http://localhost:8000/api/stocks/performance-details$(NC)"
	@echo "$(CYAN)========================$(NC)"
	$(PYTHON) run_api.py

# Quality and testing commands
test: ## Run test suite with coverage
	@echo "$(BLUE)Running test suite...$(NC)"
	pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Test suite completed$(NC)"

lint: ## Run all code quality checks
	@echo "$(BLUE)Running code quality checks...$(NC)"
	pylint $(PACKAGE_NAME)/ api/ *.py
	black --check $(PACKAGE_NAME)/ api/ tests/ *.py
	isort --check-only $(PACKAGE_NAME)/ api/ tests/ *.py
	mypy $(PACKAGE_NAME)/ api/
	@echo "$(GREEN)Code quality checks completed$(NC)"

lint-fix: ## Auto-fix code quality issues
	@echo "$(BLUE)Auto-fixing code quality issues...$(NC)"
	black $(PACKAGE_NAME)/ api/ tests/ *.py
	isort $(PACKAGE_NAME)/ api/ tests/ *.py
	@echo "$(GREEN)Code formatting applied$(NC)"

clean: ## Clean build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "$(GREEN)Cleanup completed$(NC)"
```

### pyproject.toml Complete Configuration
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ticker-converter"
version = "1.0.0"
description = "Stock ticker conversion and analysis pipeline"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Will Huntley-Clarke", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    # Core FastAPI and web framework
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.4.0",

    # Database and data processing
    "psycopg2-binary>=2.9.7",
    "sqlalchemy>=2.0.0",
    "pandas>=2.1.0",

    # HTTP client and utilities
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",

    # Workflow orchestration
    "apache-airflow>=2.7.0",
]

[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.24.0",
]

dev = [
    "ticker-converter[test]",
    # Code quality tools
    "pylint>=3.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",

    # Development tools
    "pre-commit>=3.4.0",
    "ipython>=8.0.0",
    "jupyter>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/willdeeep/ticker-converter"
Repository = "https://github.com/willdeeep/ticker-converter"
Issues = "https://github.com/willdeeep/ticker-converter/issues"

# Tool configurations
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["ticker_converter"]

[tool.pylint.master]
extension-pkg-whitelist = ["pydantic"]

[tool.pylint.messages_control]
disable = [
    "too-few-public-methods",
    "missing-module-docstring",
]

[tool.pylint.format]
max-line-length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--disable-warnings",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["ticker_converter", "api"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pylint-dev/pylint
    rev: v3.0.0
    hooks:
      - id: pylint
        additional_dependencies: [fastapi, uvicorn, psycopg2-binary, pandas, requests, python-dotenv, pydantic, sqlalchemy, apache-airflow]
```

## Testing Strategy

### Installation Testing
1. Test each installation command in clean environments
2. Verify dependency resolution and compatibility
3. Confirm operational commands work after installation

### Functional Testing
1. Test database initialization with `make init-db`
2. Verify daily data collection with `make run`
3. Confirm Airflow startup and user creation
4. Test FastAPI server startup and endpoint accessibility

### Quality Gate Testing
1. Run full test suite with coverage requirements
2. Verify pylint scores meet 10/10 standard
3. Confirm code formatting consistency
4. Test pre-commit hook functionality

## Priority & Effort

- **Priority**: High (simplifies entire development workflow)
- **Effort**: Large (3-4 days for complete implementation)
- **Dependencies**: None (self-contained modernization)
- **Impact**: High (affects all future development and operations)

## Related Work

This issue consolidates and modernizes the project infrastructure, building upon:
- Existing FastAPI implementation (issue #6)
- Current testing infrastructure
- Established code quality standards (10/10 pylint scores)

## Definition of Done

- [ ] All Makefile commands execute successfully across platforms
- [ ] pyproject.toml replaces all requirements.txt files
- [ ] Code quality tools achieve expected scores/formatting
- [ ] README.md reflects new workflow
- [ ] Pre-commit hooks prevent quality regressions
- [ ] Installation process simplified to single commands
- [ ] Operational workflow streamlined with make targets
- [ ] Development environment setup automated
- [ ] All tests pass with coverage requirements met
