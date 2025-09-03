#!/usr/bin/env bash
# ============================================================================
# ENHANCED HELP SYSTEM
# ============================================================================
# Provides comprehensive command documentation and usage guidance
# for the modular Makefile system with cross-platform support
# ============================================================================

# Color definitions for cross-platform compatibility
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows terminal colors
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    # Unix-like terminal colors
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
fi

# ============================================================================
# HELP CATEGORIES AND CONTENT
# ============================================================================

show_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                           TICKER CONVERTER                                  ║${NC}"
    echo -e "${BLUE}║                     Cross-Platform Build System                             ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_quick_start() {
    echo -e "${WHITE}${BOLD}QUICK START GUIDE${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}1. Initial Setup:${NC}"
    echo -e "   ${CYAN}make setup${NC}              # Configure environment and dependencies"
    echo -e ""
    echo -e "${GREEN}2. Choose Installation Mode:${NC}"
    echo -e "   ${CYAN}make install${NC}            # Production runtime dependencies"
    echo -e "   ${CYAN}make install-test${NC}       # Testing and quality assurance tools"
    echo -e "   ${CYAN}make install-test${NC}       # Full development environment"
    echo -e ""
    echo -e "${GREEN}3. Start Development:${NC}"
    echo -e "   ${CYAN}make test${NC}               # Run test suite"
    echo -e "   ${CYAN}make quality${NC}            # Code quality checks"
    echo -e "   ${CYAN}make db-start${NC}           # Start PostgreSQL database"
    echo -e "   ${CYAN}make airflow-start${NC}      # Launch Airflow orchestration"
    echo -e ""
    echo -e "${GREEN}4. Get Help:${NC}"
    echo -e "   ${CYAN}make help${NC}               # This help system"
    echo -e "   ${CYAN}make help-<category>${NC}    # Category-specific help"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

show_categories() {
    echo -e "${WHITE}${BOLD}AVAILABLE HELP CATEGORIES${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}make help-setup${NC}          Environment setup and platform configuration"
    echo -e "${CYAN}make help-install${NC}        Dependency installation and package management"
    echo -e "${CYAN}make help-database${NC}       PostgreSQL operations and data management"
    echo -e "${CYAN}make help-airflow${NC}        Airflow orchestration and workflow management"
    echo -e "${CYAN}make help-testing${NC}        Test execution and coverage analysis"
    echo -e "${CYAN}make help-quality${NC}        Code quality, linting, and validation"
    echo -e "${CYAN}make help-cleanup${NC}        Cleaning and teardown operations"
    echo -e "${CYAN}make help-platform${NC}       Platform detection and cross-platform features"
    echo ""
    echo -e "${WHITE}${BOLD}SPECIALIZED HELP${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}make help-workflows${NC}      Common development workflows and patterns"
    echo -e "${CYAN}make help-troubleshooting${NC} Problem diagnosis and solutions"
    echo -e "${CYAN}make help-examples${NC}       Usage examples and common scenarios"
    echo ""
}

show_setup_help() {
    echo -e "${WHITE}${BOLD}ENVIRONMENT SETUP AND CONFIGURATION${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Initial Setup:${NC}"
    echo -e "  ${CYAN}setup${NC}                   Initialize project environment and dependencies"
    echo -e "  ${CYAN}env-info${NC}                Display current environment configuration"
    echo -e "  ${CYAN}env-debug${NC}               Show detailed environment debug information"
    echo -e "  ${CYAN}env-test${NC}                Test environment setup and validation"
    echo -e ""
    echo -e "${GREEN}Platform Information:${NC}"
    echo -e "  ${CYAN}platform-info${NC}           Show platform detection results"
    echo -e "  ${CYAN}platform-debug${NC}          Detailed platform and tool availability"
    echo -e ""
    echo -e "${PURPLE}Environment Variables Required:${NC}"
    echo -e "  ${YELLOW}ALPHA_VANTAGE_API_KEY${NC}   API key for market data (get from alphavantage.co)"
    echo -e "  ${YELLOW}POSTGRES_*${NC}              Database connection configuration"
    echo -e "  ${YELLOW}AIRFLOW_*${NC}               Airflow admin and authentication settings"
    echo ""
}

show_install_help() {
    echo -e "${WHITE}${BOLD}DEPENDENCY INSTALLATION AND PACKAGE MANAGEMENT${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Installation Modes:${NC}"
    echo -e "  ${CYAN}install${NC}                 Production runtime dependencies"
    echo -e "  ${CYAN}install-test${NC}            Testing and quality assurance tools"
    echo -e "  ${CYAN}install-test${NC}            Full development environment"
    echo -e "  ${CYAN}install-all${NC}             All dependencies (runtime + test + dev)"
    echo -e ""
    echo -e "${GREEN}Package Management:${NC}"
    echo -e "  ${CYAN}pip-list${NC}                List installed packages"
    echo -e "  ${CYAN}pip-outdated${NC}            Check for package updates"
    echo -e "  ${CYAN}pip-update${NC}              Update pip and setuptools"
    echo -e ""
    echo -e "${GREEN}System Dependencies:${NC}"
    echo -e "  ${CYAN}check-tools${NC}             Verify required system tools availability"
    echo -e "  ${CYAN}install-system-deps${NC}     Install system-level dependencies"
    echo ""
}

show_database_help() {
    echo -e "${WHITE}${BOLD}POSTGRESQL OPERATIONS AND DATA MANAGEMENT${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Database Lifecycle:${NC}"
    echo -e "  ${CYAN}db-start${NC}                Start PostgreSQL service"
    echo -e "  ${CYAN}db-stop${NC}                 Stop PostgreSQL service"
    echo -e "  ${CYAN}db-restart${NC}              Restart PostgreSQL service"
    echo -e "  ${CYAN}db-status${NC}               Check PostgreSQL service status"
    echo -e ""
    echo -e "${GREEN}Database Operations:${NC}"
    echo -e "  ${CYAN}db-create${NC}               Create project database"
    echo -e "  ${CYAN}db-drop${NC}                 Drop project database"
    echo -e "  ${CYAN}db-reset${NC}                Drop and recreate database"
    echo -e "  ${CYAN}db-migrate${NC}              Run database migrations"
    echo -e ""
    echo -e "${GREEN}Data Management:${NC}"
    echo -e "  ${CYAN}db-seed${NC}                 Load initial data"
    echo -e "  ${CYAN}db-backup${NC}               Create database backup"
    echo -e "  ${CYAN}db-restore${NC}              Restore from backup"
    echo -e "  ${CYAN}db-shell${NC}                Open PostgreSQL shell"
    echo ""
}

show_airflow_help() {
    echo -e "${WHITE}${BOLD}AIRFLOW ORCHESTRATION AND WORKFLOW MANAGEMENT${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Airflow Lifecycle:${NC}"
    echo -e "  ${CYAN}airflow-start${NC}           Start Airflow (scheduler + webserver)"
    echo -e "  ${CYAN}airflow-stop${NC}            Stop all Airflow processes"
    echo -e "  ${CYAN}airflow-restart${NC}         Restart Airflow services"
    echo -e "  ${CYAN}airflow-status${NC}          Check Airflow process status"
    echo -e ""
    echo -e "${GREEN}Airflow Management:${NC}"
    echo -e "  ${CYAN}airflow-init${NC}            Initialize Airflow database and admin user"
    echo -e "  ${CYAN}airflow-reset${NC}           Reset Airflow configuration and database"
    echo -e "  ${CYAN}airflow-shell${NC}           Open Airflow shell for debugging"
    echo -e "  ${CYAN}airflow-logs${NC}            View Airflow logs"
    echo -e ""
    echo -e "${GREEN}DAG Operations:${NC}"
    echo -e "  ${CYAN}airflow-dag-list${NC}        List available DAGs"
    echo -e "  ${CYAN}airflow-dag-test${NC}        Test DAG execution"
    echo -e "  ${CYAN}airflow-dag-trigger${NC}     Manually trigger DAG run"
    echo ""
}

show_testing_help() {
    echo -e "${WHITE}${BOLD}TEST EXECUTION AND COVERAGE ANALYSIS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Test Execution:${NC}"
    echo -e "  ${CYAN}test${NC}                    Run full test suite"
    echo -e "  ${CYAN}test-unit${NC}               Run unit tests only"
    echo -e "  ${CYAN}test-integration${NC}        Run integration tests only"
    echo -e "  ${CYAN}test-fast${NC}               Run tests in parallel (fast mode)"
    echo -e ""
    echo -e "${GREEN}Coverage Analysis:${NC}"
    echo -e "  ${CYAN}test-coverage${NC}           Run tests with coverage reporting"
    echo -e "  ${CYAN}coverage-report${NC}         Generate coverage reports"
    echo -e "  ${CYAN}coverage-html${NC}           Generate HTML coverage report"
    echo -e "  ${CYAN}coverage-open${NC}           Open HTML coverage report in browser"
    echo -e ""
    echo -e "${GREEN}Test Utilities:${NC}"
    echo -e "  ${CYAN}test-watch${NC}              Run tests in watch mode (continuous)"
    echo -e "  ${CYAN}test-debug${NC}              Run tests with debugging enabled"
    echo -e "  ${CYAN}test-profile${NC}            Run performance profiling on tests"
    echo ""
}

show_quality_help() {
    echo -e "${WHITE}${BOLD}CODE QUALITY, LINTING, AND VALIDATION${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Code Quality Suite:${NC}"
    echo -e "  ${CYAN}quality${NC}                 Run all code quality checks"
    echo -e "  ${CYAN}quality-fix${NC}             Auto-fix code quality issues where possible"
    echo -e ""
    echo -e "${GREEN}Individual Tools:${NC}"
    echo -e "  ${CYAN}black${NC}                   Format code with Black"
    echo -e "  ${CYAN}black-check${NC}             Check Black formatting without changes"
    echo -e "  ${CYAN}pylint${NC}                  Run Pylint static analysis"
    echo -e "  ${CYAN}mypy${NC}                    Run MyPy type checking"
    echo -e "  ${CYAN}ruff${NC}                    Run Ruff linting and formatting"
    echo -e ""
    echo -e "${GREEN}Security and Validation:${NC}"
    echo -e "  ${CYAN}security-scan${NC}           Run security vulnerability scanning"
    echo -e "  ${CYAN}pre-commit${NC}              Run pre-commit hooks"
    echo -e "  ${CYAN}validate-all${NC}            Full validation pipeline"
    echo ""
}

show_cleanup_help() {
    echo -e "${WHITE}${BOLD}CLEANING AND TEARDOWN OPERATIONS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Build Artifacts:${NC}"
    echo -e "  ${CYAN}clean${NC}                   Remove all build artifacts and cache"
    echo -e "  ${CYAN}clean-build${NC}             Remove build directories only"
    echo -e "  ${CYAN}clean-cache${NC}             Remove Python cache files"
    echo -e "  ${CYAN}clean-coverage${NC}          Remove coverage reports"
    echo -e ""
    echo -e "${GREEN}Development Environment:${NC}"
    echo -e "  ${CYAN}clean-env${NC}               Remove virtual environment"
    echo -e "  ${CYAN}clean-logs${NC}              Remove log files"
    echo -e "  ${CYAN}clean-temp${NC}              Remove temporary files"
    echo -e ""
    echo -e "${GREEN}Services and Data:${NC}"
    echo -e "  ${CYAN}clean-db${NC}                Remove database data"
    echo -e "  ${CYAN}clean-airflow${NC}           Remove Airflow data and logs"
    echo -e "  ${CYAN}clean-all${NC}               Complete cleanup (use with caution)"
    echo ""
}

show_platform_help() {
    echo -e "${WHITE}${BOLD}PLATFORM DETECTION AND CROSS-PLATFORM FEATURES${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Platform Information:${NC}"
    echo -e "  ${CYAN}platform-info${NC}           Show current platform details"
    echo -e "  ${CYAN}platform-debug${NC}          Detailed platform debugging information"
    echo -e ""
    echo -e "${GREEN}Supported Platforms:${NC}"
    echo -e "  ${YELLOW}macOS${NC}                   Darwin-based systems (Intel/Apple Silicon)"
    echo -e "  ${YELLOW}Linux${NC}                   Ubuntu, Debian, RHEL, CentOS, Arch"
    echo -e "  ${YELLOW}Windows${NC}                 Windows 10/11 with WSL or native"
    echo -e ""
    echo -e "${GREEN}Tool Detection:${NC}"
    echo -e "  ${CYAN}check-tools${NC}             Verify system tool availability"
    echo -e "  Automatically detects: ${YELLOW}brew, apt, yum, pacman, choco, docker, git${NC}"
    echo ""
}

show_workflows_help() {
    echo -e "${WHITE}${BOLD}COMMON DEVELOPMENT WORKFLOWS AND PATTERNS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}New Developer Setup:${NC}"
    echo -e "  ${CYAN}make setup && make install-test && make test${NC}"
    echo -e ""
    echo -e "${GREEN}Daily Development:${NC}"
    echo -e "  ${CYAN}make db-start && make airflow-start${NC}     # Start services"
    echo -e "  ${CYAN}make test-watch${NC}                         # Continuous testing"
    echo -e "  ${CYAN}make quality${NC}                            # Before committing"
    echo -e ""
    echo -e "${GREEN}CI/CD Pipeline:${NC}"
    echo -e "  ${CYAN}make quality && make test && make security-scan${NC}"
    echo -e ""
    echo -e "${GREEN}Production Deployment:${NC}"
    echo -e "  ${CYAN}make install && make db-migrate && make airflow-init${NC}"
    echo -e ""
    echo -e "${GREEN}Troubleshooting:${NC}"
    echo -e "  ${CYAN}make platform-debug && make env-debug${NC}   # Diagnose issues"
    echo -e "  ${CYAN}make clean-all && make setup${NC}            # Fresh start"
    echo ""
}

show_troubleshooting_help() {
    echo -e "${WHITE}${BOLD}PROBLEM DIAGNOSIS AND SOLUTIONS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Environment Issues:${NC}"
    echo -e "  ${RED}Problem:${NC} 'Python not found'"
    echo -e "  ${CYAN}Solution:${NC} make platform-debug, install Python via suggested method"
    echo -e ""
    echo -e "  ${RED}Problem:${NC} 'Virtual environment not working'"
    echo -e "  ${CYAN}Solution:${NC} make clean-env && make setup"
    echo -e ""
    echo -e "${GREEN}Database Issues:${NC}"
    echo -e "  ${RED}Problem:${NC} 'PostgreSQL connection failed'"
    echo -e "  ${CYAN}Solution:${NC} make db-status, check .env configuration"
    echo -e ""
    echo -e "  ${RED}Problem:${NC} 'Database doesn't exist'"
    echo -e "  ${CYAN}Solution:${NC} make db-create && make db-migrate"
    echo -e ""
    echo -e "${GREEN}Airflow Issues:${NC}"
    echo -e "  ${RED}Problem:${NC} 'Airflow webserver not starting'"
    echo -e "  ${CYAN}Solution:${NC} make airflow-reset && make airflow-init"
    echo -e ""
    echo -e "  ${RED}Problem:${NC} 'DAGs not loading'"
    echo -e "  ${CYAN}Solution:${NC} Check AIRFLOW_HOME, verify DAG syntax"
    echo -e ""
    echo -e "${GREEN}Test Issues:${NC}"
    echo -e "  ${RED}Problem:${NC} 'Tests failing after changes'"
    echo -e "  ${CYAN}Solution:${NC} make test-debug, check test dependencies"
    echo ""
}

show_examples_help() {
    echo -e "${WHITE}${BOLD}USAGE EXAMPLES AND COMMON SCENARIOS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Scenario 1: First-time setup on macOS${NC}"
    echo -e "  ${CYAN}make setup${NC}               # Configure environment"
    echo -e "  ${CYAN}make install-test${NC}       # Install all dependencies"
    echo -e "  ${CYAN}make db-start${NC}           # Start PostgreSQL"
    echo -e "  ${CYAN}make db-create${NC}          # Create database"
    echo -e "  ${CYAN}make test${NC}               # Verify everything works"
    echo -e ""
    echo -e "${GREEN}Scenario 2: Running in production on Linux${NC}"
    echo -e "  ${CYAN}make setup${NC}               # Configure environment"
    echo -e "  ${CYAN}make install${NC}            # Production dependencies only"
    echo -e "  ${CYAN}make db-migrate${NC}         # Apply database schema"
    echo -e "  ${CYAN}make airflow-init${NC}       # Initialize Airflow"
    echo -e ""
    echo -e "${GREEN}Scenario 3: Testing changes before commit${NC}"
    echo -e "  ${CYAN}make quality${NC}            # Code quality checks"
    echo -e "  ${CYAN}make test-coverage${NC}      # Run tests with coverage"
    echo -e "  ${CYAN}make security-scan${NC}      # Security validation"
    echo -e ""
    echo -e "${GREEN}Scenario 4: Debugging failed tests${NC}"
    echo -e "  ${CYAN}make test-debug${NC}         # Run tests with debugging"
    echo -e "  ${CYAN}make env-debug${NC}          # Check environment setup"
    echo -e "  ${CYAN}make platform-debug${NC}     # Platform-specific issues"
    echo ""
}

# ============================================================================
# MAIN HELP DISPATCHER
# ============================================================================

show_main_help() {
    show_header
    show_quick_start
    show_categories
}

# Parse command line argument for specific help topic
case "${1:-}" in
    "setup")
        show_header
        show_setup_help
        ;;
    "install")
        show_header
        show_install_help
        ;;
    "database")
        show_header
        show_database_help
        ;;
    "airflow")
        show_header
        show_airflow_help
        ;;
    "testing")
        show_header
        show_testing_help
        ;;
    "quality")
        show_header
        show_quality_help
        ;;
    "cleanup")
        show_header
        show_cleanup_help
        ;;
    "platform")
        show_header
        show_platform_help
        ;;
    "workflows")
        show_header
        show_workflows_help
        ;;
    "troubleshooting")
        show_header
        show_troubleshooting_help
        ;;
    "examples")
        show_header
        show_examples_help
        ;;
    *)
        show_main_help
        ;;
esac
