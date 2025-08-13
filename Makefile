# Variables
SHELL := /bin/bash
PYTHON := python3
PACKAGE_NAME := ticker_converter
VENV_NAME := .venv

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m

.PHONY: help setup install install-test install-dev init-db airflow test test-ci act-pr lint lint-fix airflow-close db-close clean teardown-cache teardown-env teardown-airflow teardown-db

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help message
	@echo -e "$(CYAN)Ticker Converter - Available Commands:$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Help:$(NC)"
	@grep -E '^(help):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Setup and run:$(NC)"
	@grep -E '^(setup|install|install-test|install-dev|init-db|airflow):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Testing:$(NC)"
	@grep -E '^(test|test-ci|act-pr|lint|lint-fix):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Shutdown and clean:$(NC)"
	@grep -E '^(airflow-close|db-close|clean):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Teardown:$(NC)"
	@grep -E '^(teardown-cache|teardown-env|teardown-airflow|teardown-db):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# SETUP AND RUN
# ============================================================================

setup: ## Sets up environment variables
	@echo "$(BLUE)Setting up environment variables...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(CYAN)Please review and update the .env file with your specific values.$(NC)"; \
		echo "$(CYAN)Default values have been set from .env.example$(NC)"; \
	else \
		echo "$(GREEN).env file already exists$(NC)"; \
	fi

install: ## Install all running dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -e .
	@echo "$(GREEN)Production dependencies installed$(NC)"

install-test: ## Install production + testing dependencies
	@echo "$(BLUE)Installing production and testing dependencies...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -e ".[test]"
	@echo "$(GREEN)Production and testing dependencies installed$(NC)"

install-dev: ## Install full development environment
	@echo "$(BLUE)Installing full development environment...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -e ".[dev,test]"
	@echo "$(GREEN)Full development environment installed$(NC)"

init-db: ## Initialise PostgreSQL database using defaults
	@echo "$(BLUE)Initializing PostgreSQL database...$(NC)"
	@$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion init-db
	@echo "$(GREEN)Database initialization completed$(NC)"

airflow: ## Start Apache Airflow instance with default user
	@echo "$(BLUE)Starting Apache Airflow...$(NC)"
	@$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion start-airflow
	@echo "$(CYAN)Airflow should be available at: http://localhost:8080$(NC)"

# ============================================================================
# TESTING
# ============================================================================

test: ## Run test suite with coverage
	@echo "$(BLUE)Running test suite with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Tests completed$(NC)"

test-ci: ## Run all CI tests
	@echo "$(BLUE)Running CI tests...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=xml --cov-fail-under=80
	@echo "$(GREEN)CI tests completed$(NC)"

act-pr: ## Runs local GitHub Actions workflow using Act
	@echo "$(BLUE)Running GitHub Actions workflow locally...$(NC)"
	@if command -v act >/dev/null 2>&1; then \
		if [[ "$$(uname -m)" == "arm64" ]]; then \
			act pull_request --container-architecture linux/amd64; \
		else \
			act pull_request; \
		fi; \
	else \
		echo "$(RED)Error: 'act' is not installed. Install it from: https://github.com/nektos/act$(NC)"; \
		exit 1; \
	fi

lint: ## Run all code quality checks
	@echo "$(BLUE)Running code quality checks...$(NC)"
	@$(PYTHON) -m ruff check .
	@$(PYTHON) -m ruff format --check .
	@$(PYTHON) -m mypy $(PACKAGE_NAME)
	@echo "$(GREEN)Code quality checks completed$(NC)"

lint-fix: ## Auto-fix code quality issues
	@echo "$(BLUE)Auto-fixing code quality issues...$(NC)"
	@$(PYTHON) -m ruff check --fix .
	@$(PYTHON) -m ruff format .
	@echo "$(GREEN)Code quality fixes applied$(NC)"

# ============================================================================
# SHUTDOWN AND CLEAN
# ============================================================================

airflow-close: ## Closes down Airflow
	@echo "$(BLUE)Closing Airflow...$(NC)"
	@if pgrep -f "airflow" > /dev/null; then \
		pkill -f "airflow" && echo "$(GREEN)Airflow stopped$(NC)"; \
	else \
		echo "$(YELLOW)Airflow is not running$(NC)"; \
	fi

db-close: ## Shuts down local PostgreSQL instance
	@echo "$(BLUE)Shutting down PostgreSQL...$(NC)"
	@if pgrep -f "postgres" > /dev/null; then \
		$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion stop-db && echo "$(GREEN)PostgreSQL stopped$(NC)"; \
	else \
		echo "$(YELLOW)PostgreSQL is not running$(NC)"; \
	fi

clean: ## Clean build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage
	@echo "$(GREEN)Cleanup completed$(NC)"

# ============================================================================
# TEARDOWN
# ============================================================================

teardown-cache: ## Deletes all build artifacts and testing cache files
	@echo "$(BLUE)Removing all cache folders and temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf build/ dist/ .coverage
	@echo "$(GREEN)Cache cleanup completed$(NC)"

teardown-env: ## Remove environment file and virtual environment
	@echo "$(RED)WARNING: This will delete .env and .venv/ directory$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Removing environment files...$(NC)"
	@rm -rf .env .venv/
	@echo "$(GREEN)Environment cleanup completed$(NC)"

teardown-airflow: ## Shutdown Airflow and remove all Airflow files
	@echo "$(RED)WARNING: This will shutdown Airflow and delete all airflow/ files$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Shutting down Airflow and removing files...$(NC)"
	@if pgrep -f "airflow" > /dev/null; then \
		pkill -f "airflow"; \
		echo "$(YELLOW)Airflow processes stopped$(NC)"; \
	fi
	@rm -rf airflow/
	@echo "$(GREEN)Airflow teardown completed$(NC)"

teardown-db: ## Shutdown and remove PostgreSQL database
	@echo "$(RED)WARNING: This will shutdown PostgreSQL and delete the database$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Shutting down and removing PostgreSQL database...$(NC)"
	@$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion teardown-db
	@echo "$(GREEN)Database teardown completed$(NC)"
