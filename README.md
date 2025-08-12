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

## Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Install based on your needs:
make install       # Production pipeline only
make install-test  # Production + testing tools
make install-dev   # Full development environment
```

### 2. Database Initialization
```bash
# Initialize with last 30 trading days of data
make init-db
```

### 3. Running the Application
```bash
# Daily data collection
make run

# Start services
make airflow  # Apache Airflow (prints connection details)
make serve    # FastAPI endpoints (prints available URLs)
```

### 4. Development Commands
```bash
make test      # Run test suite
make lint      # Code quality checks
make lint-fix  # Auto-fix issues
```

## API Endpoints

When running `make serve`, the following endpoints become available:

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Top Performers**: http://localhost:8000/api/stocks/top-performers
- **Performance Details**: http://localhost:8000/api/stocks/performance-details

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
- SQLAlchemy >= 2.0.0 (Database ORM)
- Apache Airflow >= 2.7.0 (Workflow orchestration)

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

---

**Ready for production deployment with comprehensive tooling and quality standards!**
