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

.PHONY: help install install-test install-dev setup init-db run airflow serve test test-unit test-int test-ci test-fast test-full lint lint-fix clean

help: ## Show this help message
	@echo "$(CYAN)================== TICKER CONVERTER COMMANDS ==================$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 SETUP & INSTALLATION$(NC)"
	@echo "  $(CYAN)setup$(NC)           Interactive setup - configure API keys and credentials"
	@echo "  $(CYAN)install$(NC)         Install production dependencies only"
	@echo "  $(CYAN)install-test$(NC)    Install production + testing dependencies"
	@echo "  $(CYAN)install-dev$(NC)     Install full development environment"
	@echo ""
	@echo "$(YELLOW)🚀 OPERATIONS & EXECUTION$(NC)"
	@echo "  $(CYAN)init-db$(NC)         Initialize database with last 30 trading days of data"
	@echo "  $(CYAN)run$(NC)             Run daily data collection for previous trading day"
	@echo "  $(CYAN)airflow$(NC)         Start Apache Airflow instance with default user"
	@echo "  $(CYAN)serve$(NC)           Start FastAPI development server"
	@echo ""
	@echo "$(YELLOW)🧪 TESTING$(NC)"
	@echo "  $(CYAN)test$(NC)            Run test suite with coverage (legacy alias for test-full)"
	@echo "  $(CYAN)test-unit$(NC)       Run unit tests only (fast)"
	@echo "  $(CYAN)test-int$(NC)        Run integration tests only"
	@echo "  $(CYAN)test-ci$(NC)         Run CI pipeline tests (unit + basic coverage)"
	@echo "  $(CYAN)test-fast$(NC)       Run all tests quickly (no coverage reports)"
	@echo "  $(CYAN)test-full$(NC)       Run comprehensive test suite with full coverage"
	@echo ""
	@echo "$(YELLOW)✨ CODE QUALITY$(NC)"
	@echo "  $(CYAN)lint$(NC)            Run all code quality checks"
	@echo "  $(CYAN)lint-fix$(NC)        Auto-fix code quality issues (black, isort)"
	@echo ""
	@echo "$(YELLOW)🧹 MAINTENANCE$(NC)"
	@echo "  $(CYAN)clean$(NC)           Clean build artifacts and cache files"
	@echo "  $(CYAN)help$(NC)            Show this help message"
	@echo ""
	@echo "$(CYAN)============================================================$(NC)"

# Setup and installation commands
setup: ## Interactive setup - configure API keys and credentials
	@echo "$(BLUE)Starting interactive setup...$(NC)"
	$(PYTHON) scripts/setup.py
	@echo "$(GREEN)Setup completed$(NC)"

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
	@if [ -f .env ]; then \
		source .env && airflow users create \
			--username $${AIRFLOW_ADMIN_USERNAME:-admin} \
			--firstname $${AIRFLOW_ADMIN_FIRSTNAME:-Admin} \
			--lastname $${AIRFLOW_ADMIN_LASTNAME:-User} \
			--role Admin \
			--email $${AIRFLOW_ADMIN_EMAIL:-admin@ticker-converter.local} \
			--password $${AIRFLOW_ADMIN_PASSWORD:-admin123} 2>/dev/null || echo "User already exists"; \
	else \
		airflow users create \
			--username admin \
			--firstname Admin \
			--lastname User \
			--role Admin \
			--email admin@ticker-converter.local \
			--password admin123 2>/dev/null || echo "User already exists"; \
	fi
	@echo "$(GREEN)Starting Airflow webserver...$(NC)"
	@echo "$(CYAN)=== AIRFLOW CONNECTION DETAILS ===$(NC)"
	@echo "$(GREEN)URL: http://localhost:8080$(NC)"
	@if [ -f .env ]; then \
		source .env && echo "$(GREEN)Username: $${AIRFLOW_ADMIN_USERNAME:-admin}$(NC)" && echo "$(GREEN)Password: $${AIRFLOW_ADMIN_PASSWORD:-admin123}$(NC)"; \
	else \
		echo "$(GREEN)Username: admin$(NC)" && echo "$(GREEN)Password: admin123$(NC)"; \
	fi
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
test: test-full ## Run test suite with coverage (legacy alias for test-full)

test-unit: ## Run unit tests only (fast)
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v --tb=short --no-cov
	@echo "$(GREEN)Unit tests completed$(NC)"

test-int: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@echo "$(YELLOW)Note: Integration tests require valid API keys and INTEGRATION_TEST=true$(NC)"
	INTEGRATION_TEST=true pytest tests/integration/ -v --tb=short --no-cov
	@echo "$(GREEN)Integration tests completed$(NC)"

test-ci: ## Run CI pipeline tests (unit + basic coverage)
	@echo "$(BLUE)Running CI test suite...$(NC)"
	pytest tests/unit/ --cov=src/$(PACKAGE_NAME) --cov-report=term-missing --cov-fail-under=35
	@echo "$(GREEN)CI test suite completed$(NC)"

test-fast: ## Run all tests quickly (no coverage reports)
	@echo "$(BLUE)Running all tests (fast mode)...$(NC)"
	pytest tests/ -v --tb=short -x --no-cov
	@echo "$(GREEN)Fast test suite completed$(NC)"

test-full: ## Run comprehensive test suite with full coverage
	@echo "$(BLUE)Running comprehensive test suite...$(NC)"
	pytest tests/ --cov=src/$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=35 -v
	@echo "$(GREEN)Comprehensive test suite completed$(NC)"
	@echo "$(CYAN)Coverage reports generated:$(NC)"
	@echo "  $(GREEN)HTML: htmlcov/index.html$(NC)"
	@echo "  $(GREEN)XML: coverage.xml$(NC)"

lint: ## Run all code quality checks
	@echo "$(BLUE)Running code quality checks...$(NC)"
	pylint src/$(PACKAGE_NAME)/ api/ run_api.py
	black --check src/$(PACKAGE_NAME)/ api/ tests/ run_api.py || (echo "Code formatting issues found. Run 'make lint-fix' to fix them." && exit 1)
	isort --check-only src/$(PACKAGE_NAME)/ api/ tests/ run_api.py || (echo "Import sorting issues found. Run 'make lint-fix' to fix them." && exit 1)
	mypy src/$(PACKAGE_NAME)/ api/ || true
	@echo "$(GREEN)Code quality checks completed$(NC)"

lint-fix: ## Auto-fix code quality issues (black first, then isort)
	@echo "$(BLUE)Auto-fixing code quality issues...$(NC)"
	@echo "$(YELLOW)Step 1: Running black formatter...$(NC)"
	black src/$(PACKAGE_NAME)/ api/ tests/ run_api.py
	@echo "$(YELLOW)Step 2: Running isort import sorter...$(NC)"
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
