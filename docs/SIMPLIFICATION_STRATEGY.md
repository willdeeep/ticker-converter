# Project Simplification Strategy - SQL-Centric ETL Pipeline

**Date**: August 11, 2025  
**Status**: Approved for Implementation  
**Priority**: HIGH - Required before proceeding with remaining features

## Problem Statement

The ticker-converter project had become overly complex with excessive feature engineering, quality validation, and ETL processing modules that exceeded the core requirements for a financial data pipeline demonstration.

**Original Scope Creep Issues**:
- Complex feature engineering with 30+ technical indicators
- Excessive quality validation with detailed reporting
- Multiple data serialization formats (pandas, bytes, JSON)
- Over-engineered ETL modules with complex class hierarchies
- Unnecessary abstractions that obscured core functionality

## Approved Simplification Strategy

### **Core Focus (Simplified Scope)**

**Data Sources**:
- **Magnificent Seven stocks**: AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA
- **Daily OHLCV data only** (no intraday complexity)
- **USD to GBP currency conversion only** (single currency pair)
- **Alpha Vantage API only** (leveraging completed Issue #1)

**Technical Approach**:
- **SQL-first pipeline**: All transformations done in SQL, not Python
- **Dimensional modeling**: Star schema with dim/fact tables
- **Direct SQL storage**: No intermediate Parquet/JSON files
- **Simple API endpoints**: Direct SQL query execution

### 📁 **Files Scheduled for DELETION - DETAILED LIST**

As documented in [Issue #12](https://github.com/willdeeep/ticker-converter/issues/12):

#### Complete File Removal:
```bash
# ETL Modules - Complex Python Processing
src/ticker_converter/etl_modules/feature_engineer.py        # 347 lines - Excessive feature engineering
src/ticker_converter/etl_modules/quality_validator.py       # 298 lines - Overly complex validation  

# Data Models - Complex Classes
src/ticker_converter/data_models/quality_metrics.py         # 156 lines - Unnecessary complexity

# Scripts - Demo/Example Code
scripts/demo_pipeline.py                                    # 423 lines - Demonstrates removed functionality

# Test Files - Tests for Deleted Features
tests/unit/etl_modules/test_quality_validator.py           # 267 lines - Tests for deleted features
tests/integration/test_data_pipeline.py                    # 345 lines - Complex integration tests
```

**Total File Removal**: 6 files, approximately 1,836 lines of code

#### Classes to Remove from `market_data.py`:
```python
# REMOVE: Volatility Classification (47 lines)
class VolatilityFlag(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

# REMOVE: Complex Data Cleaning (89 lines)
class CleanedMarketData(BaseModel):
    symbol: str
    date: datetime
    cleaned_prices: Dict[str, float]
    outliers_removed: int
    volatility_flag: VolatilityFlag

# REMOVE: Feature Engineering Results (134 lines)
class FeatureEngineeredData(BaseModel):
    symbol: str
    date: datetime
    moving_averages: Dict[str, float]
    technical_indicators: Dict[str, float]
    volatility_metrics: Dict[str, float]

# REMOVE: Validation Results (67 lines)
class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    quality_score: float
```

**Class Removal**: 4 classes, approximately 337 lines of code

#### Directories to Simplify:
```bash
# BEFORE: Complex structure
src/ticker_converter/etl_modules/
├── feature_engineer.py          # DELETE
├── quality_validator.py         # DELETE  
├── data_cleaner.py              # SIMPLIFY - keep basic validation only
└── utils.py                     # KEEP - utility functions

# AFTER: Simplified structure  
src/ticker_converter/etl_modules/
├── data_cleaner.py              # Simplified - basic validation only
└── utils.py                     # Utility functions only

# NEW: SQL-centric structure
sql/
├── ddl/                         # Data Definition Language
├── etl/                         # ETL SQL Scripts  
└── queries/                     # API Query Templates
```

#### Documentation to Remove/Update:
```bash
# Documentation cleanup
docs/feature_engineering.md                # DELETE - no longer applicable
docs/quality_metrics.md                   # DELETE - functionality removed
docs/complex_etl_guide.md                 # DELETE - replaced by SQL guide

# README.md - COMPLETE REWRITE required
# Current: 156 lines describing complex pipeline
# Target: ~80 lines describing simplified SQL approach
```

**Summary of Deletions**:
- **Total Files Removed**: 9 files (6 Python + 3 documentation)
- **Total Code Removed**: ~2,200+ lines
- **Complexity Reduction**: ~60% reduction in codebase size
- **Maintenance Burden**: Significantly reduced
class FeatureEngineeredData(BaseModel)    # Replace with SQL calculations
class ValidationResult(BaseModel)         # Simplify to basic validation
```

#### Files to Simplify:
```
src/ticker_converter/data_models/market_data.py  # Keep only MarketDataPoint, RawMarketData
src/ticker_converter/etl_modules/data_cleaner.py # Basic validation only
src/ticker_converter/core.py                     # Remove complex transform methods
```

### 🗄️ **New SQL-Centric Architecture**

#### Database Schema (Star Schema):
```sql
-- Dimension Tables
dim_stocks (stock_id, symbol, company_name, sector, exchange)
dim_dates (date_id, date, year, month, quarter, is_trading_day)  
dim_currencies (currency_id, code, name, country)

-- Fact Tables
fact_stock_prices (date_id, stock_id, open_usd, high_usd, low_usd, close_usd, volume)
fact_currency_rates (date_id, from_currency_id, to_currency_id, exchange_rate)
```

#### SQL Views for Analytics:
```sql
-- Performance calculations using SQL window functions
v_stock_performance   # Daily returns via LAG() functions
v_stocks_gbp         # Currency conversion via JOINs
v_top_performers     # Top 5 stocks ORDER BY daily_return DESC LIMIT 5
v_price_ranges       # Price filtering with parameterized WHERE clauses
```

### **Updated GitHub Issues**

#### Revised Issue Priorities:
1. **Issue #12**: URGENT - Reduce project complexity (MUST BE COMPLETED FIRST)
2. **Issue #3**: Simplify data models for SQL-first storage  
3. **Issue #4**: Design normalized SQL database schema (Star Schema)
4. **Issue #13**: Integrate NYSE stock data ingestion with SQL storage
5. **Issue #5**: Create Airflow DAG using SQL operators
6. **Issue #6**: Create FastAPI with SQL query endpoints  
7. **Issue #8**: Documentation for simplified SQL-centric pipeline

#### Key Changes Made to Issues:
- **Emphasis on SQL operators** in Airflow (not Python operators)
- **Direct SQL query execution** in FastAPI endpoints
- **Removal of complex feature engineering** requirements
- **Focus on dimensional modeling** instead of flat file processing
- **NYSE stocks only** (5-10 symbols maximum)

### **Implementation Strategy**

#### Phase 1: Complexity Reduction (Issue #12)
```bash
# Delete excessive modules
rm src/ticker_converter/etl_modules/feature_engineer.py
rm src/ticker_converter/etl_modules/quality_validator.py  
rm src/ticker_converter/data_models/quality_metrics.py
rm scripts/demo_pipeline.py
rm tests/unit/etl_modules/test_quality_validator.py
rm tests/integration/test_data_pipeline.py

# Simplify market_data.py (remove complex classes)
# Keep only: MarketDataPoint, RawMarketData
# Add: CurrencyRate model
```

#### Phase 2: SQL Schema Design (Issues #3, #4)
```sql
-- Create dimensional model
sql/ddl/001_create_dimensions.sql
sql/ddl/002_create_facts.sql
sql/ddl/003_create_views.sql  
sql/ddl/004_create_indexes.sql
```

#### Phase 3: Data Ingestion (Issue #13)
```python
# Simplified data fetchers
src/data_ingestion/nyse_fetcher.py      # Alpha Vantage → SQL INSERT
src/data_ingestion/currency_fetcher.py  # USD/GBP rates → SQL INSERT
```

#### Phase 4: Orchestration & API (Issues #5, #6)
```python
# Airflow with SQL operators
dags/nyse_stock_etl.py                  # SQLExecuteQueryOperator tasks

# FastAPI with direct SQL
api/main.py                            # Direct database query execution
api/queries.sql                        # SQL query templates
```

### **Expected Outcomes**

#### Quantitative Improvements:
- **50%+ reduction** in project file count
- **Simplified data models** (4 classes → 2 classes)
- **SQL-first approach** (all transformations via SQL)
- **Single data source** (NYSE stocks only)
- **Single currency pair** (USD/GBP only)

#### Qualitative Benefits:
- **Clearer separation of concerns**: API fetching vs SQL processing
- **Standard dimensional modeling**: Industry-standard star schema
- **Better performance**: SQL operations vs Python pandas
- **Easier maintenance**: SQL queries vs complex Python classes
- **Meets core requirements**: Focus on actual ETL pipeline needs

### **Migration Path**

#### Step 1: Backup Current State
```bash
git checkout -b backup/complex-implementation
git checkout feature/data-cleaning-pipeline-issue-3
```

#### Step 2: Execute Complexity Reduction (Issue #12)
- Delete specified files
- Simplify data models  
- Update imports and references
- Fix broken tests

#### Step 3: Implement SQL-Centric Design
- Create star schema
- Build SQL views
- Implement data ingestion
- Create Airflow DAG with SQL operators
- Build FastAPI with SQL endpoints

#### Step 4: Documentation and Testing
- Update README with simplified architecture
- Document SQL query examples
- Create integration tests for SQL pipeline
- Performance testing with SQL operations

### **Success Criteria**

#### Technical Validation:
- [ ] Project file count reduced by 50%+
- [ ] All transformations executed via SQL queries
- [ ] API endpoints return data via direct SQL execution
- [ ] Airflow DAG uses SQL operators exclusively
- [ ] Star schema properly normalized with foreign keys

#### Functional Validation:
- [ ] NYSE stock data ingestion working
- [ ] USD/GBP currency conversion accurate
- [ ] Top 5 performers endpoint functional
- [ ] Price range filtering operational
- [ ] Daily ETL pipeline orchestrated via Airflow

#### Quality Validation:
- [ ] All tests passing after simplification
- [ ] Code quality maintained (Ruff, Black, MyPy)
- [ ] Documentation updated for new architecture
- [ ] No references to deleted functionality

---

## Conclusion

This simplification strategy transforms the ticker-converter from an over-engineered demonstration into a focused, SQL-centric ETL pipeline that meets the core requirements:

1. **Ingest**: NYSE stock data via Alpha Vantage API
2. **Transform**: Currency conversion and performance calculations via SQL
3. **Store**: Dimensional model in PostgreSQL  
4. **Orchestrate**: Airflow DAG with SQL operators
5. **Serve**: FastAPI endpoints executing SQL queries

The simplified approach demonstrates professional ETL pipeline development while maintaining focus on the actual requirements rather than excessive feature engineering.

**Next Action**: Begin implementation of Issue #12 (complexity reduction) immediately.
