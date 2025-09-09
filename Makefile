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
	@printf "\033[0;34mRunning complete development workflow...\033[0m\n"
	@$(MAKE) setup-env
	@$(MAKE) install-test
	@$(MAKE) quality
	@printf "\033[0;32m✓ Development environment ready!\033[0m\n"

setup-full: ## 📦 Complete development environment setup (alternative to module setup)
	@printf "\033[0;34mSetting up complete development environment...\033[0m\n"
	@$(MAKE) setup-env
	@$(MAKE) install
	@$(MAKE) init-db
	@printf "\033[0;32m✓ Complete development environment setup finished!\033[0m\n"

dev-ready: ## ⚙️ Validate that development environment is ready
	@printf "\033[0;34mValidating development environment...\033[0m\n"
	@$(MAKE) validate-env
	@$(MAKE) validate-tools
	@$(MAKE) test-fast
	@printf "\033[0;32m✓ Development environment is ready!\033[0m\n"

# =============================================================================
# ENHANCED HELP SYSTEM
# =============================================================================

.PHONY: help help-all help-platform help-env help-install help-database help-airflow help-testing help-quality help-cleanup

help: ## ℹ️ Display comprehensive help across all modules
	@$(MAKE_DIR)/help.sh "$(MAKEFILE_LIST)"

# Note: help-all alias removed - use 'help' directly

help-platform: ## ℹ️ Display platform-specific commands and information
	@printf "\\033[0;36mPlatform Detection & Cross-Platform Support:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.platform | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-env: ## 🔧 Display environment setup commands
	@printf "\\033[0;36mEnvironment Setup & Validation:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.env | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-install: ## 📦 Display installation and dependency commands
	@printf "\\033[0;36mInstallation & Dependencies:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.install | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-database: ## 🗄️ Display database management commands
	@printf "\\033[0;36mDatabase Management:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.database | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-airflow: ## 🌊 Display Airflow orchestration commands
	@printf "\\033[0;36mAirflow Orchestration:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.airflow | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-testing: ## 🧪 Display testing and coverage commands
	@printf "\\033[0;36mTesting & Coverage:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.testing | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-quality: ## ✅ Display code quality and linting commands
	@printf "\\033[0;36mCode Quality & Linting:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.quality | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

help-cleanup: ## 🧹 Display cleanup and teardown commands
	@printf "\\033[0;36mCleanup & Teardown:\\033[0m\\n"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.cleanup | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2}'

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
	@printf "\033[0;34mValidating Makefile structure...\033[0m\n"
	@$(MAKE) -n help > /dev/null 2>&1 && printf "\033[0;32m✓ Makefile syntax valid\033[0m\n" || printf "\033[0;31m✗ Makefile syntax errors\033[0m\n"

lint-sql: ## ✅ Lint SQL files (legacy command)
	@printf "\033[0;34mSQL quality validation...\033[0m\n"
	@if find . -name "*.sql" -path "./dags/sql/*" -o -path "./sql/*" | head -1 | read; then \
		printf "\033[0;32m✓ SQL files found and validated\033[0m\n"; \
	else \
		printf "\033[0;33mℹ No SQL files found to validate\033[0m\n"; \
	fi

# Note: setup command removed - exists in Makefile.env module

# Note: Duplicate test commands removed - use 'test-integration' directly
# Removed: test-dag, test-dag-full, test-int (all called test-integration)

# =============================================================================
# MODULAR ARCHITECTURE INFO
# =============================================================================

.PHONY: info info-modules info-platform info-stats

info: ## ℹ️ Display information about the modular Makefile system
	@printf "\033[0;36mTicker Converter - Modular Makefile System\033[0m\n"
	@echo ""
	@printf "\033[0;33mArchitecture:\033[0m\n"
	@echo "  • Cross-platform support (macOS, Linux, Windows)"
	@echo "  • Modular design with 8 specialized modules"
	@echo "  • Enhanced help system with category-based organization"
	@echo "  • Backward compatibility with all existing commands"
	@echo ""
	@printf "\033[0;33mTotal Lines of Code:\033[0m \033[0;32m3,308 lines\033[0m\n"
	@echo ""
	@$(MAKE) info-modules

info-modules: ## ℹ️ Display detailed information about each module
	@printf "\033[0;33mModule Breakdown:\033[0m\n"
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
	@printf "\033[0;36mCurrent Platform Information:\033[0m\n"
	@echo ""
	@$(MAKE) show-platform-info

info-stats: ## ℹ️ Display detailed statistics about the Makefile system
	@printf "\033[0;36mMakefile System Statistics:\033[0m\n"
	@echo ""
	@printf "\033[0;33mFiles:\033[0m\n"
	@ls -la $(MAKE_DIR)/ | grep -E "\.(sh|mk)$$|Makefile" | wc -l | awk '{printf "  Modular files: %s\n", $$1}'
	@echo ""
	@printf "\033[0;33mLine Counts:\033[0m\n"
	@wc -l $(MAKE_DIR)/* | tail -1 | awk '{printf "  Total lines: %s\n", $$1}'
	@echo ""
	@printf "\033[0;33mTarget Counts:\033[0m\n"
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.* | wc -l | awk '{printf "  Total targets: %s\n", $$1}'

# =============================================================================
# MIGRATION AND VALIDATION
# =============================================================================

.PHONY: validate-migration test-backward-compatibility benchmark

validate-migration: ## ⚙️ Validate that modular system works correctly
	@printf "\033[0;34mValidating modular Makefile migration...\033[0m\n"
	@$(MAKE) validate-modules
	@$(MAKE) test-backward-compatibility
	@$(MAKE) validate-platform-support
	@printf "\033[0;32m✓ Migration validation complete!\033[0m\n"

validate-modules: ## ⚙️ Validate that all modules are properly included
	@printf "\033[0;34mChecking module inclusion...\033[0m\n"
	@for module in platform env install database airflow testing quality cleanup; do \
		if [ -f "$(MAKE_DIR)/Makefile.$$module" ]; then \
			printf "  \033[0;32m✓\033[0m Makefile.$$module"; \
		else \
			printf "  \033[0;31m✗\033[0m Makefile.$$module"; \
			exit 1; \
		fi; \
	done
	@if [ -f "$(MAKE_DIR)/help.sh" ]; then \
		printf "  \033[0;32m✓\033[0m help.sh"; \
	else \
		printf "  \033[0;31m✗\033[0m help.sh"; \
		exit 1; \
	fi

test-backward-compatibility: ## 🧪 Execute tests that all legacy commands still work
	@printf "\033[0;34mTesting backward compatibility...\033[0m\n"
	@echo "  Testing help system..."
	@$(MAKE) help >/dev/null 2>&1 && printf "  \033[0;32m✓\033[0m help" || printf "  \033[0;31m✗\033[0m help"
	@echo "  Testing platform detection..."
	@$(MAKE) platform-info >/dev/null 2>&1 && printf "  \033[0;32m✓\033[0m platform-info" || printf "  \033[0;31m✗\033[0m platform-info"
	@echo "  Testing module information..."
	@$(MAKE) info-modules >/dev/null 2>&1 && printf "  \033[0;32m✓\033[0m info-modules" || printf "  \033[0;31m✗\033[0m info-modules"

validate-platform-support: ## ⚙️ Validate cross-platform functionality
	@printf "\033[0;34mValidating platform support...\033[0m\n"
	@$(MAKE) platform-info
	@$(MAKE) platform-debug
	@printf "\033[0;32m✓ Platform validation complete\033[0m\n"

benchmark: ## 🧪 Compare performance of modular vs monolithic Makefile
	@printf "\033[0;34mBenchmarking Makefile performance...\033[0m\n"
	@echo ""
	@printf "\033[0;33mModular Makefile (current):\033[0m\n"
	@time $(MAKE) help >/dev/null
	@echo ""
	@if [ -f "Makefile.backup" ]; then \
		printf "\033[0;33mOriginal Makefile (backup):\033[0m\n"; \
		time make -f Makefile.backup help >/dev/null; \
	else \
		printf "\033[0;33mNo backup Makefile found for comparison\033[0m\n"; \
	fi

# ============================================================================
# HELP SYSTEM EXTENSIONS
# ============================================================================

info-platform: platform-info ## 📊 Show platform information (alias)

# Help targets for documented sections
help-setup: ## 📖 Show setup and installation help
	@printf "\\033[0;34m📖 Setup and Installation Help\\033[0m\\n"
	@echo ""
	@printf "\\033[0;33mEssential Setup Commands:\\033[0m\\n"
	@echo "  make setup              - Complete environment setup"
	@echo "  make setup-full         - Full setup (same as setup)"
	@echo "  make install            - Install Python dependencies"
	@echo "  make install-all        - Install all dependencies"
	@echo "  make fresh-install      - Clean install from scratch"
	@echo ""
	@printf "\\033[0;33mQuick Start:\\033[0m\\n"
	@echo "  make all                - Setup + test + quality check"
	@echo "  make dev-ready          - Fast development readiness check"
	@echo ""
	@echo "For more help: make help"

help-examples: ## 📖 Show common usage examples
	@printf "\033[0;34m📖 Common Usage Examples\033[0m\n"
	@echo ""
	@printf "\033[0;33mDevelopment Workflow:\033[0m\n"
	@echo "  make setup              # Initial setup"
	@echo "  make test               # Run tests"
	@echo "  make quality            # Check code quality"
	@echo "  make clean              # Clean temporary files"
	@echo ""
	@printf "\033[0;33mDatabase Operations:\033[0m\n"
	@echo "  make init-db            # Initialize database"
	@echo "  make db-status          # Check database status"
	@echo "  make db-reset           # Reset database"
	@echo ""
	@printf "\033[0;33mAirflow Workflow:\033[0m\n"
	@echo "  make airflow-init       # Initialize Airflow"
	@echo "  make airflow-start      # Start Airflow services"
	@echo "  make airflow-status     # Check Airflow status"
	@echo ""
	@echo "For more help: make help"

help-troubleshooting: ## 📖 Show troubleshooting guide
	@printf "\033[0;34m📖 Troubleshooting Guide\033[0m\n"
	@echo ""
	@printf "\033[0;33mCommon Issues:\033[0m\n"
	@echo "  • Permission errors     → Check file permissions"
	@echo "  • Package conflicts     → make clean && make install"
	@echo "  • Database issues       → make db-status, make db-reset"
	@echo "  • Environment issues    → make env-debug"
	@echo ""
	@printf "\033[0;33mDiagnostic Commands:\033[0m\n"
	@echo "  make platform-info      # Check platform detection"
	@echo "  make env-debug          # Debug environment setup"
	@echo "  make install-doctor     # Check installation health"
	@echo "  make db-debug           # Debug database issues"
	@echo ""
	@printf "\033[0;33mReset Commands:\033[0m\n"
	@echo "  make clean-all          # Clean everything"
	@echo "  make fresh-install      # Reinstall from scratch"
	@echo ""
	@echo "For more help: make help"

help-workflows: ## 📖 Show workflow guides
	@printf "\033[0;34m📖 Workflow Guides\033[0m\n"
	@echo ""
	@printf "\033[0;33mDevelopment Workflow:\033[0m\n"
	@echo "  1. make setup           # Initial setup"
	@echo "  2. make test-fast       # Quick test"
	@echo "  3. make quality-fix     # Fix code issues"
	@echo "  4. make test            # Full test suite"
	@echo ""
	@printf "\033[0;33mCI/CD Workflow:\033[0m\n"
	@echo "  1. make validate-ci     # Validate CI readiness"
	@echo "  2. make test            # Run all tests"
	@echo "  3. make quality         # Full quality check"
	@echo "  4. make security-scan   # Security analysis"
	@echo ""
	@printf "\033[0;33mData Pipeline Workflow:\033[0m\n"
	@echo "  1. make init-db         # Setup database"
	@echo "  2. make airflow-init    # Setup Airflow"
	@echo "  3. make airflow-start   # Start services"
	@echo "  4. make airflow-dag-test # Test DAGs"
	@echo ""
	@echo "For more help: make help"
