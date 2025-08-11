# Final Project Structure - Simplified SQL-Centric ETL Pipeline

```
ticker-converter/
├── README.md                           # Updated project overview (simplified scope)
├── pyproject.toml                      # Dependencies & tool configuration
├── LICENSE                             # MIT license
├── Makefile                            # Build, test, quality commands + Act integration
├── pytest.ini                          # Pytest configuration
├── copilot-instructions.md             # AI development guidelines
├── .env                                # Environment variables (git-ignored)
├── .env.example                        # Environment template (Alpha Vantage API key)
├── .gitignore                          # Git ignore rules
│
├── .github/                            # GitHub Repository Configuration
│   ├── ISSUE_TEMPLATE/                 # Professional issue templates
│   │   ├── bug_report.md               # Bug report template
│   │   ├── feature_request.md          # Feature request template
│   │   ├── documentation.md            # Documentation improvement template
│   │   ├── testing.md                  # Testing enhancement template
│   │   └── config.yml                  # Issue template configuration
│   │
│   └── workflows/                      # GitHub Actions CI/CD (Future)
│       └── main.yml                    # Test, lint, build workflow
│
├── docs/                               # Project Documentation
│   ├── SIMPLIFICATION_STRATEGY.md      # Complexity reduction strategy
│   ├── QUICK_REFERENCE.md              # Developer quick reference
│   ├── SQL_SCHEMA.md                   # Database schema documentation
│   ├── API_ENDPOINTS.md                # FastAPI endpoint documentation
│   ├── DEPLOYMENT.md                   # Setup and deployment guide
│   ├── FINAL_PROJECT_STRUCTURE.md      # This file - complete project structure
│   ├── GIT_WORKFLOW.md                 # Git workflow and GitHub CLI guide
│   └── data_pipeline.md                # Legacy documentation (to be updated)
│
├── sql/                                # SQL Scripts & Database Operations
│   ├── ddl/                            # Data Definition Language (Schema Creation)
│   │   ├── 001_create_dimensions.sql   # Dimension tables (stocks, dates, currencies)
│   │   ├── 002_create_facts.sql        # Fact tables (prices, currency_rates)
│   │   ├── 003_create_views.sql        # Analytical views (performance, conversions)
│   │   └── 004_create_indexes.sql      # Performance indexes
│   │
│   ├── etl/                            # ETL Transform Operations (Called by Airflow)
│   │   ├── load_dimensions.sql         # Populate dim tables from raw data
│   │   ├── daily_transform.sql         # Currency conversion & performance calc
│   │   ├── data_quality_checks.sql     # Validation queries for pipeline
│   │   └── cleanup_old_data.sql        # Data retention management
│   │
│   └── queries/                        # API Query Templates (Called by FastAPI)
│       ├── top_performers.sql          # Top 5 stocks by daily return
│       ├── price_ranges.sql            # Stock filtering by price range
│       ├── currency_conversion.sql     # USD to GBP price conversion
│       └── stock_summary.sql           # Daily stock summary statistics
│
├── src/                                # Python Source Code (Simplified)
│   └── ticker_converter/
│       ├── __init__.py
│       │
│       ├── data_models/               # Pydantic Models (Simplified)
│       │   ├── __init__.py
│       │   ├── market_data.py         # MarketDataPoint, RawMarketData only
│       │   └── currency.py            # CurrencyRate model for USD/GBP
│       │
│       ├── etl/                       # ETL Functions (SQL-Focused)
│       │   ├── __init__.py
│       │   ├── extract_data.py        # Fetch NYSE stocks & currency rates
│       │   ├── transform_data.py      # Execute SQL transformation scripts
│       │   ├── load_to_db.py          # Load data using SQL INSERT operations
│       │   └── data_quality.py        # Basic validation & SQL quality checks
│       │
│       ├── database/                  # Database Operations
│       │   ├── __init__.py
│       │   ├── connection.py          # PostgreSQL connection management
│       │   ├── schema.py              # Schema creation & migration functions
│       │   └── queries.py             # SQL query execution utilities
│       │
│       └── api_clients/               # External API Integration (Existing)
│           ├── __init__.py
│           ├── alpha_vantage.py       # Stock data client (Issue #1 completed)
│           └── currency_api.py        # USD/GBP exchange rate client
│
├── api/                               # FastAPI Application
│   ├── __init__.py
│   ├── main.py                        # FastAPI app with SQL-powered endpoints
│   ├── models.py                      # Response models for API endpoints
│   ├── database.py                    # Database connection for API
│   └── dependencies.py                # FastAPI dependency injection
│
├── dags/                              # 🌊 Airflow DAGs (Only 2 DAGs)
│   ├── test_dag.py                    # Simple test DAG for Airflow validation
│   └── nyse_stock_etl.py              # Production ETL DAG (SQL operators)
│
├── tests/                             # Test Suite (Simplified)
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures & test configuration
│   │
│   ├── unit/                          # Unit Tests
│   │   ├── __init__.py
│   │   ├── test_data_models.py        # Test MarketDataPoint, CurrencyRate
│   │   ├── test_extract_data.py       # Test data extraction functions
│   │   ├── test_transform_data.py     # Test SQL transform execution
│   │   ├── test_load_to_db.py         # Test database loading functions
│   │   └── test_database.py           # Test database operations
│   │
│   ├── integration/                   # Integration Tests
│   │   ├── __init__.py
│   │   ├── test_sql_pipeline.py       # Test complete SQL ETL pipeline
│   │   ├── test_api_endpoints.py      # Test FastAPI SQL endpoints
│   │   └── test_airflow_dag.py        # Test DAG execution
│   │
│   └── fixtures/                      # Test Data
│       ├── sample_stock_data.json     # Sample NYSE stock data
│       ├── sample_currency_rates.json # Sample USD/GBP rates
│       └── test_database.sql          # PostgreSQL test database schema
│
├── scripts/                           # Utility Scripts
│   ├── setup_database.py              # Initialize database schema
│   ├── demo_simplified_pipeline.py    # Simplified pipeline demonstration
│   └── data_validation.py             # Manual data quality checks
│
└── .github/                           # GitHub Configuration
    └── workflows/
        └── ci.yml                     # GitHub Actions CI/CD pipeline
```

## **Key Folder Structure Decisions**

### **SQL Organization** (`sql/` directory):
- **`ddl/`**: Database schema creation (dimensions, facts, views, indexes)
- **`etl/`**: Transform operations called by Airflow SQL operators
- **`queries/`**: Query templates called by FastAPI endpoints

### **Simplified Python Code** (`src/ticker_converter/`):
- **`data_models/`**: Only essential Pydantic models (2 files)
- **`etl/`**: Core ETL functions that execute SQL scripts
- **`database/`**: Database connection and SQL execution utilities
- **`api_clients/`**: External API integration (leveraging Issue #1)

### **API Application** (`api/`):
- FastAPI application with direct SQL query execution
- Response models for JSON serialization
- Database connection management

### **Airflow DAGs** (`dags/`):
- **Only 2 DAGs**: test_dag.py & nyse_stock_etl.py
- Production DAG uses SQL operators exclusively

### **Simplified Tests** (`tests/`):
- **Unit tests**: Individual component testing
- **Integration tests**: SQL pipeline & API endpoint testing
- **Test fixtures**: Sample data for testing

## **Data Flow Architecture**

```
Alpha Vantage API → extract_data.py → Raw SQL Tables
                                         ↓
Currency API → extract_data.py → Raw SQL Tables
                                         ↓
                    transform_data.py → SQL ETL Scripts → Dimensional Tables
                                         ↓
                    FastAPI Endpoints → SQL Queries → JSON Responses
                                         ↓
                    Airflow DAG → SQL Operators → Scheduled ETL
```

## **Function Locations**

### **ETL Functions** (`src/ticker_converter/etl/`):
- `extract_data.fetch_nyse_stocks()` → Alpha Vantage → SQL INSERT
- `extract_data.fetch_currency_rates()` → Currency API → SQL INSERT  
- `transform_data.execute_daily_transform()` → Runs `sql/etl/daily_transform.sql`
- `load_to_db.bulk_insert_stocks()` → SQL INSERT operations
- `data_quality.run_quality_checks()` → Executes `sql/etl/data_quality_checks.sql`

### **SQL Functions**:
- **Schema Creation**: `sql/ddl/` scripts called by `database/schema.py`
- **ETL Transforms**: `sql/etl/` scripts called by Airflow SQL operators
- **API Queries**: `sql/queries/` templates called by FastAPI endpoints

### **Database Operations** (`src/ticker_converter/database/`):
- `connection.get_database_connection()` → PostgreSQL connection
- `schema.create_schema()` → Execute DDL scripts
- `queries.execute_sql_file()` → Run SQL scripts from files

This structure maintains the simplified scope while providing clear separation of concerns between Python orchestration and SQL data operations.
