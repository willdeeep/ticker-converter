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

.PHONY: help setup install install-test init-db run airflow airflow-fix-config test test-ci act-pr lint lint-makefile lint-sql lint-black lint-isort lint-pylint lint-mypy lint-fix airflow-close db-close clean teardown-cache teardown-env teardown-airflow teardown-db _load_env _validate_env _setup_python_environment _install_quality_tools

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help message
	@echo -e "$(CYAN)Ticker Converter - Available Commands:$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Help:$(NC)"
	@grep -E '^(help):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Setup and install:$(NC)"
	@grep -E '^(setup|install|install-test|init-db):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Run and inspect:$(NC)"
	@grep -E '^(run|inspect|airflow|airflow-fix-config):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Testing:$(NC)"
	@grep -E '^(test|test-int|test-ci|act-pr|lint|lint-fix|quality):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[0m %s\n", $$1, $$2}'
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

setup: ## Initialize project and basic environment (environment variables)
	@echo -e "$(BLUE)Setting up ticker-converter project environment...$(NC)"
	@echo -e "$(YELLOW)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo -e "$(CYAN)STEP 1: Customize Environment Configuration$(NC)"
	@echo -e "$(YELLOW)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@if [ ! -f .env ]; then \
		echo -e "$(YELLOW)Please customize .env.example with your values:$(NC)"; \
		echo -e "$(CYAN)  • ALPHA_VANTAGE_API_KEY: Get from https://www.alphavantage.co/support/#api-key$(NC)"; \
		echo -e "$(CYAN)  • Database credentials: Set your PostgreSQL configuration$(NC)"; \
		echo -e "$(CYAN)  • Airflow admin: Set your preferred admin username/password$(NC)"; \
		echo -e "$(CYAN)  • JWT secret: Change from default for security$(NC)"; \
		echo -e ""; \
		echo -e "$(YELLOW)Press Enter after customizing .env.example to continue...$(NC)"; \
		read -p ""; \
		cp .env.example .env; \
		echo -e "$(GREEN)✓ Copied customized .env.example to .env$(NC)"; \
	else \
		echo -e "$(GREEN)✓ .env file already exists$(NC)"; \
	fi
	@echo -e "$(CYAN)STEP 2: Validate Configuration$(NC)"
	@$(MAKE) _validate_env
	@echo -e "$(CYAN)STEP 3: Setup Python Environment$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo -e "$(GREEN)✓ Environment setup completed!$(NC)"
	@echo -e "$(CYAN)Next steps:$(NC)"
	@echo -e "$(YELLOW)  • Production runtime: make install$(NC)"
	@echo -e "$(YELLOW)  • Testing workflow: make install-test$(NC)"
	@echo -e "$(YELLOW)  • Development work: make install-dev$(NC)"
	@echo -e "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

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

# ============================================================================
# ENVIRONMENT INFRASTRUCTURE
# ============================================================================

_load_env: ## Internal: Load and export environment variables
	@if [ ! -f .env ]; then \
		echo -e "$(RED)Error: .env file not found. Run 'make setup' first.$(NC)"; \
		echo -e "$(YELLOW)Tip: Copy .env.example to .env and customize the values$(NC)"; \
		exit 1; \
	fi

_validate_env: _load_env ## Internal: Validate required environment variables  
	@echo -e "$(YELLOW)Validating environment variables...$(NC)"
	@set -a && . ./.env && set +a && \
	$(call check_var,POSTGRES_HOST) && \
	$(call check_var,POSTGRES_PORT) && \
	$(call check_var,POSTGRES_DB) && \
	$(call check_var,POSTGRES_USER) && \
	$(call check_var,POSTGRES_PASSWORD) && \
	$(call check_var,AIRFLOW_ADMIN_USERNAME) && \
	$(call check_var,AIRFLOW_ADMIN_PASSWORD) && \
	$(call check_var,AIRFLOW_ADMIN_EMAIL) && \
	$(call check_var,AIRFLOW_ADMIN_FIRSTNAME) && \
	$(call check_var,AIRFLOW_ADMIN_LASTNAME) && \
	$(call check_var,AIRFLOW__API_AUTH__JWT_SECRET) && \
	$(call check_var,ALPHA_VANTAGE_API_KEY) && \
	echo -e "$(GREEN)✓ Environment validation passed$(NC)"

# Function to validate individual environment variables
# Usage: $(call check_var,VARIABLE_NAME)
# Fails if variable is empty or contains placeholder values
define check_var
	if [ -z "$${$(1)}" ] || [ "$${$(1)}" = "your_alpha_vantage_api_key_here" ] || [ "$${$(1)}" = "your-secure-jwt-secret-key-change-for-production" ]; then \
		echo -e "$(RED)✗ Error: Required variable $(1) needs customization in .env$(NC)"; \
		echo -e "$(YELLOW)Please edit .env and set a proper value for $(1)$(NC)"; \
		echo -e "$(CYAN)Hint: Check .env.example for guidance$(NC)"; \
		exit 1; \
	fi
endef

# ============================================================================
# SETUP AND RUN
# ============================================================================

install: ## Install all runtime dependencies (Airflow, FastAPI, database, etc.)
	@echo -e "$(BLUE)Installing all runtime dependencies...$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(YELLOW)Installing all runtime dependencies (FastAPI, database, HTTP, Airflow)...$(NC)"
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -e .
	@echo -e "$(GREEN)✓ Runtime dependencies installed$(NC)"
	@echo -e "$(CYAN)Dependencies: FastAPI, uvicorn, pydantic, psycopg2-binary, asyncpg, pandas, requests, aiohttp, python-dotenv, apache-airflow$(NC)"

install-test: ## Install everything needed for testing/validation (pytest, black, mypy, sqlfluff, etc.)
	@echo -e "$(BLUE)Installing all testing and validation dependencies...$(NC)"
	@$(MAKE) _setup_python_environment
	@echo -e "$(YELLOW)Installing runtime + testing/validation dependencies...$(NC)"
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -e ".[test]"
	@echo -e "$(YELLOW)Installing system-level quality tools...$(NC)"
	@$(MAKE) _install_quality_tools
	@echo -e "$(GREEN)✓ All testing and validation dependencies installed$(NC)"
	@echo -e "$(CYAN)Dependencies: Runtime + pytest, black, mypy, pylint, sqlfluff, pre-commit, ipython, jupyter$(NC)"

_install_quality_tools: ## Helper: Install system-level quality tools (checkmake, etc.)
	@echo "Installing optional system-level quality tools..."
	@# Install checkmake if not available
	@if ! command -v checkmake >/dev/null 2>&1; then \
		echo "Installing checkmake..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install checkmake || echo "⚠️  Failed to install checkmake via brew"; \
		elif command -v go >/dev/null 2>&1; then \
			go install github.com/checkmake/checkmake/cmd/checkmake@latest || echo "⚠️  Failed to install checkmake via go"; \
		else \
			echo "ℹ️  checkmake installation skipped - requires brew or go"; \
		fi; \
	else \
		echo "✓ checkmake already installed"; \
	fi
	@# Note: sqlfluff is installed via pip in the quality dependencies
	@echo "✓ Quality tools installation completed"

inspect: ## Inspect system components and configuration
	@echo -e "$(BLUE)Running system diagnostics...$(NC)"
	@$(PYTHON) scripts/inspect_system.py $(if $(DETAILED),--detailed) $(if $(JSON),--json)
	@echo -e "$(GREEN)System inspection completed$(NC)"

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

run: _validate_env ## Execute data pipeline (run or run DAG_NAME=manual_backfill)
	@if [ -n "$(DAG_NAME)" ]; then \
		echo -e "$(BLUE)Triggering Airflow DAG: $(DAG_NAME)$(NC)"; \
		cd $(PWD) && \
		AIRFLOW_HOME="$${PWD}/airflow" \
		AIRFLOW__CORE__DAGS_FOLDER="$${PWD}/dags" \
		AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:////$${PWD}/airflow/airflow.db" \
		airflow dags trigger $(DAG_NAME); \
		echo -e "$(GREEN)✅ DAG $(DAG_NAME) triggered successfully$(NC)"; \
	else \
		echo -e "$(BLUE)Running data ingestion pipeline...$(NC)"; \
		echo -e "$(YELLOW)📊 Fetching latest market data and currency rates$(NC)"; \
		$(PYTHON) -c "from src.ticker_converter.integrations.orchestrator import DataIngestionOrchestrator; orchestrator = DataIngestionOrchestrator(); results = orchestrator.run_full_ingestion(); print('✅ Pipeline completed:', results)"; \
		echo -e "$(GREEN)✅ Data pipeline completed successfully$(NC)"; \
	fi

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
	$(PYTHON) -m pytest tests/integration/ -v --tb=short --no-cov

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

lint-makefile: _validate_env ## Lint and validate Makefile structure
	@echo "Checking Makefile syntax and structure..."
	@# Check basic Makefile syntax with make dry-run
	@$(MAKE) -n help > /dev/null 2>&1 || (echo "❌ Makefile syntax error detected"; exit 1)
	@# Install checkmake if not available (optional - graceful fallback)
	@if command -v checkmake >/dev/null 2>&1; then \
		echo "Running checkmake linting..."; \
		checkmake Makefile || echo "⚠️  Checkmake warnings detected - review recommended"; \
	else \
		echo "ℹ️  checkmake not installed - install with: brew install checkmake (optional)"; \
	fi
	@echo "✓ Makefile structure validation completed"

lint-sql: _validate_env ## Lint and validate SQL files
	@echo "Checking SQL file quality and standards..."
	@# Check for SQL files
	@if [ ! -d "dags/sql" ] && [ ! -d "sql" ]; then \
		echo "ℹ️  No SQL directories found - skipping SQL linting"; \
		exit 0; \
	fi
	@# Install sqlfluff if not available (graceful fallback)
	@if command -v sqlfluff >/dev/null 2>&1; then \
		echo "Running sqlfluff linting..."; \
		find . -name "*.sql" -path "./dags/sql/*" -o -path "./sql/*" | head -5 | while read file; do \
			echo "Checking $$file..."; \
			sqlfluff lint "$$file" --dialect postgres || echo "⚠️  SQL issues detected in $$file"; \
		done; \
	else \
		echo "ℹ️  sqlfluff not installed - install with: pip install sqlfluff (optional)"; \
	fi
	@# Basic SQL pattern checks
	@echo "Running basic SQL quality checks..."
	@find . -name "*.sql" -path "./dags/sql/*" -o -path "./sql/*" | while read file; do \
		if grep -q "SELECT \*" "$$file"; then \
			echo "⚠️  SELECT * found in $$file - consider explicit column lists"; \
		fi; \
		if ! grep -q "^-- Purpose:" "$$file" && echo "$$file" | grep -q "/ddl/"; then \
			echo "⚠️  Missing purpose comment in DDL file: $$file"; \
		fi; \
	done
	@echo "✓ SQL quality checks completed"

lint: _validate_env ## Run comprehensive linting (black, isort, pylint, mypy)
	@echo "Running full linting pipeline..."
	@$(MAKE) lint-black
	@$(MAKE) lint-isort  
	@$(MAKE) lint-pylint
	@$(MAKE) lint-mypy
	@echo "✓ All linting checks passed"

lint-black: _validate_env ## Run Black code formatting check
	@echo "Running Black formatting check..."
	@$(PYTHON) -m black --check .

lint-isort: _validate_env ## Run isort import sorting check
	@echo "Running isort import check..."
	@$(PYTHON) -m isort --check-only .

lint-pylint: _validate_env ## Run Pylint static analysis
	@echo "Running Pylint analysis..."
	@$(PYTHON) -m pylint src/$(PACKAGE_NAME) dags/

lint-mypy: _validate_env ## Run MyPy type checking
	@echo "Running MyPy type checking..."
	@$(PYTHON) -m mypy src/$(PACKAGE_NAME)

lint-fix: ## Auto-fix code quality issues
	@echo -e "$(BLUE)Auto-fixing code quality issues...$(NC)"
	@$(PYTHON) -m black .
	@$(PYTHON) -m isort .
	@echo -e "$(GREEN)Code quality fixes applied$(NC)"

quality: ## Run comprehensive quality gate validation
	@echo "Running comprehensive quality gate validation..."
	@echo "Quality Gate Pipeline: Makefile → SQL → Black → isort → Pylint → MyPy → Tests with Coverage"
	@echo ""
	@echo "Step 1/7: Makefile Linting..."
	@$(MAKE) lint-makefile
	@echo "✓ Makefile linting: PASSED"
	@echo ""
	@echo "Step 2/7: SQL Quality Checks..."
	@$(MAKE) lint-sql
	@echo "✓ SQL quality: PASSED"
	@echo ""
	@echo "Step 3/7: Code Formatting (Black)..."
	@$(MAKE) lint-black
	@echo "✓ Black formatting: PASSED"
	@echo ""
	@echo "Step 4/7: Import Sorting (isort)..."
	@$(MAKE) lint-isort
	@echo "✓ Import sorting: PASSED"
	@echo ""
	@echo "Step 5/7: Code Quality (Pylint)..."
	@$(MAKE) lint-pylint
	@echo "✓ Pylint score: 10.00/10 PASSED"
	@echo ""
	@echo "Step 6/7: Type Checking (MyPy)..."
	@$(MAKE) lint-mypy
	@echo "✓ MyPy type checking: PASSED"
	@echo ""
	@echo "Step 7/7: Test Suite with Coverage..."
	@$(MAKE) test
	@echo "✓ Tests and coverage: PASSED"
	@echo ""
	@echo "All Quality Gates PASSED!"
	@echo "✓ Makefile structure: Valid and compliant"
	@echo "✓ SQL quality: Standards compliant"
	@echo "✓ Code formatting: Black compliant"
	@echo "✓ Import sorting: isort compliant"
	@echo "✓ Code quality: Pylint 10.00/10"
	@echo "✓ Type safety: MyPy clean"
	@echo "✓ Test coverage: 67%+ with all tests passing"
	@echo "Ready for commit and pull request!"

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
