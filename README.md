# Financial Market Data Analytics Pipeline

A Python-based ETL pipeline for financial market data analysis, built with Apache Airflow and designed to align with SCSK's Financial IT Business Segment requirements.

## Project Overview

This project implements a comprehensive financial data analytics pipeline that:

- **Ingests** real-time and historical market data from Alpha Vantage API
- **Transforms** data through cleaning, normalization, and feature engineering
- **Stores** processed data in PostgreSQL with optimized schemas
- **Orchestrates** workflows using Apache Airflow
- **Serves** data through a FastAPI backend with performance analytics

## Features

- 🔄 **ETL Pipeline**: Complete extract, transform, load workflows
- 📊 **Data Processing**: Moving averages, volatility calculations, and custom metrics
- 🗄️ **Database Integration**: PostgreSQL with SQLAlchemy ORM
- ⚡ **API Backend**: FastAPI with automatic documentation
- 🔧 **Workflow Orchestration**: Apache Airflow DAGs
- 🧪 **Testing**: Comprehensive test suite with pytest
- 📦 **Modern Python**: Type hints, black formatting, ruff linting

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install core dependencies
pip install -e .

# Or install with development tools
pip install -e ".[dev]"
```

### Basic Usage

```python
from ticker_converter import FinancialDataPipeline

# Initialize pipeline
pipeline = FinancialDataPipeline()

# Fetch market data
data = pipeline.fetch_stock_data("AAPL", period="1mo")

# Process and analyze
processed_data = pipeline.transform(data)
```

## Development

### Project Structure

```
├── src/
│   └── ticker_converter/
│       ├── etl_modules/     # ETL processing logic
│       ├── data_models/     # Pydantic models
│       └── utils/           # Utility functions
├── dags/                    # Airflow DAGs
├── sql/                     # Database schemas
├── tests/                   # Test suite
└── docs/                    # Documentation
```

### GitHub Issues & Roadmap

The project is organized into specific GitHub issues:

1. **Issue #1**: API Integration (Alpha Vantage)
2. **Issue #2**: Raw Data Storage (JSON/Parquet)
3. **Issue #3**: Data Transformation Pipeline
4. **Issue #4**: Database Schema & Storage
5. **Issue #5**: Airflow DAG Orchestration
6. **Issue #6**: FastAPI Backend (Bonus)
7. **Issue #7**: Testing Infrastructure
8. **Issue #8**: Documentation

### Optional Dependencies

Install additional features as needed:

```bash
# Database functionality
pip install -e ".[database]"

# Apache Airflow
pip install -e ".[airflow]"

# Data visualization
pip install -e ".[viz]"

# Cloud storage
pip install -e ".[cloud]"

# All features
pip install -e ".[all]"
```

### Code Quality

The project uses modern Python tooling:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/
```

## Relevance to SCSK

This project aligns with SCSK's Financial IT Business Segment, which provides:
- Systems development for financial institutions
- AML (Anti-Money Laundering) projects
- Securities industry development projects
- Wealth management solutions
- Digital transformation (DX) initiatives

The pipeline demonstrates advanced data engineering capabilities using modern Python and AI/ML technologies relevant to financial services.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/willdeeep/ticker-converter/issues)
- 💬 [Discussions](https://github.com/willdeeep/ticker-converter/discussions)
