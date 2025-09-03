# Cross-Platform Development Guide

## Overview

This guide covers development setup and workflows for the Ticker Converter project across different operating systems using our modular Makefile system.

## Supported Platforms

| Platform | Architecture | Status | Package Manager |
|----------|-------------|--------|-----------------|
| macOS | Intel (x86_64) | ✅ Supported | Homebrew |
| macOS | Apple Silicon (arm64) | ✅ Supported | Homebrew |
| Linux | x86_64 (Ubuntu/Debian) | ✅ Supported | APT |
| Linux | x86_64 (RHEL/CentOS) | 🟡 Community | YUM/DNF |
| Windows | x86_64 | ✅ Supported | Chocolatey |
| Windows | WSL2 | ✅ Supported | APT |

## Platform-Specific Setup

### macOS Development Setup

#### Prerequisites
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Automated Setup
```bash
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Our system automatically detects macOS and configures:
# - Homebrew package manager
# - pyenv for Python version management
# - PostgreSQL via brew services
# - All development dependencies
make setup
```

#### Manual Verification
```bash
make platform-info  # Verify detection
make platform-debug # Detailed tool availability
```

### Linux Development Setup (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential curl git wget
```

#### Automated Setup
```bash
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Our system automatically detects Linux and configures:
# - APT package manager
# - System Python or pyenv
# - PostgreSQL via systemctl
# - All development dependencies
make setup
```

#### Manual Package Installation (if needed)
```bash
# The system handles this automatically, but for reference:
sudo apt install -y python3.11 python3.11-venv postgresql postgresql-contrib
```

### Windows Development Setup

#### Option 1: Native Windows
```powershell
# Install Chocolatey (Run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Clone and setup
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Our system automatically detects Windows and configures:
# - Chocolatey package manager
# - Python 3.11 installation
# - PostgreSQL Windows service
# - All development dependencies
make setup
```

#### Option 2: WSL2 (Recommended)
```bash
# In WSL2 Ubuntu environment
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Follows Linux setup path automatically
make setup
```

## Development Workflows

### Getting Started
```bash
# 1. Verify platform detection
make platform-info

# 2. Check tool availability
make platform-debug

# 3. Complete setup
make setup

# 4. Install development dependencies
make install-dev

# 5. Verify installation
make validate-install
```

### Daily Development
```bash
# Start development session
make dev-ready  # Validates environment and runs fast tests

# Development cycle
make test-watch  # Continuous testing during development
make quality     # Code quality checks
make test-coverage  # Full test suite with coverage

# Service management
make db-start    # Start PostgreSQL
make airflow-start  # Start Airflow orchestration
```

### Testing Across Platforms
```bash
# Quick tests (fast feedback)
make test-fast

# Comprehensive testing
make test-unit
make test-integration
make test-coverage

# Performance testing
make test-benchmark
make test-profile
```

### Code Quality
```bash
# Format and lint
make quality  # Complete quality pipeline

# Individual tools
make lint-black    # Code formatting
make lint-isort    # Import organization
make lint-pylint   # Static analysis (maintains 10.00/10)
make lint-mypy     # Type checking
make security-scan # Security vulnerability check
```

## Platform-Specific Notes

### macOS Considerations
- **Apple Silicon**: Full native support with arm64 detection
- **PostgreSQL**: Managed via `brew services start postgresql@15`
- **Python**: Managed via pyenv for version consistency
- **Permissions**: Standard user permissions sufficient

### Linux Considerations
- **Service Management**: Uses systemctl for PostgreSQL
- **Package Manager**: Automatic detection of APT/YUM/DNF
- **Python**: Prefers system Python 3.11, falls back to pyenv
- **Permissions**: May require sudo for system package installation

### Windows Considerations
- **Package Manager**: Chocolatey for system dependencies
- **Services**: Windows Service Manager for PostgreSQL
- **Path Handling**: Automatic Windows path separator handling
- **Python**: Direct installation or Windows Store version

## Troubleshooting

### Common Issues

#### Platform Detection Problems
```bash
# Force platform detection refresh
make platform-debug

# Check specific tool availability
make check-tools

# Validate installation
make validate-install
```

#### Permission Issues
```bash
# macOS: Ensure Homebrew ownership
sudo chown -R $(whoami) /opt/homebrew

# Linux: Check sudo access for system packages
sudo -v

# Windows: Run PowerShell as Administrator for Chocolatey
```

#### Python Version Issues
```bash
# Check Python version
make validate-python

# Install specific Python version
make install-python-311

# Rebuild virtual environment
make clean-env
make setup-env
```

#### PostgreSQL Connection Issues
```bash
# Check PostgreSQL status
make db-status

# Restart PostgreSQL
make db-restart

# Reset database
make db-reset  # Caution: destroys data
```

### Platform-Specific Troubleshooting

#### macOS Issues
```bash
# Homebrew permission issues
make doctor-macos

# Xcode tools missing
xcode-select --install

# PostgreSQL connection issues
brew services restart postgresql@15
```

#### Linux Issues
```bash
# Package manager issues
make doctor-linux

# PostgreSQL issues
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Python development headers
sudo apt install -y python3.11-dev
```

#### Windows Issues
```bash
# Chocolatey issues
make doctor-windows

# PostgreSQL service issues
net start postgresql-x64-15

# Python PATH issues
make validate-python-path
```

## Advanced Configuration

### Environment Customization
```bash
# Custom Python version
echo "PYTHON_VERSION=3.11.12" >> .env

# Custom PostgreSQL settings
echo "POSTGRES_VERSION=15" >> .env

# Platform-specific overrides
echo "PACKAGE_MANAGER=custom" >> .env
```

### Tool Installation Options
```bash
# System-wide installation
make install-system-deps

# User-space installation
make install-user-deps

# Development environment only
make install-dev-deps
```

### Performance Optimization
```bash
# Enable parallel testing
make test-parallel

# Use faster linting
make lint-fast

# Skip optional tools
export SKIP_OPTIONAL_TOOLS=true
make setup
```

## Integration with IDEs

### VS Code
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

### PyCharm
- Set Python interpreter to `.venv/bin/python`
- Configure code style to use Black formatting
- Enable Pylint integration

### Vim/Neovim
```vim
" Use project virtual environment
let g:python3_host_prog = expand('.venv/bin/python')
```

## Contributing

### Platform Testing
Before submitting changes that affect the build system:

1. Test on your primary platform
2. Use GitHub Actions for cross-platform testing
3. Update platform-specific documentation as needed

### Adding New Platform Support
1. Update `make/Makefile.platform` with detection logic
2. Add platform-specific installation commands
3. Update this guide with new platform instructions
4. Test thoroughly on target platform

## Resources

- [Makefile Modernization Roadmap](../my_docs/MAKEFILE_MODERNIZATION_ROADMAP.md)
- [GitHub Copilot Instructions](../.github/copilot-instructions.md)
- [Architecture Documentation](./architecture/)
- [Deployment Guide](./deployment/)
