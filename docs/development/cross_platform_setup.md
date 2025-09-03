# Cross-Platform Development Setup Guide

This guide provides platform-specific instructions for setting up the ticker-converter development environment across macOS, Linux, and Windows systems.

## Overview

The ticker-converter project is designed to work seamlessly across major development platforms. Our Makefile-driven workflow automatically detects your operating system and adapts commands accordingly.

### Supported Platforms

| Platform | Status | Package Manager | Python Management |
|----------|---------|-----------------|-------------------|
| **macOS** | ✅ Primary | Homebrew | pyenv |
| **Linux (Ubuntu/Debian)** | ✅ Secondary | apt | pyenv/system |
| **Linux (RHEL/CentOS)** | ⚠️  Community | yum/dnf | pyenv/system |
| **Windows 11** | 🚧 Planned | Chocolatey | python.org |
| **Windows (WSL2)** | 🚧 Planned | apt | pyenv |

---

## macOS Setup

### Prerequisites

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install pyenv for Python management**:
   ```bash
   brew install pyenv
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
   echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
   echo 'eval "$(pyenv init -)"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **Install PostgreSQL**:
   ```bash
   brew install postgresql@15
   brew services start postgresql@15
   ```

### Development Setup

1. **Clone and setup the project**:
   ```bash
   git clone https://github.com/willdeeep/ticker-converter.git
   cd ticker-converter
   make setup
   ```

2. **Install development dependencies**:
   ```bash
   make install-test
   ```

3. **Initialize the database**:
   ```bash
   make init-db
   ```

4. **Verify installation**:
   ```bash
   make quality
   ```

### macOS-Specific Notes

- **Apple Silicon**: The project works on both Intel and Apple Silicon Macs
- **Xcode Command Line Tools**: Required for compiling some Python packages
- **Homebrew Services**: Used for managing PostgreSQL and other services

---

## Linux Setup (Ubuntu/Debian)

### Prerequisites

1. **Update package manager**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install development essentials**:
   ```bash
   sudo apt install -y build-essential curl git
   ```

3. **Install pyenv**:
   ```bash
   curl https://pyenv.run | bash
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
   echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
   echo 'eval "$(pyenv init -)"' >> ~/.bashrc
   source ~/.bashrc
   ```

4. **Install PostgreSQL**:
   ```bash
   sudo apt install -y postgresql postgresql-contrib
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

### Development Setup

1. **Clone and setup the project**:
   ```bash
   git clone https://github.com/willdeeep/ticker-converter.git
   cd ticker-converter
   make setup
   ```

2. **Install development dependencies**:
   ```bash
   make install-test
   ```

3. **Initialize the database**:
   ```bash
   make init-db
   ```

4. **Verify installation**:
   ```bash
   make quality
   ```

### Linux-Specific Notes

- **systemctl**: Used for service management instead of brew services
- **apt**: Package management through apt instead of Homebrew
- **Python Dependencies**: May require additional development headers

---

## Windows Setup (Planned)

> **Note**: Windows support is planned for the Makefile modernization project (Issue #62). Currently, we recommend using WSL2 for Windows development.

### WSL2 Setup (Interim Solution)

1. **Install WSL2**:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

2. **Follow Linux setup instructions** within WSL2 environment

### Native Windows Support (Coming Soon)

The upcoming Makefile modernization will include:
- **Chocolatey** package manager integration
- **PowerShell** and **Command Prompt** compatibility
- **Windows Services** management for PostgreSQL
- **Native Python** installation support

---

## Cross-Platform Features

### Automatic Platform Detection

Our Makefile automatically detects your platform and adapts commands:

```bash
# Works on all platforms
make setup        # Detects OS and uses appropriate package manager
make install-test # Installs using platform-specific tools
make quality      # Runs cross-platform quality checks
```

### Graceful Tool Detection

The system gracefully handles missing optional tools:

- **checkmake**: Makefile linting (optional, installs via package manager)
- **sqlfluff**: SQL linting (installs via pip)
- **Docker**: For containerized testing (optional)

### Environment Variable Handling

Cross-platform environment variable management:

```bash
# Works across shell environments
source .env       # Unix-like systems
# set commands     # Windows (planned)
```

---

## Troubleshooting

### Common Issues

#### Python Version Issues

**Problem**: Python 3.11.12 not available
```bash
# macOS
brew install pyenv
pyenv install 3.11.12

# Linux
curl https://pyenv.run | bash
pyenv install 3.11.12
```

#### PostgreSQL Connection Issues

**Problem**: Database connection failed
```bash
# Check service status
# macOS
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql
```

#### Permission Issues

**Problem**: Permission denied errors
```bash
# Ensure proper ownership
chown -R $USER:$USER ~/.pyenv
chown -R $USER:$USER .venv/
```

### Platform-Specific Debugging

#### macOS Debugging
```bash
# Check Homebrew installation
brew doctor

# Check pyenv configuration
pyenv doctor

# Check PostgreSQL status
brew services list
```

#### Linux Debugging
```bash
# Check package installation
dpkg -l | grep postgresql

# Check service status
systemctl status postgresql

# Check Python build dependencies
sudo apt install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
```

---

## Performance Optimization

### Platform-Specific Tips

#### macOS
- **Apple Silicon**: Use native ARM builds when available
- **Homebrew**: Regular cleanup with `brew cleanup`
- **Xcode**: Keep Command Line Tools updated

#### Linux
- **Package Cache**: Regular cleanup with `sudo apt autoremove`
- **Build Tools**: Ensure latest gcc/clang for optimal compilation
- **Memory**: Consider swap configuration for large builds

---

## IDE Integration

### VS Code Configuration

Cross-platform VS Code settings for optimal development experience:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "files.associations": {
        "Makefile.*": "makefile"
    },
    "terminal.integrated.env.osx": {
        "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}"
    },
    "terminal.integrated.env.linux": {
        "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}"
    }
}
```

### Task Integration

Platform-aware VS Code tasks:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Quality Check",
            "type": "shell",
            "command": "make",
            "args": ["quality"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

---

## Migration Guide

### From Single Platform to Cross-Platform

If you're currently using the project on a single platform and want to enable cross-platform development:

1. **Update local repository**:
   ```bash
   git pull origin main
   ```

2. **Verify cross-platform features**:
   ```bash
   make help  # Should show platform-aware help
   ```

3. **Test on secondary platform**:
   ```bash
   make setup && make install-test && make quality
   ```

### Team Onboarding

For teams working across different platforms:

1. **Standardize on project structure** (already cross-platform)
2. **Document platform-specific requirements** in team wiki
3. **Use consistent environment variables** across platforms
4. **Validate cross-platform CI/CD** with GitHub Actions

---

## Future Enhancements

### Planned Improvements (Issue #62)

1. **Enhanced Windows Support**: Native PowerShell and cmd compatibility
2. **Container Integration**: Docker-based development environments
3. **Cloud Development**: GitHub Codespaces and GitPod support
4. **Improved Tool Detection**: Better fallback mechanisms and error messages

### Community Contributions

We welcome contributions for additional platform support:

- **FreeBSD/OpenBSD**: Unix-like system support
- **Alpine Linux**: Lightweight container environments
- **ARM Linux**: Raspberry Pi and ARM server support

---

## Support

### Getting Help

1. **Check platform-specific troubleshooting** above
2. **Review existing issues**: [GitHub Issues](https://github.com/willdeeep/ticker-converter/issues)
3. **Create new issue**: Include platform details and error logs
4. **Community discussion**: Platform-specific setup help

### Reporting Platform Issues

When reporting platform-specific issues, include:

```bash
# System information
uname -a                    # Platform details
python --version           # Python version
make --version             # Make version
# Package manager info (brew --version, apt --version, etc.)
```

---

## Contributing

### Cross-Platform Testing

When contributing changes that might affect cross-platform compatibility:

1. **Test on multiple platforms** (or document platform limitations)
2. **Update platform-specific documentation** as needed
3. **Consider graceful degradation** for platform-specific features
4. **Validate CI/CD** across different GitHub Actions runners

### Platform Support Contributions

To add support for a new platform:

1. **Follow existing patterns** in Makefile structure
2. **Add platform detection** logic
3. **Implement package manager** integration
4. **Update documentation** with setup instructions
5. **Add CI/CD testing** for new platform
