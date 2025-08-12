# Variables
SHELL := /bin/bash
PYTHON := python3
PACKAGE_NAME := ticker_converter
VENV_NAME := .venv
ENV_FILE := .env

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

# Load environment variables from .env if it exists
ifneq (,$(wildcard $(ENV_FILE)))
    include $(ENV_FILE)
endif

.PHONY: help install install-test install-dev setup-env init-db init-schema run airflow airflow-stop airflow-status serve test lint lint-fix lint-dags clean teardown teardown-db teardown-venv act-pr

help: ## Show this help message
	@echo -e "$(BLUE)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup-env: ## Setup environment configuration (.env file and API key)
	@echo -e "$(BLUE)Setting up environment configuration...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo -e "$(YELLOW)No .env file found. Creating one...$(NC)"; \
		echo "# Financial Data API Configuration" > $(ENV_FILE); \
		echo "# Generated on $$(date)" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# Alpha Vantage API (required for stock data)" >> $(ENV_FILE); \
		echo "# Get your free API key at: https://www.alphavantage.co/support/#api-key" >> $(ENV_FILE); \
		read -p "Enter your Alpha Vantage API key: " api_key; \
		echo "ALPHA_VANTAGE_API_KEY=$$api_key" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# PostgreSQL Database Configuration" >> $(ENV_FILE); \
		echo "POSTGRES_HOST=localhost" >> $(ENV_FILE); \
		echo "POSTGRES_PORT=5432" >> $(ENV_FILE); \
		echo "POSTGRES_DB=ticker_converter" >> $(ENV_FILE); \
		echo "POSTGRES_USER=postgres" >> $(ENV_FILE); \
		echo "POSTGRES_PASSWORD=postgres" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# Airflow Configuration" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_USERNAME=admin" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_PASSWORD=admin123" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.local" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_FIRSTNAME=Admin" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_LASTNAME=User" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# API Configuration" >> $(ENV_FILE); \
		echo "API_TIMEOUT=30" >> $(ENV_FILE); \
		echo "MAX_RETRIES=3" >> $(ENV_FILE); \
		echo "RATE_LIMIT_DELAY=1.0" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# FastAPI Settings" >> $(ENV_FILE); \
		echo "DEBUG=false" >> $(ENV_FILE); \
		echo "CORS_ORIGINS=*" >> $(ENV_FILE); \
		echo "LOG_LEVEL=INFO" >> $(ENV_FILE); \
		echo -e "$(GREEN)Environment file created successfully!$(NC)"; \
	else \
		echo -e "$(GREEN)Environment file already exists.$(NC)"; \
		if [ -z "$(ALPHA_VANTAGE_API_KEY)" ]; then \
			echo -e "$(YELLOW)Warning: ALPHA_VANTAGE_API_KEY not set in .env file$(NC)"; \
			read -p "Enter your Alpha Vantage API key: " api_key; \
			if grep -q "ALPHA_VANTAGE_API_KEY=" $(ENV_FILE); then \
				sed -i.bak "s/ALPHA_VANTAGE_API_KEY=.*/ALPHA_VANTAGE_API_KEY=$$api_key/" $(ENV_FILE); \
				rm -f $(ENV_FILE).bak; \
			else \
				echo "ALPHA_VANTAGE_API_KEY=$$api_key" >> $(ENV_FILE); \
			fi; \
			echo -e "$(GREEN)API key updated in .env file$(NC)"; \
		else \
			echo -e "$(GREEN)API key is configured$(NC)"; \
		fi; \
	fi

install: ## Install production dependencies
	@echo -e "$(BLUE)Installing production dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e .
	@echo -e "$(GREEN)Production dependencies installed successfully$(NC)"

install-test: ## Install test dependencies
	@echo -e "$(BLUE)Installing test dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e ".[test]"
	@echo -e "$(GREEN)Test dependencies installed successfully$(NC)"

install-dev: ## Install development dependencies  
	@echo -e "$(BLUE)Installing development dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e ".[dev]"
	@echo -e "$(GREEN)Development dependencies installed successfully$(NC)"

init-db: ## Initialize database with smart data loading (local data priority)
	@echo "$(BLUE)Initializing database with smart data loading...$(NC)"
	@echo "$(YELLOW)Priority: local real data > dummy data (1 day) > API minimal fetch$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --smart-init
	@echo "$(GREEN)Database initialized successfully$(NC)"

init-schema: ## Initialize database schema only (no data loading)
	@echo "$(BLUE)Initializing database schema only...$(NC)"
	@echo "$(YELLOW)Creating tables, views, and indexes from DDL files$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --schema-only
	@echo "$(GREEN)Database schema created successfully$(NC)"= .env

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
CYAN := \033[0;36m
RED := \033[0;31m
NC := \033[0m

# Load environment variables if .env exists
ifneq (,$(wildcard $(ENV_FILE)))
    include $(ENV_FILE)
    export
endif

.PHONY: help install install-test install-dev setup-env init-db init-schema run airflow airflow-stop airflow-status serve test lint lint-fix lint-dags clean teardown teardown-db teardown-venv act-pr

help: ## Show this help message
	@echo -e "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## .*$$/ {printf "  \033[0;36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# Environment setup
setup-env: ## Set up environment configuration (.env file)
	@echo -e "$(BLUE)Setting up environment configuration...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo -e "$(YELLOW)No .env file found. Creating one...$(NC)"; \
		echo "# Financial Data API Configuration" > $(ENV_FILE); \
		echo "# Generated on $$(date)" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# Alpha Vantage API (required for stock data)" >> $(ENV_FILE); \
		echo "# Get your free API key at: https://www.alphavantage.co/support/#api-key" >> $(ENV_FILE); \
		read -p "Enter your Alpha Vantage API key: " api_key; \
		echo "ALPHA_VANTAGE_API_KEY=$$api_key" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# PostgreSQL Database Configuration" >> $(ENV_FILE); \
		echo "POSTGRES_HOST=localhost" >> $(ENV_FILE); \
		echo "POSTGRES_PORT=5432" >> $(ENV_FILE); \
		echo "POSTGRES_DB=ticker_converter" >> $(ENV_FILE); \
		echo "POSTGRES_USER=postgres" >> $(ENV_FILE); \
		echo "POSTGRES_PASSWORD=postgres" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# Airflow Configuration" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_USERNAME=admin" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_PASSWORD=admin123" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.local" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_FIRSTNAME=Admin" >> $(ENV_FILE); \
		echo "AIRFLOW_ADMIN_LASTNAME=User" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# API Configuration" >> $(ENV_FILE); \
		echo "API_TIMEOUT=30" >> $(ENV_FILE); \
		echo "MAX_RETRIES=3" >> $(ENV_FILE); \
		echo "RATE_LIMIT_DELAY=1.0" >> $(ENV_FILE); \
		echo "" >> $(ENV_FILE); \
		echo "# FastAPI Settings" >> $(ENV_FILE); \
		echo "DEBUG=false" >> $(ENV_FILE); \
		echo "CORS_ORIGINS=*" >> $(ENV_FILE); \
		echo "LOG_LEVEL=INFO" >> $(ENV_FILE); \
		echo -e "$(GREEN)Environment file created successfully!$(NC)"; \
	else \
		echo -e "$(GREEN)Environment file already exists.$(NC)"; \
		if [ -z "$(ALPHA_VANTAGE_API_KEY)" ]; then \
			echo -e "$(YELLOW)Warning: ALPHA_VANTAGE_API_KEY not set in .env file$(NC)"; \
			read -p "Enter your Alpha Vantage API key: " api_key; \
			if grep -q "ALPHA_VANTAGE_API_KEY=" $(ENV_FILE); then \
				sed -i.bak "s/ALPHA_VANTAGE_API_KEY=.*/ALPHA_VANTAGE_API_KEY=$$api_key/" $(ENV_FILE); \
				rm -f $(ENV_FILE).bak; \
			else \
				echo "ALPHA_VANTAGE_API_KEY=$$api_key" >> $(ENV_FILE); \
			fi; \
			echo -e "$(GREEN)API key updated in .env file$(NC)"; \
		else \
			echo -e "$(GREEN)API key is configured$(NC)"; \
		fi; \
	fi
	@echo -e "$(CYAN)Environment setup complete!$(NC)"

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
init-db: ## Initialize database with minimal sample data (1 stock, 1 currency record)
	@echo -e "$(BLUE)Initializing database with sample data...$(NC)"
	@echo -e "$(YELLOW)This will fetch one currency exchange rate and Apple stock data$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --init --days=1
	@echo -e "$(GREEN)Database initialized successfully$(NC)"

init-db-full: ## Initialize database with last 30 trading days of data
	@echo -e "$(BLUE)Initializing database with full historical data...$(NC)"
	@echo -e "$(YELLOW)This will fetch the last 30 trading days from Alpha Vantage API$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --init --days=30
	@echo -e "$(GREEN)Database initialized successfully$(NC)"

run: ## Run daily data collection for previous trading day
	@echo "$(BLUE)Running daily data collection...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --daily
	@echo "$(GREEN)Daily data collection completed$(NC)"

airflow: setup-env ## Start Apache Airflow instance with default user
	@echo -e "$(BLUE)Starting Apache Airflow...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --airflow-setup
	@echo -e "$(GREEN)Airflow setup completed$(NC)"
	@echo -e "$(CYAN)=== AIRFLOW CONNECTION DETAILS ===$(NC)"
	@echo -e "$(GREEN)URL: http://localhost:8080$(NC)"
	@if [ -n "$(AIRFLOW_ADMIN_USERNAME)" ]; then \
		echo -e "$(GREEN)Username: $(AIRFLOW_ADMIN_USERNAME)$(NC)"; \
		echo -e "$(GREEN)Password: $(AIRFLOW_ADMIN_PASSWORD)$(NC)"; \
	else \
		echo -e "$(GREEN)Username: admin$(NC)"; \
		echo -e "$(GREEN)Password: admin123$(NC)"; \
	fi
	@echo -e "$(CYAN)=================================$(NC)"
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
	pytest tests/ --cov=src/$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Test suite completed$(NC)"

lint: ## Run all code quality checks
	@echo "$(BLUE)Running code quality checks...$(NC)"
	pylint src/$(PACKAGE_NAME)/ api/ run_api.py
	black --check src/$(PACKAGE_NAME)/ api/ tests/ run_api.py
	isort --check-only src/$(PACKAGE_NAME)/ api/ tests/ run_api.py
	mypy src/$(PACKAGE_NAME)/ api/
	@echo "$(GREEN)Code quality checks completed$(NC)"

lint-fix: ## Auto-fix code quality issues
	@echo "$(BLUE)Auto-fixing code quality issues...$(NC)"
	black src/$(PACKAGE_NAME)/ api/ tests/ run_api.py
	isort src/$(PACKAGE_NAME)/ api/ tests/ run_api.py
	@echo "$(GREEN)Code formatting applied$(NC)"

lint-dags: ## Run pylint specifically for Airflow DAGs
	@echo -e "$(BLUE)Running pylint checks on Airflow DAGs...$(NC)"
	pylint dags/ --disable=pointless-statement
	@echo -e "$(GREEN)DAG linting completed$(NC)"

# Cleanup commands
teardown: ## Remove cache directories and temporary files
	@echo -e "$(BLUE)Removing cache directories and temporary files...$(NC)"
	@echo -e "$(YELLOW)Removing Python cache directories...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo -e "$(GREEN)Cache cleanup completed$(NC)"

teardown-db: ## Remove PostgreSQL database (WARNING: This will delete all data!)
	@echo -e "$(RED)WARNING: This will permanently delete all database objects and data!$(NC)"
	@echo -e "$(YELLOW)This operation cannot be undone.$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --teardown
	@echo -e "$(GREEN)Database teardown completed$(NC)"

airflow-stop: ## Stop Apache Airflow services
	@echo -e "$(YELLOW)Stopping Apache Airflow services...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --airflow-teardown
	@echo -e "$(GREEN)Airflow services stopped$(NC)"

airflow-status: ## Check Apache Airflow status
	@echo -e "$(BLUE)Checking Airflow status...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --airflow-status

teardown-venv: ## Remove virtual environment directory
	@echo -e "$(YELLOW)Removing virtual environment directory...$(NC)"
	@if [ -d "$(VENV_NAME)" ]; then \
		rm -rf "$(VENV_NAME)"; \
		echo -e "$(GREEN)Virtual environment removed$(NC)"; \
	else \
		echo -e "$(YELLOW)Virtual environment directory not found$(NC)"; \
	fi

clean: ## Clean build artifacts and cache files (same as teardown plus build artifacts)
	@echo -e "$(BLUE)Cleaning build artifacts and cache files...$(NC)"
	$(MAKE) teardown
	@echo -e "$(YELLOW)Removing build artifacts...$(NC)"
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo -e "$(GREEN)Cleanup completed$(NC)"

act-pr: ## Run GitHub Actions CI locally using act (simulates pull request)
	@echo -e "$(BLUE)Running GitHub Actions CI workflow locally...$(NC)"
	@echo -e "$(YELLOW)This simulates the CI checks that run on pull requests$(NC)"
	@if [[ "$$(uname -m)" == "arm64" ]]; then \
		echo -e "$(CYAN)Detected Apple Silicon (M1/M2) - using linux/amd64 architecture$(NC)"; \
		act pull_request --container-architecture linux/amd64 --platform ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest; \
	else \
		echo -e "$(CYAN)Using default architecture$(NC)"; \
		act pull_request; \
	fi
	@echo -e "$(GREEN)Local CI simulation completed$(NC)"
