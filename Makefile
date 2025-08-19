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

.PHONY: help setup install install-test install-dev init-db airflow airflow-fix-config test test-ci act-pr lint lint-fix airflow-close db-close clean teardown-cache teardown-env teardown-airflow teardown-db

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
	@grep -E '^(setup|install|install-test|install-dev|init-db|airflow|airflow-fix-config):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Testing:$(NC)"
	@grep -E '^(test|test-int|test-ci|act-pr|lint|lint-fix):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
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
	@echo -e "$(BLUE)Setting up environment variables...$(NC)"
	@if [ ! -f .env ]; then \
				echo -e "$(YELLOW)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
				echo -e "$(CYAN)Please review and update the .env file with your specific values.$(NC)"; \
				echo -e "$(CYAN)Default values have been set from .env.example$(NC)"; \
	else \
				echo -e "$(GREEN).env file already exists$(NC)"; \
	fi

_setup_python_environment: ## Internal: Setup Python environment with pyenv and virtual environment
	@echo -e "$(BLUE)Setting up Python environment...$(NC)"
	@if ! command -v pyenv >/dev/null 2>&1; then \
		echo -e "$(RED)Error: pyenv is not installed or not in PATH$(NC)"; \
		echo -e "$(YELLOW)Please install pyenv first:$(NC)"; \
		echo -e "$(CYAN)  macOS: brew install pyenv$(NC)"; \
		echo -e "$(CYAN)  Linux: curl https://pyenv.run | bash$(NC)"; \
		echo -e "$(CYAN)Then add pyenv to your shell profile and restart your shell$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(YELLOW)Checking Python 3.11.12 availability...$(NC)"
	@if ! pyenv versions --bare | grep -q "^3.11.12$$"; then \
		echo -e "$(YELLOW)Python 3.11.12 not found. Installing...$(NC)"; \
		pyenv install 3.11.12; \
	else \
		echo -e "$(GREEN)Python 3.11.12 is already installed$(NC)"; \
	fi
	@echo -e "$(YELLOW)Setting local Python version to 3.11.12...$(NC)"
	@pyenv local 3.11.12
	@echo -e "$(YELLOW)Setting up virtual environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		echo -e "$(YELLOW)Creating virtual environment...$(NC)"; \
		python -m venv .venv; \
	else \
		echo -e "$(GREEN)Virtual environment already exists$(NC)"; \
	fi
	@echo -e "$(GREEN)Python environment setup completed$(NC)"

install: ## Install all running dependencies
	@echo -e "$(BLUE)Installing production dependencies...$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(YELLOW)Installing production dependencies...$(NC)"
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -e .
	@echo -e "$(GREEN)Production dependencies installed$(NC)"

install-test: ## Install production + testing dependencies
	@echo -e "$(BLUE)Installing production and testing dependencies...$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(YELLOW)Installing production and testing dependencies...$(NC)"
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -e ".[test]"
	@echo -e "$(GREEN)Production and testing dependencies installed$(NC)"

install-dev: ## Install full development environment
	@echo -e "$(BLUE)Installing full development environment...$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(YELLOW)Installing full development environment...$(NC)"
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -e ".[dev,test]"
	@echo -e "$(GREEN)Full development environment installed$(NC)"

init-db: ## Initialise PostgreSQL database using defaults
	@echo -e "$(BLUE)Initializing PostgreSQL database...$(NC)"
	@echo -e "$(YELLOW)Loading environment variables...$(NC)"
	@source .env && \
	echo -e "$(YELLOW)Checking PostgreSQL service status...$(NC)" && \
	if ! pgrep -f "postgres" > /dev/null; then \
		echo -e "$(YELLOW)Starting PostgreSQL service...$(NC)"; \
		if command -v brew >/dev/null 2>&1; then \
			brew services start postgresql || brew services start postgresql@14 || brew services start postgresql@15; \
		else \
			sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null; \
		fi; \
		sleep 2; \
	fi && \
	echo -e "$(YELLOW)Creating PostgreSQL user and database...$(NC)" && \
	createuser -s $$POSTGRES_USER 2>/dev/null || echo -e "$(YELLOW)User $$POSTGRES_USER already exists$(NC)" && \
	createdb -O $$POSTGRES_USER $$POSTGRES_DB 2>/dev/null || echo -e "$(YELLOW)Database $$POSTGRES_DB already exists$(NC)" && \
	echo -e "$(YELLOW)Setting up database schema...$(NC)" && \
	if [ -d dags/sql/ddl ]; then \
		for ddl_file in dags/sql/ddl/*.sql; do \
			if [ -f "$$ddl_file" ]; then \
				echo -e "$(CYAN)Executing: $$ddl_file$(NC)" && \
				psql -h $$POSTGRES_HOST -p $$POSTGRES_PORT -U $$POSTGRES_USER -d $$POSTGRES_DB -f "$$ddl_file" 2>/dev/null || \
				echo -e "$(YELLOW)Warning: Failed to execute $$ddl_file$(NC)"; \
			fi; \
		done && \
		echo -e "$(GREEN)Schema setup completed$(NC)"; \
	else \
		echo -e "$(YELLOW)Note: No DDL directory found at dags/sql/ddl$(NC)"; \
	fi && \
	echo -e "$(GREEN)Database initialization completed$(NC)" && \
	echo -e "$(CYAN)Database connection details:$(NC)" && \
	echo -e "$(GREEN)Host: $$POSTGRES_HOST$(NC)" && \
	echo -e "$(GREEN)Port: $$POSTGRES_PORT$(NC)" && \
	echo -e "$(GREEN)Database: $$POSTGRES_DB$(NC)" && \
	echo -e "$(GREEN)User: $$POSTGRES_USER$(NC)"

airflow: ## Start Apache Airflow instance with default user
	@echo -e "$(BLUE)Starting Apache Airflow...$(NC)"
	@echo -e "$(YELLOW)Activating virtual environment...$(NC)"
	@source .venv/bin/activate && \
	echo -e "$(YELLOW)Loading environment variables...$(NC)" && \
	source .env && \
	echo -e "$(YELLOW)Setting up project-local Airflow configuration...$(NC)" && \
	export AIRFLOW_HOME="$${PWD}/airflow" && \
	export AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" && \
	export AIRFLOW__CORE__LOAD_EXAMPLES=False && \
	export AIRFLOW__CORE__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager" && \
	export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" && \
	export AIRFLOW__API_AUTH__JWT_SECRET="$$AIRFLOW__API_AUTH__JWT_SECRET" && \
	echo -e "$(YELLOW)Airflow Home: $${PWD}/airflow$(NC)" && \
	echo -e "$(YELLOW)DAGs Folder: $${PWD}/dags$(NC)" && \
	echo -e "$(YELLOW)Setting up Airflow database...$(NC)" && \
	AIRFLOW_HOME="$${PWD}/airflow" \
	AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" \
	AIRFLOW__CORE__LOAD_EXAMPLES=False \
	AIRFLOW__CORE__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager" \
	AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" \
	AIRFLOW__API_AUTH__JWT_SECRET="$$AIRFLOW__API_AUTH__JWT_SECRET" \
	airflow db migrate && \
	echo -e "$(YELLOW)Creating default admin user (if not exists)...$(NC)" && \
	AIRFLOW_HOME="$${PWD}/airflow" \
	AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" \
	AIRFLOW__CORE__LOAD_EXAMPLES=False \
	AIRFLOW__CORE__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager" \
	AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" \
	AIRFLOW__API_AUTH__JWT_SECRET="$$AIRFLOW__API_AUTH__JWT_SECRET" \
	airflow users create \
		--username $$AIRFLOW_ADMIN_USERNAME \
		--firstname $$AIRFLOW_ADMIN_FIRSTNAME \
		--lastname $$AIRFLOW_ADMIN_LASTNAME \
		--role Admin \
		--email $$AIRFLOW_ADMIN_EMAIL \
		--password $$AIRFLOW_ADMIN_PASSWORD 2>/dev/null || echo -e "$(YELLOW)User already exists$(NC)" && \
	echo -e "$(GREEN)Starting Airflow scheduler and API server...$(NC)" && \
	echo -e "$(CYAN)Airflow will be available at: http://localhost:8080$(NC)" && \
	echo -e "$(GREEN)Username: $$AIRFLOW_ADMIN_USERNAME | Password: $$AIRFLOW_ADMIN_PASSWORD$(NC)" && \
	echo -e "$(YELLOW)Starting scheduler in background...$(NC)" && \
	AIRFLOW_HOME="$${PWD}/airflow" \
	AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" \
	AIRFLOW__CORE__LOAD_EXAMPLES=False \
	AIRFLOW__CORE__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager" \
	AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" \
	AIRFLOW__API_AUTH__JWT_SECRET="$$AIRFLOW__API_AUTH__JWT_SECRET" \
	airflow scheduler --daemon && \
	sleep 2 && \
	echo -e "$(YELLOW)Starting API server...$(NC)" && \
	AIRFLOW_HOME="$${PWD}/airflow" \
	AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" \
	AIRFLOW__CORE__LOAD_EXAMPLES=False \
	AIRFLOW__CORE__AUTH_MANAGER="airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager" \
	AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" \
	AIRFLOW__API_AUTH__JWT_SECRET="$$AIRFLOW__API_AUTH__JWT_SECRET" \
	airflow api-server --port 8080

airflow-config: ## Fix Airflow 3.0.4 configuration deprecation warnings
	@echo -e "$(BLUE)Setting Airflow configuration for 3.0.4...$(NC)"
	@$(PYTHON) scripts/fix_airflow_config.py
	@echo -e "$(GREEN)Airflow configuration updated$(NC)"

# ============================================================================
# TESTING
# ============================================================================

test: ## Run test suite with coverage
	@echo -e "$(BLUE)Running test suite with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing --ignore=tests/integration
	@echo -e "$(GREEN)Tests completed$(NC)"

test-int: ## Run integration tests only (requires external services)
	@echo -e "$(BLUE)Running integration tests...$(NC)"
	@echo -e "$(YELLOW)Note: Integration tests require external services (PostgreSQL, Airflow, API keys)$(NC)"
	@echo -e "$(YELLOW)Ensure services are running and configured properly$(NC)"
	@if [ ! -f .env ]; then echo "Error: .env file not found. Run 'make setup' first."; exit 1; fi
	@set -a && . ./.env && set +a && \
	export AIRFLOW_HOME="$$PWD/airflow" && \
	export AIRFLOW__CORE__DAGS_FOLDER="$$PWD/dags" && \
	export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:///$$(pwd)/airflow/airflow.db" && \
	$(PYTHON) -m pytest tests/integration/ -v --tb=short

test-ci: ## Run all CI tests
	@echo -e "$(BLUE)Running CI tests...$(NC)"
	@$(PYTHON) -m pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=xml --cov-fail-under=80 --ignore=tests/integration
	@echo -e "$(GREEN)CI tests completed$(NC)"

act-pr: ## Runs local GitHub Actions workflow using Act
	@echo -e "$(BLUE)Running GitHub Actions workflow locally...$(NC)"
	@if command -v act >/dev/null 2>&1; then \
		if [[ "$$(uname -m)" == "arm64" ]]; then \
			act pull_request --container-architecture linux/amd64; \
		else \
			act pull_request; \
		fi; \
	else \
				echo -e "$(RED)Error: 'act' is not installed. Install it from: https://github.com/nektos/act$(NC)"; \
		exit 1; \
	fi

lint: ## Run all code quality checks
	@echo -e "$(BLUE)Running code quality checks...$(NC)"
	@$(PYTHON) -m black --check .
	@$(PYTHON) -m isort --check-only .
	@$(PYTHON) -m pylint src/$(PACKAGE_NAME) dags/
	@$(PYTHON) -m mypy src/$(PACKAGE_NAME)
	@echo -e "$(GREEN)Code quality checks completed$(NC)"

lint-fix: ## Auto-fix code quality issues
	@echo -e "$(BLUE)Auto-fixing code quality issues...$(NC)"
	@$(PYTHON) -m black .
	@$(PYTHON) -m isort .
	@echo -e "$(GREEN)Code quality fixes applied$(NC)"

# ============================================================================
# SHUTDOWN AND CLEAN
# ============================================================================

airflow-close: ## Closes down Airflow
	@echo -e "$(BLUE)Closing Airflow...$(NC)"
	@if pgrep -f "airflow" > /dev/null; then \
		pkill -f "airflow" && echo -e "$(GREEN)Airflow stopped$(NC)"; \
	else \
		echo -e "$(YELLOW)Airflow is not running$(NC)"; \
	fi

db-close: ## Shuts down local PostgreSQL instance
	@echo -e "$(BLUE)Shutting down PostgreSQL...$(NC)"
	@if pgrep -f "postgres" > /dev/null; then \
		if command -v brew >/dev/null 2>&1; then \
			brew services stop postgresql || brew services stop postgresql@14 || brew services stop postgresql@15; \
		else \
			sudo systemctl stop postgresql 2>/dev/null || sudo service postgresql stop 2>/dev/null; \
		fi; \
		echo -e "$(GREEN)PostgreSQL stopped$(NC)"; \
	else \
		echo -e "$(YELLOW)PostgreSQL is not running$(NC)"; \
	fi

clean: ## Clean build artifacts and cache files
	@echo -e "$(BLUE)Cleaning build artifacts...$(NC)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage
	@echo -e "$(GREEN)Cleanup completed$(NC)"

# ============================================================================
# TEARDOWN
# ============================================================================

teardown-cache: ## Deletes all build artifacts and testing cache files
	@echo -e "$(BLUE)Removing all cache folders and temporary files...$(NC)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".tox" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
	@rm -rf build/ dist/ .coverage
	@echo -e "$(GREEN)Cache cleanup completed$(NC)"

teardown-env: ## Remove environment file and virtual environment
	@echo -e "$(RED)WARNING: This will delete .env and .venv/ directory$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo -e "$(BLUE)Removing environment files...$(NC)"
	@rm -rf .env .venv/
	@echo -e "$(GREEN)Environment cleanup completed$(NC)"

teardown-airflow: ## Shutdown Airflow and remove all Airflow files
	@echo -e "$(RED)WARNING: This will shutdown Airflow and delete all airflow/ files$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo -e "$(BLUE)Shutting down Airflow and removing files...$(NC)"
	@if pgrep -f "airflow" > /dev/null; then \
		pkill -f "airflow"; \
		echo -e "$(YELLOW)Airflow processes stopped$(NC)"; \
		sleep 2; \
	fi
	@# Remove airflow directory with better error handling
	@if [ -d "airflow" ]; then \
		sleep 1; \
		rm -rf airflow/ 2>/dev/null || (chmod -R 755 airflow/ 2>/dev/null && rm -rf airflow/) || true; \
		if [ ! -d "airflow" ]; then \
			echo -e "$(GREEN)Airflow files removed$(NC)"; \
		else \
			echo -e "$(YELLOW)Some airflow files may remain - manual cleanup may be needed$(NC)"; \
		fi; \
	fi
	@echo -e "$(GREEN)Airflow teardown completed$(NC)"

teardown-db: ## Shutdown and remove PostgreSQL database
	@echo -e "$(RED)WARNING: This will shutdown PostgreSQL and delete the database$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo -e "$(BLUE)Shutting down and removing PostgreSQL database...$(NC)"
	@if pgrep -f "postgres" > /dev/null; then \
		if command -v brew >/dev/null 2>&1; then \
			brew services stop postgresql || brew services stop postgresql@14 || brew services stop postgresql@15; \
		else \
			sudo systemctl stop postgresql 2>/dev/null || sudo service postgresql stop 2>/dev/null; \
		fi; \
	fi
	@echo -e "$(YELLOW)Note: PostgreSQL system database files are preserved. Use your system's PostgreSQL tools to remove data if needed.$(NC)"
	@echo -e "$(GREEN)Database teardown completed$(NC)"
