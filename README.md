````markdown
# Stock Market Currency Converter

A comprehensive financial data pipeline that fetches real-time stock prices and currency exchange rates, providing USD-denominated stock performance data converted to GBP for UK-based investors and analysts.

## Overview

This application integrates with the Alpha Vantage API to collect both equity market data and foreign exchange rates, combining them to deliver actionable insights for international investment analysis. The system fetches stock prices and trading volumes for major US equities, retrieves USD/GBP exchange rates, and calculates equivalent values in British Pounds.

### Core Functionality

The application connects to Alpha Vantage's comprehensive financial data API to:

- **Stock Data Collection**: Retrieves daily stock prices, trading volumes, and performance metrics for major US equities including the "Magnificent Seven" technology stocks (Apple, Microsoft, Google, Amazon, Tesla, Meta, and Nvidia)
- **Currency Exchange Integration**: Fetches real-time USD to GBP exchange rates to enable accurate currency conversion
- **Cross-Market Analysis**: Joins equity and forex data to provide British Pound equivalent values for US stock investments
- **Historical Data Management**: Maintains time-series data for trend analysis and performance tracking

### Technical Architecture

- **SQL-First Design**: Direct PostgreSQL integration with optimized queries for financial data analysis
- **RESTful API**: FastAPI-powered endpoints for programmatic data access and integration
- **Automated Workflows**: Apache Airflow orchestration for reliable daily data collection
- **Professional Tooling**: Comprehensive code quality standards with automated testing and CI/CD integration

## Quick Start with Act (Recommended)

The fastest way to get the application running is using [Act](https://github.com/nektos/act), which simulates GitHub Actions locally and handles all environment setup automatically.

### Prerequisites

Install Act on your system:

**macOS (using Homebrew):**
```bash
brew install act
```

**Other Systems:**
Visit the [Act installation guide](https://github.com/nektos/act#installation) for detailed instructions.

### Running the Application

1. **Clone the Repository**
   ```bash
   git clone https://github.com/willdeeep/ticker-converter.git
   cd ticker-converter
   ```

2. **Set Up API Access**
   
   Create a `.env` file in the project root:
   ```bash
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://user:pass@localhost:5432/ticker_converter
   ```
   
   Get your free Alpha Vantage API key at: https://www.alphavantage.co/support/#api-key

3. **Run Complete Setup**
   ```bash
   make act-pr
   ```
   
   This single command will:
   - Set up Python 3.11 environment
   - Install all dependencies
   - Run comprehensive tests
   - Validate code quality
   - Ensure everything works correctly

4. **Start the Services**
   
   After Act completes successfully:
   ```bash
   make install-dev    # Install development environment
   make init-db        # Initialize database with historical data
   make serve          # Start FastAPI server
   ```

## Alternative Setup (Manual Installation)

If Act is not available or you prefer manual setup, follow these steps:

### System Requirements

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Git

### Manual Installation Steps

1. **Clone and Setup Virtual Environment**
   ```bash
   git clone https://github.com/willdeeep/ticker-converter.git
   cd ticker-converter
   
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**
   
   Choose based on your needs:
   ```bash
   pip install -e .                # Production only
   pip install -e ".[test]"        # Production + testing
   pip install -e ".[dev]"         # Full development environment
   ```

3. **Configure Environment**
   
   Create `.env` file with your settings:
   ```bash
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/ticker_converter
   ```

4. **Initialize Database**
   ```bash
   # Ensure PostgreSQL is running
   python -m ticker_converter.cli_ingestion --init --days=30
   ```

5. **Run Tests**
   ```bash
   pytest tests/ --cov=src/ticker_converter --cov-report=html
   ```

6. **Start Services**
   ```bash
   # Start API server
   python run_api.py
   
   # In another terminal, start Airflow (optional)
   airflow webserver --port 8080
   ```

## API Endpoints

Once the FastAPI server is running (via `make serve` or `python run_api.py`), access these endpoints:

- **Health Check**: http://localhost:8000/health
- **Interactive Documentation**: http://localhost:8000/docs
- **Top Performing Stocks**: http://localhost:8000/api/stocks/top-performers
- **Detailed Performance Metrics**: http://localhost:8000/api/stocks/performance-details

All endpoints return JSON data with stock prices converted to GBP using current exchange rates.

## Troubleshooting

### Act Issues

If `make act-pr` fails:

1. **Docker Not Running**: Ensure Docker Desktop is running
   ```bash
   docker --version  # Should return version info
   ```

2. **Apple Silicon Compatibility**: The Makefile automatically detects M1/M2 Macs and uses compatible containers

3. **Insufficient Resources**: Act requires significant memory. Increase Docker memory allocation to 4GB or more

4. **Network Issues**: Act downloads container images. Ensure stable internet connection

### Manual Setup Issues

1. **Python Version**: Verify Python 3.9+ is installed
   ```bash
   python --version
   ```

2. **PostgreSQL Connection**: Test database connectivity
   ```bash
   psql postgresql://username:password@localhost:5432/ticker_converter
   ```

3. **API Key Validation**: Test your Alpha Vantage key
   ```bash
   curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=YOUR_KEY"
   ```

4. **Port Conflicts**: If port 8000 is in use, modify `run_api.py` or kill existing processes
   ```bash
   lsof -ti:8000  # Find process using port 8000
   ```

## Development Commands

For ongoing development work, these Make commands provide streamlined workflows:

### Core Operations
- `make install` - Install production dependencies only
- `make install-test` - Install production + testing dependencies
- `make install-dev` - Install full development environment with quality tools
- `make init-db` - Initialize database with 30 days of historical data
- `make run` - Execute daily data collection for the previous trading day

### Service Management
- `make serve` - Start FastAPI development server on http://localhost:8000
- `make airflow` - Start Apache Airflow instance (access at http://localhost:8080)

### Code Quality
- `make test` - Run comprehensive test suite with coverage reporting
- `make lint` - Execute all code quality checks (pylint, black, isort, mypy)
- `make lint-fix` - Automatically fix formatting issues
- `make lint-dags` - Run specific linting checks for Airflow DAGs
- `make clean` - Remove build artifacts and cache files

### CI/CD Testing
- `make act-pr` - Simulate GitHub Actions CI pipeline locally using Act

## Architecture Overview

### Data Flow
1. **Daily Collection**: Airflow orchestrates data fetching from Alpha Vantage API
2. **Currency Conversion**: USD stock prices are converted to GBP using current exchange rates
3. **Storage**: Time-series data stored in PostgreSQL with optimized indexing
4. **API Access**: FastAPI provides RESTful endpoints for data consumption

### Technology Stack
- **Python 3.9+**: Core application runtime
- **PostgreSQL**: Primary data storage with optimized financial data schemas
- **FastAPI**: Modern web framework for API development
- **Apache Airflow**: Workflow orchestration and scheduling
- **Alpha Vantage API**: External data source for market and forex data
- **pytest**: Comprehensive testing framework
- **Docker/Act**: Containerized CI/CD simulation

### Project Structure
```
ticker-converter/
├── src/ticker_converter/          # Core Python package
│   ├── api_clients/               # Alpha Vantage API integration
│   ├── data_ingestion/            # Data collection and processing
│   ├── data_models/               # Pydantic data models
│   └── database/                  # PostgreSQL connection management
├── api/                           # FastAPI application
├── dags/                          # Apache Airflow DAGs
├── sql/queries/                   # Optimized SQL queries
├── tests/                         # Comprehensive test suite
├── scripts/                       # Utility and testing scripts
└── docs/                          # Project documentation
```

## Dependencies

### Core Runtime Dependencies
- **requests >= 2.31.0**: HTTP client for API integration
- **psycopg2-binary >= 2.9.7**: PostgreSQL database adapter
- **pandas >= 2.1.0**: Data manipulation and analysis
- **python-dotenv >= 1.0.0**: Environment variable management
- **apache-airflow >= 3.0.0**: Workflow orchestration platform

### Optional Dependencies (API)
- **fastapi >= 0.104.0**: Modern web framework
- **uvicorn >= 0.24.0**: ASGI server with performance optimizations
- **pydantic >= 2.4.0**: Data validation and serialization
- **asyncpg >= 0.28.0**: Async PostgreSQL driver for API endpoints

### Development and Testing Tools
- **pytest >= 7.4.0**: Testing framework with fixtures and parametrization
- **pytest-cov >= 4.1.0**: Coverage reporting integration
- **pytest-asyncio >= 0.21.0**: Async test support
- **httpx**: HTTP client for API testing
- **responses**: HTTP request mocking for unit tests

### Code Quality Tools
- **pylint >= 3.0.0**: Comprehensive code analysis
- **black >= 23.0.0**: Opinionated code formatting
- **isort >= 5.12.0**: Import statement organization
- **mypy >= 1.5.0**: Static type checking
- **pre-commit >= 3.4.0**: Git hook automation

## Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/ticker-converter.git
   cd ticker-converter
   ```

2. **Setup Development Environment**
   ```bash
   make install-dev  # Install all development tools
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**
   - Follow the existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

5. **Quality Checks**
   ```bash
   make lint-fix     # Auto-fix formatting
   make lint         # Verify all quality checks pass
   make test         # Ensure all tests pass
   ```

6. **Test CI Pipeline**
   ```bash
   make act-pr       # Simulate GitHub Actions locally
   ```

7. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

### Code Standards

All contributions must meet these requirements:
- **Code Quality**: Pass all `make lint` checks with perfect scores
- **Test Coverage**: Include tests for new functionality
- **Type Safety**: Use type hints for all public APIs
- **Documentation**: Update docstrings and README as needed
- **Backwards Compatibility**: Avoid breaking existing APIs

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete terms.

## Support and Resources

- **Project Repository**: https://github.com/willdeeep/ticker-converter
- **Issue Tracker**: https://github.com/willdeeep/ticker-converter/issues
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Alpha Vantage API**: https://www.alphavantage.co/documentation/

For technical support or feature requests, please create an issue on GitHub with detailed information about your environment and specific requirements.
