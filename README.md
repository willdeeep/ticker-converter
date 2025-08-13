# Financial Market Data Analytics Pipeline

A modern Python-based stock ticker conversion and analysis pipeline with Makefile-driven workflow, featuring FastAPI endpoints, PostgreSQL integration, and comprehensive code quality tools.

## Overview

This project implements a production-ready financial data analytics pipeline designed for professional development workflows. It combines SQL-first architecture with modern Python tooling to deliver reliable stock performance analysis.

### Key Features

- **Makefile-Based Workflow**: Simplified operations with intuitive `make` commands
- **FastAPI Integration**: REST API endpoints for stock performance analysis  
- **PostgreSQL Backend**: Robust data persistence with optimized SQL queries
- **Code Quality Tools**: Automated formatting, linting, and type checking
- **Comprehensive Testing**: Full test coverage with pytest and coverage reporting
- **Development Environment**: Pre-commit hooks and automated quality gates

## What's New in v1.1.0

### Major Improvements
- **🚀 Upgraded to Apache Airflow 3.0.4**: Latest workflow orchestration with modern @dag and @task decorators
- **🐍 Standardized on Python 3.11.12**: Single Python version for optimal compatibility and performance
- **🧪 Enhanced Test Coverage**: Improved from 38% to 44% with comprehensive unit tests
- **⚡ Improved CI/CD Pipeline**: Faster, more reliable automated testing and deployment
- **🔧 Better Type Safety**: Full mypy compliance with proper type annotations
- **📚 Enhanced Documentation**: Clear setup instructions and troubleshooting guides

### Breaking Changes
- **Python Version**: Now requires exactly Python 3.11.12 (previously supported 3.9+)
- **Airflow Syntax**: Updated to Airflow 3.0 decorator patterns (legacy syntax removed)
- **Dependencies**: Removed SQLAlchemy (not needed for direct SQL approach)

## Quick Start

### Requirements

**Python Version**: This project is built specifically for Python 3.11.12 and requires exactly this version for optimal compatibility with all dependencies and type annotations.

```bash
python --version  # Should output: Python 3.11.12
```

**System Requirements**:
- PostgreSQL (for database backend)
- Git (for version control)
- Make (for automation commands)

### Step-by-Step Setup

Follow these commands in order to set up the project:

#### 1. Clone and Enter Repository
```bash
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter
```

#### 2. Set Up Environment Variables
```bash
make setup
# This creates .env file with default values
# Edit .env file to add your Alpha Vantage API key:
# ALPHA_VANTAGE_API_KEY=your_api_key_here
```

#### 3. Install Dependencies
Choose the installation type based on your needs:

```bash
# For production use only:
make install

# For development with testing tools:
make install-dev

# For testing only:
make install-test
```

#### 4. Initialize Database
```bash
make init-db
# This sets up PostgreSQL with sample data (last 30 trading days)
```

#### 5. Start Services
```bash
# Start Apache Airflow for workflow orchestration:
make airflow
# Note: Airflow web UI will be available at http://localhost:8080

# In a separate terminal, start the FastAPI server:
make serve
# Note: API endpoints will be available at http://localhost:8000
```

### Daily Operations

#### Running Data Collection
```bash
make run  # Executes daily ETL pipeline
```

#### Testing and Quality Assurance
```bash
make test      # Run test suite with coverage
make lint      # Check code quality
make lint-fix  # Auto-fix formatting issues
make act-pr    # Test GitHub Actions locally
```

#### Maintenance
```bash
make clean           # Clean build artifacts
make airflow-close   # Stop Airflow services
make db-close        # Stop PostgreSQL
```

### Complete Teardown
```bash
make teardown-airflow  # Remove all Airflow data
make teardown-db       # Remove PostgreSQL database
make teardown-env      # Remove virtual environment
```

## API Endpoints

When running `make serve`, the following endpoints become available:

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Top Performers**: http://localhost:8000/api/stocks/top-performers
- **Performance Details**: http://localhost:8000/api/stocks/performance-details

## Troubleshooting

### Common Issues and Solutions

#### Python Version Mismatch
```bash
# Verify you have Python 3.11.12
python --version

# If not, install via pyenv (recommended):
pyenv install 3.11.12
pyenv local 3.11.12
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
make db-close  # Stop any existing instances
make init-db   # Reinitialize database
```

#### Airflow Issues
```bash
# Reset Airflow if needed
make teardown-airflow
make airflow
```

#### Import/Module Errors
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
make install-dev
```

#### API Key Issues
```bash
# Verify your .env file has the API key
cat .env | grep ALPHA_VANTAGE_API_KEY

# Get a free API key at: https://www.alphavantage.co/support/#api-key
```

### Getting Help
```bash
make help  # Show all available commands with descriptions
```

## Makefile Commands

### Installation Commands
- `make install` - Install production dependencies only
- `make install-test` - Install production + testing dependencies  
- `make install-dev` - Install full development environment

### Operational Commands
- `make init-db` - Initialize database with last 30 trading days of data
- `make run` - Run daily data collection for previous trading day
- `make airflow` - Start Apache Airflow instance with default user
- `make serve` - Start FastAPI development server

### Quality & Testing Commands
- `make test` - Run test suite with coverage
- `make lint` - Run all code quality checks
- `make lint-fix` - Auto-fix code quality issues
- `make clean` - Clean build artifacts and cache files

### Airflow Access
After running `make airflow`, access the web interface at:
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin123

## Development Environment

### Code Quality Standards
The project maintains strict code quality with:
- **pylint**: 10/10 scores across all modules
- **black**: Consistent code formatting (88-character line length)
- **isort**: Organized import statements
- **mypy**: Static type checking
- **pre-commit**: Automated quality gates

### Project Structure
```
├── src/ticker_converter/     # Core Python package
├── api/                      # FastAPI application
├── sql/queries/              # SQL query files
├── tests/                    # Test suite
├── dags/                     # Apache Airflow DAGs
├── scripts/                  # Utility scripts
└── docs/                     # Documentation
```

### Testing Strategy
Run comprehensive tests with coverage reporting:
```bash
make test  # Runs pytest with coverage
```

Coverage reports are generated in `htmlcov/` for detailed analysis.

## Installation Options

### Production Environment
```bash
make install  # Core dependencies only
```

### Testing Environment  
```bash
make install-test  # Includes pytest, coverage tools
```

### Development Environment
```bash
make install-dev  # Full toolchain with quality tools
```

## Dependencies

### Core Dependencies
- FastAPI >= 0.104.0 (Web framework)
- uvicorn >= 0.24.0 (ASGI server)
- psycopg2-binary >= 2.9.7 (PostgreSQL adapter)
- pandas >= 2.1.0 (Data processing)
- Apache Airflow >= 3.0.4 (Workflow orchestration)

### Development Tools
- pylint >= 3.0.0 (Code analysis)
- black >= 23.0.0 (Code formatting)
- isort >= 5.12.0 (Import sorting)
- mypy >= 1.5.0 (Type checking)
- pre-commit >= 3.4.0 (Git hooks)

## Code Quality

The project enforces high code quality standards:

### Automated Formatting
```bash
make lint-fix  # Apply black + isort formatting
```

### Quality Checks
```bash
make lint  # Run pylint, black, isort, mypy
```

### Pre-commit Hooks
Installed automatically with `make install-dev`:
- Trailing whitespace removal
- YAML syntax checking
- Code formatting with black
- Import sorting with isort
- Linting with pylint

## Architecture

### SQL-First Design
- Custom SQL queries optimized for financial data analysis
- PostgreSQL-only architecture for data persistence
- Async database connections for optimal performance

### API Design
- RESTful endpoints with automatic OpenAPI documentation
- Pydantic models for type-safe request/response handling
- Comprehensive error handling with detailed HTTP responses

### Data Pipeline
- Apache Airflow orchestration for reliable data workflows
- Alpha Vantage API integration for market data
- Magnificent Seven stock focus (AAPL, MSFT, GOOGL, etc.)

## Production Deployment

### Environment Variables
Set up your `.env` file:
```bash
ALPHA_VANTAGE_API_KEY=your_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/ticker_converter
```

### Database Setup
The `make init-db` command handles:
- Schema creation
- Historical data population
- Index optimization
- View generation

### Service Management
- **FastAPI**: `make serve` starts development server
- **Airflow**: `make airflow` starts full Airflow stack
- **Database**: PostgreSQL connection handling built-in

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Install development environment (`make install-dev`)
4. Make changes with quality checks (`make lint-fix`)
5. Run tests (`make test`)
6. Commit changes (pre-commit hooks apply automatically)
7. Push and create Pull Request

### Quality Standards
All contributions must:
- Pass `make lint` with 10/10 pylint scores
- Include tests with `make test` passing
- Follow black formatting standards
- Include type hints for mypy

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/willdeeep/ticker-converter/issues)
- **API Docs**: http://localhost:8000/docs (when running `make serve`)

## Further Reading

Explore detailed documentation in the `docs/` folder:

### Architecture Documentation
- [System Overview](docs/architecture/overview.md) - High-level system design and component interactions
- [Database Design](docs/architecture/database_design.md) - SQL schema, relationships, and optimization strategies
- [API Design](docs/architecture/api_design.md) - FastAPI endpoint specifications and design patterns
- [Airflow Setup](docs/architecture/airflow_setup.md) - Workflow orchestration configuration and DAG design

### Deployment Guides
- [Local Setup](docs/deployment/local_setup.md) - Detailed local development environment setup
- [Production Deployment](docs/deployment/production.md) - Production deployment strategies and best practices

### User Guides
- [CLI Usage](docs/user_guides/cli_usage.md) - Command-line interface documentation and examples

---

**Ready for production deployment with comprehensive tooling and quality standards!**
