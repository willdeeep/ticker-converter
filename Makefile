# Financial Market Data Analytics Pipeline - Makefile
# Ticker Converter Project
# Author: Will Huntley-Clarke

.PHONY: help install install-dev clean test test-unit test-integration test-coverage test-fast
.PHONY: lint format check-format check-typing check-security check-all
.PHONY: demo run-demo run-pipeline
.PHONY: git-status git-add git-commit git-push
.PHONY: build package dist upload
.PHONY: docs serve-docs
.PHONY: env-setup env-check env-clean
.PHONY: ci-setup ci-test ci-quality ci-full

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
PIP := pip
PACKAGE_NAME := ticker_converter
SOURCE_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
SCRIPTS_DIR := scripts

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(CYAN)Financial Market Data Analytics Pipeline - Makefile$(NC)"
	@echo "$(BLUE)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install-dev    # Install all dependencies"
	@echo "  make test           # Run all tests"
	@echo "  make lint           # Check code quality"
	@echo "  make demo           # Run demo pipeline"

# Environment Setup
env-setup: ## Create and activate virtual environment
	@echo "$(BLUE)Setting up virtual environment...$(NC)"
	python -m venv .venv
	@echo "$(GREEN)Virtual environment created. Activate with: source .venv/bin/activate$(NC)"

env-check: ## Check if virtual environment is activated
	@echo "$(BLUE)Checking environment...$(NC)"
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "$(RED)No virtual environment detected. Run: source .venv/bin/activate$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)Virtual environment active: $$VIRTUAL_ENV$(NC)"; \
	fi

env-clean: ## Remove virtual environment and cache files
	@echo "$(YELLOW)Cleaning environment...$(NC)"
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Environment cleaned$(NC)"

# Installation
install: ## Install basic dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install -e .

install-dev: ## Install all development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev,storage,models]"
	@echo "$(GREEN)Development environment ready$(NC)"

install-all: ## Install all optional dependencies
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(PIP) install -e ".[all]"

# Testing
test: ## Run all tests with coverage
	@echo "$(BLUE)Running all tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/ --cov=$(SOURCE_DIR)/$(PACKAGE_NAME) --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=40

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/unit/ -v

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/integration/ -v

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running fast tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/ -x --tb=short -q

test-coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/ --cov=$(SOURCE_DIR)/$(PACKAGE_NAME) --cov-report=html:htmlcov
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-specific: ## Run specific test (usage: make test-specific TEST=test_file.py::test_name)
	@echo "$(BLUE)Running specific test: $(TEST)$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/$(TEST) -v

# Code Quality
lint: ## Run all linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	$(PYTHON) -m ruff check $(SOURCE_DIR)/ $(TEST_DIR)/

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	$(PYTHON) -m ruff check $(SOURCE_DIR)/ $(TEST_DIR)/ --fix

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(PYTHON) -m black $(SOURCE_DIR)/ $(TEST_DIR)/ $(SCRIPTS_DIR)/
	$(PYTHON) -m ruff check --fix $(SOURCE_DIR)/ $(TEST_DIR)/ $(SCRIPTS_DIR)/

check-format: ## Check if code is properly formatted
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(PYTHON) -m black --check $(SOURCE_DIR)/ $(TEST_DIR)/ $(SCRIPTS_DIR)/

check-typing: ## Run mypy type checking
	@echo "$(BLUE)Running type checking...$(NC)"
	$(PYTHON) -m mypy $(SOURCE_DIR)/$(PACKAGE_NAME)

check-security: ## Run security checks with bandit
	@echo "$(BLUE)Running security checks...$(NC)"
	$(PYTHON) -m bandit -r $(SOURCE_DIR)/ -f json || true

check-all: lint check-format check-typing ## Run all quality checks

# Demo and Pipeline
demo: ## Run the demo pipeline
	@echo "$(BLUE)Running demo pipeline...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/demo_pipeline.py

run-demo: demo ## Alias for demo

run-pipeline: ## Run the main pipeline (interactive)
	@echo "$(BLUE)Running main pipeline...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli

# Git Operations
git-status: ## Show git status
	@echo "$(BLUE)Git status:$(NC)"
	git status

git-add: ## Add all changes to git
	@echo "$(BLUE)Adding changes to git...$(NC)"
	git add .
	git status

git-commit: ## Commit changes (usage: make git-commit MSG="commit message")
	@echo "$(BLUE)Committing changes...$(NC)"
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide a commit message with MSG=\"your message\"$(NC)"; \
		exit 1; \
	fi
	git commit -m "$(MSG)"

git-push: ## Push changes to remote
	@echo "$(BLUE)Pushing to remote...$(NC)"
	git push

git-log: ## Show recent git log
	@echo "$(BLUE)Recent commits:$(NC)"
	git log --oneline -10

# CI/CD Simulation
ci-setup: install-dev ## Setup CI environment
	@echo "$(GREEN)CI environment setup complete$(NC)"

ci-test: test-fast ## Run CI tests (fast)
	@echo "$(GREEN)CI tests completed$(NC)"

ci-quality: check-all ## Run CI quality checks
	@echo "$(GREEN)CI quality checks completed$(NC)"

ci-full: ci-setup ci-quality test ## Run full CI pipeline
	@echo "$(GREEN)Full CI pipeline completed$(NC)"

# Build and Package
clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

build: clean ## Build the package
	@echo "$(BLUE)Building package...$(NC)"
	$(PYTHON) -m build

package: build ## Create distribution packages
	@echo "$(GREEN)Package built successfully$(NC)"
	ls -la dist/

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@if [ -d "$(DOCS_DIR)" ]; then \
		cd $(DOCS_DIR) && make html; \
	else \
		echo "$(YELLOW)Documentation directory not found$(NC)"; \
	fi

serve-docs: docs ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@if [ -d "$(DOCS_DIR)/_build/html" ]; then \
		cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000; \
	else \
		echo "$(RED)Documentation not built. Run 'make docs' first$(NC)"; \
	fi

# Data Operations
clean-data: ## Clean temporary data files
	@echo "$(YELLOW)Cleaning data files...$(NC)"
	rm -rf data/temp/
	rm -rf raw_data_output/temp/
	@echo "$(GREEN)Data files cleaned$(NC)"

# Development Workflow Shortcuts
dev-setup: env-setup install-dev ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Don't forget to activate the virtual environment: source .venv/bin/activate$(NC)"

dev-test: lint-fix test-fast ## Quick development test cycle
	@echo "$(GREEN)Development test cycle completed$(NC)"

dev-commit: lint-fix test-fast git-add ## Prepare for commit (lint, test, add)
	@echo "$(GREEN)Ready for commit. Use: make git-commit MSG=\"your message\"$(NC)"

# Production Readiness
prod-check: check-all test ## Full production readiness check
	@echo "$(GREEN)Production readiness check completed$(NC)"

# Monitoring and Analysis
profile: ## Run performance profiling
	@echo "$(BLUE)Running performance profiling...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats $(SCRIPTS_DIR)/demo_pipeline.py
	@echo "$(GREEN)Profile saved to profile.stats$(NC)"

memory-profile: ## Run memory profiling
	@echo "$(BLUE)Running memory profiling...$(NC)"
	$(PYTHON) -m memory_profiler $(SCRIPTS_DIR)/demo_pipeline.py

# Security and Dependencies
security-audit: ## Run security audit
	@echo "$(BLUE)Running security audit...$(NC)"
	$(PYTHON) -m safety check
	$(PYTHON) -m bandit -r $(SOURCE_DIR)/

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev]"

# Aliases for common workflows
quick-test: test-fast ## Alias for test-fast
quality: check-all ## Alias for check-all
setup: dev-setup ## Alias for dev-setup

# Display current configuration
show-config: ## Show current project configuration
	@echo "$(CYAN)Project Configuration:$(NC)"
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "Pip version: $(shell $(PIP) --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Virtual environment: $$VIRTUAL_ENV"
	@echo "Package name: $(PACKAGE_NAME)"
	@echo "Source directory: $(SOURCE_DIR)"
	@echo "Test directory: $(TEST_DIR)"
