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

clean: ## Clean build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "$(GREEN)Cleanup completed$(NC)"
