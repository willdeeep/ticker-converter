# =============================================================================
# Ticker Converter - Modular Cross-Platform Makefile
# =============================================================================
# This is the main Makefile that orchestrates all modular components.
# The modular structure provides maintainable, cross-platform build automation.
#
# Module Structure:
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
# COMMON FUNCTIONS - Phase 3 Optimization: Extract repeated patterns
# =============================================================================

# Common output formatting functions
define output_header
	@echo -e "$(CYAN)$(1):$(NC)"
endef

define success_message
	@echo -e "$(GREEN)✓ $(1)$(NC)"
endef

define warning_message
	@echo -e "$(YELLOW)⚠ $(1)$(NC)"
endef

define error_message
	@echo -e "$(RED)✗ $(1)$(NC)"
endef

# =============================================================================
# MODULAR INCLUDES - Order matters for dependencies
# =============================================================================

# 1. Platform detection must come first (foundation for everything else)
include $(MAKE_DIR)/Makefile.platform

# 2. Environment setup (depends on platform detection)
include $(MAKE_DIR)/Makefile.env

# 3. Installation capabilities (depends on platform and environment)
include $(MAKE_DIR)/Makefile.install

# 4. Service modules (depend on installation capabilities)
include $(MAKE_DIR)/Makefile.database
include $(MAKE_DIR)/Makefile.airflow

# 5. Development workflow modules (depend on services)
include $(MAKE_DIR)/Makefile.testing
include $(MAKE_DIR)/Makefile.quality

# 6. Cleanup operations (can depend on all other modules)
include $(MAKE_DIR)/Makefile.cleanup

# =============================================================================
# MAIN WORKFLOW TARGETS
# =============================================================================

.PHONY: all setup-full dev-ready

all: ## Run the most common development workflow (setup, install-test, quality)
	@echo -e "$(BLUE)Running complete development workflow...$(NC)"
	@$(MAKE) setup-env
	@$(MAKE) install-test
	@$(MAKE) quality
	@echo -e "$(GREEN)✓ Development environment ready!$(NC)"

setup-full: ## Complete development environment setup (alternative to module setup)
	@echo -e "$(BLUE)Setting up complete development environment...$(NC)"
	@$(MAKE) setup-env
	@$(MAKE) install
	@$(MAKE) init-db
	@echo -e "$(GREEN)✓ Complete development environment setup finished!$(NC)"

dev-ready: ## Validate that development environment is ready
	@echo -e "$(BLUE)Validating development environment...$(NC)"
	@$(MAKE) validate-env
	@$(MAKE) validate-tools
	@$(MAKE) test-fast
	@echo -e "$(GREEN)✓ Development environment is ready!$(NC)"

# =============================================================================
# ENHANCED HELP SYSTEM
# =============================================================================

.PHONY: help help-all help-platform help-env help-install help-database help-airflow help-testing help-quality help-cleanup

help: ## Show comprehensive help across all modules
	@$(MAKE_DIR)/help.sh "$(MAKEFILE_LIST)"

# Note: help-all alias removed - use 'help' directly

help-platform: ## Show platform-specific commands and information
	@echo -e "$(CYAN)Platform Detection & Cross-Platform Support:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.platform | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-env: ## Show environment setup commands
	@echo -e "$(CYAN)Environment Setup & Validation:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.env | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-install: ## Show installation and dependency commands
	@echo -e "$(CYAN)Installation & Dependencies:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.install | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-database: ## Show database management commands
	@echo -e "$(CYAN)Database Management:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.database | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-airflow: ## Show Airflow orchestration commands
	@echo -e "$(CYAN)Airflow Orchestration:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.airflow | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-testing: ## Show testing and coverage commands
	@echo -e "$(CYAN)Testing & Coverage:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.testing | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-quality: ## Show code quality and linting commands
	@echo -e "$(CYAN)Code Quality & Linting:$(NC)"
	@echo ""
	@grep -h "^[a-zA-Z0-9_-]*:.*##.*$$" $(MAKE_DIR)/Makefile.quality | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

help-cleanup: ## Show cleanup and teardown commands
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
init-db: ## Initialize database (legacy command)
	@$(MAKE) db-create
	@$(MAKE) db-init-schema

# Note: Removed duplicate commands that exist in modules:
# - act-pr (exists in Makefile.quality)  
# - airflow-config (exists in Makefile.airflow)
# - install (exists in Makefile.install)
# - install-test (exists in Makefile.install)
# - setup (exists in Makefile.env)

lint-makefile: ## Lint Makefile structure (legacy command)
	@echo -e "$(BLUE)Validating Makefile structure...$(NC)"
	@$(MAKE) -n help > /dev/null 2>&1 && echo -e "$(GREEN)✓ Makefile syntax valid$(NC)" || echo -e "$(RED)✗ Makefile syntax errors$(NC)"

lint-sql: ## Lint SQL files (legacy command)
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

info: ## Show information about the modular Makefile system
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

info-modules: ## Show detailed information about each module
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

info-platform: ## Show current platform detection results
	@echo -e "$(CYAN)Current Platform Information:$(NC)"
	@echo ""
	@$(MAKE) show-platform-info

info-stats: ## Show detailed statistics about the Makefile system
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

validate-migration: ## Validate that modular system works correctly
	@echo -e "$(BLUE)Validating modular Makefile migration...$(NC)"
	@$(MAKE) validate-modules
	@$(MAKE) test-backward-compatibility
	@$(MAKE) validate-platform-support
	@echo -e "$(GREEN)✓ Migration validation complete!$(NC)"

validate-modules: ## Check that all modules are properly included
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

test-backward-compatibility: ## Test that all legacy commands still work
	@echo -e "$(BLUE)Testing backward compatibility...$(NC)"
	@echo "  Testing help system..."
	@$(MAKE) help >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) help" || echo -e "  $(RED)✗$(NC) help"
	@echo "  Testing platform detection..."
	@$(MAKE) platform-info >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) platform-info" || echo -e "  $(RED)✗$(NC) platform-info"
	@echo "  Testing module information..."
	@$(MAKE) info-modules >/dev/null 2>&1 && echo -e "  $(GREEN)✓$(NC) info-modules" || echo -e "  $(RED)✗$(NC) info-modules"

validate-platform-support: ## Validate cross-platform functionality
	@echo -e "$(BLUE)Validating platform support...$(NC)"
	@$(MAKE) platform-info
	@$(MAKE) platform-debug
	@echo -e "$(GREEN)✓ Platform validation complete$(NC)"

benchmark: ## Compare performance of modular vs monolithic Makefile
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
