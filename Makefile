# Variables
SHELL := /bin/bash
PYTHON := python3
PACKAGE_NAME := ticker_converter
VENV_NAME := .venv
ENV_FILE := .env

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

.PHONY: help install install-test install-dev setup-env init-db init-schema init-db-full run airflow airflow-stop airflow-status serve test lint lint-fix lint-dags clean teardown teardown-db teardown-venv act-pr

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## .*$$/ {printf "  \033[0;36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# Database operations
init-schema: ## Initialize database schema only (no data loading)
	@echo -e "$(BLUE)Initializing database schema only...$(NC)"
	@echo -e "$(YELLOW)Creating tables, views, and indexes from DDL files$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --schema-only
	@echo -e "$(GREEN)Database schema created successfully$(NC)"

# Status operations
status: ## Check data ingestion and system status
	@echo -e "$(BLUE)Checking system status...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion status

# Airflow commands  
airflow-status: ## Check Apache Airflow status
	@echo -e "$(BLUE)Checking Airflow status...$(NC)"
	$(PYTHON) -m $(PACKAGE_NAME).cli_ingestion --airflow-status
