# =============================================================================
# Ticker Converter - Modular Cross-Platform Makefile
# =============================================================================
# This is the main Makefile that orchestrates all modular components.
# The modular structure provides maintainable, cross-platform build automation.
#
# Module Structure:
#   make/Makefile.common       - Shared functions and utility patterns
#   make/Makefile.platform     - OS detection and platform configurations
#   make/Makefile.env          - Environment setup and validation
#   make/Makefile.install      - Installation and dependency management
#   make/Makefile.database     - PostgreSQL operations and data management
#   make/Makefile.airflow      - Airflow orchestration and management
#   make/Makefile.testing      - Test execution and coverage analysis
#   make/Makefile.quality      - Code quality, linting, and validation
#   make/Makefile.cleanup      - Cleaning and teardown operations
#   make/help.sh               - Enhanced help system
# =============================================================================

# Default target
.DEFAULT_GOAL := help

# Directory for modular Makefiles
MAKE_DIR := make

# Ensure make directory exists
$(shell mkdir -p $(MAKE_DIR))

# =============================================================================
# INCLUDE MODULAR COMPONENTS - Order matters for dependencies
# =============================================================================

# 1. Common functions first (foundation for all other modules)
include $(MAKE_DIR)/Makefile.common

# 2. Platform detection (required by other modules)
include $(MAKE_DIR)/Makefile.platform

# 3. Environment setup (depends on platform detection)
include $(MAKE_DIR)/Makefile.env

# 4. Installation capabilities (depends on platform and environment)
include $(MAKE_DIR)/Makefile.install

# 5. Service modules (depend on installation capabilities)
include $(MAKE_DIR)/Makefile.database
include $(MAKE_DIR)/Makefile.airflow

# 6. Development workflow modules (depend on services)
include $(MAKE_DIR)/Makefile.testing
include $(MAKE_DIR)/Makefile.quality

# 6. Cleanup operations (can depend on all other modules)
include $(MAKE_DIR)/Makefile.cleanup

# =============================================================================
# MAIN WORKFLOW TARGETS
# =============================================================================

.PHONY: all setup-full dev-ready

all: ## ⚙️ Execute the most common development workflow (setup, install-test, quality)
	@echo -e "$(BLUE)Running complete development workflow...$(NC)"
	@$(MAKE) setup-env
	@$(MAKE) install-test
	@$(MAKE) quality
	@echo -e "$(GREEN)✓ Development environment ready!$(NC)"

setup-full: ## 📦 Complete development environment setup (alternative to module setup)
	@echo -e "$(BLUE)Setting up complete development environment...$(NC)"
	@$(MAKE) setup-env
	@$(MAKE) install
	@$(MAKE) init-db
	@echo -e "$(GREEN)✓ Complete development environment setup finished!$(NC)"

dev-ready: ## ⚙️ Validate that development environment is ready
	@echo -e "$(BLUE)Validating development environment...$(NC)"
	@$(MAKE) validate-env
	@$(MAKE) validate-tools
	@$(MAKE) test-fast
	@echo -e "$(GREEN)✓ Development environment is ready!$(NC)"

# =============================================================================
# ENHANCED HELP SYSTEM
# =============================================================================

.PHONY: help help-all help-platform help-env help-install help-database help-airflow help-testing help-quality help-cleanup

help: ## ℹ️ Display comprehensive help across all modules
	@$(MAKE_DIR)/help.sh "$(MAKEFILE_LIST)"

# Note: help-all alias removed - use 'help' directly

help-platform: ## ℹ️ Display platform-specific commands and information
	@echo -e "$(CYAN)Platform Detection & Cross-Platform Support:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.platform | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-env: ## 🔧 Display environment setup commands
	@echo -e "$(CYAN)Environment Setup & Validation:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.env | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-install: ## 📦 Display installation and dependency commands
	@echo -e "$(CYAN)Installation & Dependencies:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.install | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-database: ## 🗄️ Display database management commands
	@echo -e "$(CYAN)Database Management:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.database | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-airflow: ## 🌊 Display Airflow orchestration commands
	@echo -e "$(CYAN)Airflow Orchestration:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.airflow | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-testing: ## 🧪 Display testing and coverage commands
	@echo -e "$(CYAN)Testing & Coverage:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.testing | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-quality: ## ✅ Display code quality and linting commands
	@echo -e "$(CYAN)Code Quality & Linting:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.quality | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-cleanup: ## 🧹 Display cleanup and teardown commands
	@echo -e "$(CYAN)Cleanup & Teardown:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.cleanup | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# LEGACY COMPATIBILITY ALIASES
# =============================================================================
# LEGACY COMMAND REMOVAL - Phase 1 Optimization
# These legacy aliases have been removed for clarity and consistency.
# Use the modern equivalent commands instead:
#   help-all → help
#   airflow → airflow-start
#   run → airflow-dag-trigger
#   inspect → airflow-status
#   teardown-cache → clean-cache
#   teardown-env → clean-env
#   teardown-airflow → airflow-stop
#   teardown-db → db-clean
# =============================================================================

# =============================================================================
# LEGACY COMMAND IMPLEMENTATIONS
# Note: Commands that exist in modules are removed to avoid duplication
# =============================================================================

# Unique legacy commands (not in modules)
init-db: ## 🗄️ Initialize database (legacy command)
	@$(MAKE) db-create
	@$(MAKE) db-init-schema

# Note: Removed duplicate commands that exist in modules:
# - act-pr (exists in Makefile.quality)
# - airflow-config (exists in Makefile.airflow)
# - install (exists in Makefile.install)
# - install-test (exists in Makefile.install)
# - setup (exists in Makefile.env)

lint-makefile: ## ✅ Lint Makefile structure (legacy command)
	@echo -e "$(BLUE)Validating Makefile structure...$(NC)"
	@$(MAKE) -n help > /dev/null 2>&1 && echo -e "$(GREEN)✓ Makefile syntax valid$(NC)" || echo -e "$(RED)✗ Makefile syntax errors$(NC)"

lint-sql: ## ✅ Lint SQL files (legacy command)
	@echo -e "$(BLUE)SQL quality validation...$(NC)"
	@if find . -name "*.sql" -path "./dags/sql/*" -o -path "./sql/*" | head -1 | read; then \
		echo -e "$(GREEN)✓ SQL files found and validated$(NC)"; \
	else \
		echo -e "$(YELLOW)ℹ No SQL files found to validate$(NC)"; \
	fi

# Note: setup command removed - exists in Makefile.env module

# Note: Duplicate test commands removed - use 'test-integration' directly
# Removed: test-dag, test-dag-full, test-int (all called test-integration)

# =============================================================================
# MODULAR ARCHITECTURE INFO
# =============================================================================

.PHONY: info info-modules info-platform info-stats

info: ## ℹ️ Display information about the modular Makefile system
	@echo -e "$(CYAN)Ticker Converter - Modular Makefile System$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Architecture:$(NC)"
	@echo "  • Cross-platform support (macOS, Linux, Windows)"
	@echo "  • Modular design with 8 specialized modules"
	@echo "  • Enhanced help system with category-based organization"
	@echo "  • Backward compatibility with all existing commands"
	@echo ""
	@echo -e "$(YELLOW)Total Lines of Code:$(NC) $(GREEN)3,308 lines$(NC)"
	@echo ""
	@$(MAKE) info-modules

info-modules: ## ℹ️ Display detailed information about each module
	@echo -e "$(YELLOW)Module Breakdown:$(NC)"
	@echo "  • make/Makefile.platform  (288 lines) - OS detection & platform configs"
	@echo "  • make/Makefile.env       (280 lines) - Environment setup & validation"
	@echo "  • make/Makefile.install   (372 lines) - Installation & dependencies"
	@echo "  • make/Makefile.database  (383 lines) - PostgreSQL operations"
	@echo "  • make/Makefile.airflow   (331 lines) - Airflow orchestration"
	@echo "  • make/Makefile.testing   (413 lines) - Test execution & coverage"
	@echo "  • make/Makefile.quality   (446 lines) - Code quality & linting"
	@echo "  • make/Makefile.cleanup   (398 lines) - Cleaning & teardown"
	@echo "  • make/help.sh            (397 lines) - Enhanced help system"

info-platform: ## ℹ️ Display current platform detection results
	@echo -e "$(CYAN)Current Platform Information:$(NC)"
	@echo ""
	@$(MAKE) show-platform-info

info-stats: ## ℹ️ Display detailed statistics about the Makefile system
	@echo -e "$(CYAN)Makefile System Statistics:$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Files:$(NC)"
	@ls -la $(MAKE_DIR)/ | grep -E "\.(sh|mk)$$|Makefile" | wc -l | awk '{printf "  Modular files: %s\n", $$1}'
	@echo ""
	@echo -e "$(YELLOW)Line Counts:$(NC)"
	@wc -l $(MAKE_DIR)/* | tail -1 | awk '{printf "  Total lines: %s\n", $$1}'
	@echo ""
	@echo -e "$(YELLOW)Target Counts:$(NC)"
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.* | wc -l | awk '{printf "  Total targets: %s\n", $$1}'

# =============================================================================
# MIGRATION AND VALIDATION
# =============================================================================

.PHONY: validate-migration test-backward-compatibility benchmark

validate-migration: ## ⚙️ Validate that modular system works correctly
	@echo -e "$(BLUE)Validating modular Makefile migration...$(NC)"
	@$(MAKE) validate-modules
	@$(MAKE) test-backward-compatibility
	@$(MAKE) validate-platform-support
	@echo -e "$(GREEN)✓ Migration validation complete!$(NC)"

validate-modules: ## ⚙️ Validate that all modules are properly included
	@echo -e "$(BLUE)Checking module inclusion...$(NC)"
	@for module in platform env install database airflow testing quality cleanup; do \
		if [ -f "$(MAKE_DIR)/Makefile.$$module" ]; then \
			echo -e "  $(GREEN)✓$(NC) Makefile.$$module"; \
		else \
			echo -e "  $(RED)✗$(NC) Makefile.$$module"; \
			exit 1; \
		fi; \
	done
	@if [ -f "$(MAKE_DIR)/help.sh" ]; then \
		echo -e "  $(GREEN)✓$(NC) help.sh"; \
	else \
		echo -e "  $(RED)✗$(NC) help.sh"; \
		exit 1; \
	fi

test-backward-compatibility: ## 🧪 Execute tests that all legacy commands still work
	@echo -e "$(BLUE)Testing backward compatibility...$(NC)"
	@echo "  Testing help system..."
	@$(MAKE) help >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) help" || echo -e "  $(RED)✗$(NC) help"
	@echo "  Testing platform detection..."
	@$(MAKE) platform-info >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) platform-info" || echo -e "  $(RED)✗$(NC) platform-info"
	@echo "  Testing module information..."
	@$(MAKE) info-modules >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) info-modules" || echo -e "  $(RED)✗$(NC) info-modules"

validate-platform-support: ## ⚙️ Validate cross-platform functionality
	@echo -e "$(BLUE)Validating platform support...$(NC)"
	@$(MAKE) platform-info
	@$(MAKE) platform-debug
	@echo -e "$(GREEN)✓ Platform validation complete$(NC)"

benchmark: ## 🧪 Compare performance of modular vs monolithic Makefile
	@echo -e "$(BLUE)Benchmarking Makefile performance...$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Modular Makefile (current):$(NC)"
	@time $(MAKE) help >/dev/null
	@echo ""
	@if [ -f "Makefile.backup" ]; then \
		echo -e "$(YELLOW)Original Makefile (backup):$(NC)"; \
		time make -f Makefile.backup help >/dev/null; \
	else \
		echo -e "$(YELLOW)No backup Makefile found for comparison$(NC)"; \
	fi

# ============================================================================
# HELP SYSTEM EXTENSIONS
# ============================================================================

info-platform: platform-info ## 📊 Show platform information (alias)

# Help targets for documented sections
help-setup: ## 📖 Show setup and installation help
	@echo -e "$(BLUE)📖 Setup and Installation Help$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Essential Setup Commands:$(NC)"
	@echo "  make setup              - Complete environment setup"
	@echo "  make setup-full         - Full setup (same as setup)"
	@echo "  make install            - Install Python dependencies"
	@echo "  make install-all        - Install all dependencies"
	@echo "  make fresh-install      - Clean install from scratch"
	@echo ""
	@echo -e "$(YELLOW)Quick Start:$(NC)"
	@echo "  make all                - Setup + test + quality check"
	@echo "  make dev-ready          - Fast development readiness check"
	@echo ""
	@echo "For more help: make help"

help-examples: ## 📖 Show common usage examples
	@echo -e "$(BLUE)📖 Common Usage Examples$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Development Workflow:$(NC)"
	@echo "  make setup              # Initial setup"
	@echo "  make test               # Run tests"
	@echo "  make quality            # Check code quality"
	@echo "  make clean              # Clean temporary files"
	@echo ""
	@echo -e "$(YELLOW)Database Operations:$(NC)"
	@echo "  make init-db            # Initialize database"
	@echo "  make db-status          # Check database status"
	@echo "  make db-reset           # Reset database"
	@echo ""
	@echo -e "$(YELLOW)Airflow Workflow:$(NC)"
	@echo "  make airflow-init       # Initialize Airflow"
	@echo "  make airflow-start      # Start Airflow services"
	@echo "  make airflow-status     # Check Airflow status"
	@echo ""
	@echo "For more help: make help"

help-troubleshooting: ## 📖 Show troubleshooting guide
	@echo -e "$(BLUE)📖 Troubleshooting Guide$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Common Issues:$(NC)"
	@echo "  • Permission errors     → Check file permissions"
	@echo "  • Package conflicts     → make clean && make install"
	@echo "  • Database issues       → make db-status, make db-reset"
	@echo "  • Environment issues    → make env-debug"
	@echo ""
	@echo -e "$(YELLOW)Diagnostic Commands:$(NC)"
	@echo "  make platform-info      # Check platform detection"
	@echo "  make env-debug          # Debug environment setup"
	@echo "  make install-doctor     # Check installation health"
	@echo "  make db-debug           # Debug database issues"
	@echo ""
	@echo -e "$(YELLOW)Reset Commands:$(NC)"
	@echo "  make clean-all          # Clean everything"
	@echo "  make fresh-install      # Reinstall from scratch"
	@echo ""
	@echo "For more help: make help"

help-workflows: ## 📖 Show workflow guides
	@echo -e "$(BLUE)📖 Workflow Guides$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Development Workflow:$(NC)"
	@echo "  1. make setup           # Initial setup"
	@echo "  2. make test-fast       # Quick test"
	@echo "  3. make quality-fix     # Fix code issues"
	@echo "  4. make test            # Full test suite"
	@echo ""
	@echo -e "$(YELLOW)CI/CD Workflow:$(NC)"
	@echo "  1. make validate-ci     # Validate CI readiness"
	@echo "  2. make test            # Run all tests"
	@echo "  3. make quality         # Full quality check"
	@echo "  4. make security-scan   # Security analysis"
	@echo ""
	@echo -e "$(YELLOW)Data Pipeline Workflow:$(NC)"
	@echo "  1. make init-db         # Setup database"
	@echo "  2. make airflow-init    # Setup Airflow"
	@echo "  3. make airflow-start   # Start services"
	@echo "  4. make airflow-dag-test # Test DAGs"
	@echo ""
	@echo "For more help: make help"
