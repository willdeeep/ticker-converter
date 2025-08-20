#!/usr/bin/env bash
"""
Install optional linting tools for enhanced quality pipeline.

This script installs additional linting tools for Makefile and SQL validation:
- checkmake: Makefile linter
- sqlfluff: SQL linter and formatter
"""

set -euo pipefail

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Installing Enhanced Quality Pipeline Tools...${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install tool with multiple methods
install_tool() {
    local tool=$1
    local desc=$2
    local pip_name=$3
    local brew_name=$4
    
    echo -e "${YELLOW}Installing ${tool} (${desc})...${NC}"
    
    if command_exists "$tool"; then
        echo -e "${GREEN}✓ ${tool} already installed${NC}"
        return 0
    fi
    
    # Try pip first
    if command_exists pip; then
        echo "Attempting pip install..."
        if pip install "$pip_name"; then
            echo -e "${GREEN}✓ ${tool} installed via pip${NC}"
            return 0
        fi
    fi
    
    # Try homebrew on macOS
    if [[ "$OSTYPE" == "darwin"* ]] && command_exists brew; then
        echo "Attempting homebrew install..."
        if brew install "$brew_name"; then
            echo -e "${GREEN}✓ ${tool} installed via homebrew${NC}"
            return 0
        fi
    fi
    
    echo -e "${RED}❌ Failed to install ${tool}${NC}"
    echo -e "${YELLOW}Manual installation required:${NC}"
    echo "  - pip install ${pip_name}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  - brew install ${brew_name}"
    fi
    return 1
}

# Install checkmake for Makefile linting
install_tool "checkmake" "Makefile linter" "checkmake" "checkmake"

echo ""

# Install sqlfluff for SQL linting
install_tool "sqlfluff" "SQL linter and formatter" "sqlfluff" "sqlfluff"

echo ""
echo -e "${GREEN}Enhanced Quality Pipeline Installation Complete!${NC}"
echo ""
echo -e "${YELLOW}Available new quality checks:${NC}"
echo "  make lint-makefile  - Lint Makefile structure and syntax"
echo "  make lint-sql       - Lint SQL files for quality and standards"
echo "  make quality        - Run full enhanced quality pipeline"
echo ""
echo -e "${YELLOW}VS Code Extensions for enhanced development:${NC}"
echo "  - ms-vscode.makefile-tools (Makefile support)"
echo "  - mtxr.sqltools (SQL database management)"
echo "  - inferrinizzard.prettier-sql-vscode (SQL formatting)"
echo ""
echo -e "${BLUE}Quality pipeline now includes:${NC}"
echo "  1. Makefile linting and validation"
echo "  2. SQL quality checks and standards"
echo "  3. Python formatting (Black)"
echo "  4. Import sorting (isort)"
echo "  5. Code quality (Pylint)"
echo "  6. Type checking (MyPy)"
echo "  7. Test suite with coverage"
