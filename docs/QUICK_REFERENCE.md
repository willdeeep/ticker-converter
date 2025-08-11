# Quick Reference: SQL-Centric Pipeline Implementation

## 🚨 IMMEDIATE ACTIONS REQUIRED

### Issue Execution Order:
1. **Issue #12** - Complexity Reduction (START HERE - HIGH PRIORITY)
2. **Issue #3** - Simplified Data Models  
3. **Issue #4** - SQL Star Schema
4. **Issue #13** - Data Ingestion
5. **Issue #5** - Airflow SQL DAG
6. **Issue #6** - FastAPI SQL Endpoints
7. **Issue #8** - Documentation

## 🗑️ FILES TO DELETE (Issue #12)

```bash
# Execute these deletions immediately:
rm src/ticker_converter/etl_modules/feature_engineer.py
rm src/ticker_converter/etl_modules/quality_validator.py
rm src/ticker_converter/data_models/quality_metrics.py
rm scripts/demo_pipeline.py
rm tests/unit/etl_modules/test_quality_validator.py
rm tests/integration/test_data_pipeline.py
```

## CLASSES TO REMOVE FROM `market_data.py`

Keep ONLY:
- `MarketDataPoint` 
- `RawMarketData`

Remove:
- `VolatilityFlag`
- `CleanedMarketData` 
- `FeatureEngineeredData`
- `ValidationResult`

Add:
- `CurrencyRate` (new model for USD/GBP)

## SIMPLIFIED SCOPE

**Data Focus**:
- Magnificent Seven stocks: AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA
- Daily OHLCV data only
- USD → GBP conversion only
- Alpha Vantage API (Issue #1 complete)

**Technical Focus**:
- SQL-first transformations
- Star schema (dim/fact tables)
- Direct SQL in API endpoints
- SQL operators in Airflow
- PostgreSQL as single database solution

## SQL SCHEMA DESIGN

```sql
-- Dimensions
dim_stocks (stock_id, symbol, company_name, sector, exchange)
dim_dates (date_id, date, year, month, quarter, is_trading_day)
dim_currencies (currency_id, code, name, country)

-- Facts  
fact_stock_prices (date_id, stock_id, open_usd, high_usd, low_usd, close_usd, volume)
fact_currency_rates (date_id, from_currency_id, to_currency_id, exchange_rate)

-- Views
v_stock_performance  # Daily returns via SQL window functions
v_stocks_gbp         # Prices in GBP via JOINs
v_top_performers     # Top 5 stocks ORDER BY LIMIT 5
```

## API ENDPOINTS (SQL-Powered)

```python
@app.get("/api/stocks/top-performers")
# Execute: SELECT TOP 5 ... ORDER BY daily_return DESC LIMIT 5

@app.get("/api/stocks/price-range")  
# Execute: SELECT ... WHERE price BETWEEN ? AND ?

@app.get("/api/stocks/gbp-prices")
# Execute: SELECT ... JOIN fact_currency_rates ...
```

## AIRFLOW DAG STRUCTURE

```python
fetch_stock_data >> fetch_currency_rates >> transform_to_warehouse >> data_quality_check
```

Tasks use `SQLExecuteQueryOperator` with external `.sql` files

## 📁 NEW DIRECTORY STRUCTURE

```
sql/
├── ddl/
│   ├── 001_create_dimensions.sql
│   ├── 002_create_facts.sql  
│   ├── 003_create_views.sql
│   └── 004_create_indexes.sql
├── etl/
│   ├── daily_transform.sql
│   ├── data_quality_checks.sql
│   └── load_dimensions.sql
└── queries/
    ├── top_performers.sql
    ├── price_ranges.sql
    └── currency_conversion.sql

src/data_ingestion/
├── nyse_fetcher.py
└── currency_fetcher.py

api/
├── main.py
├── models.py
└── queries.sql

dags/
└── nyse_stock_etl.py
```

## SUCCESS METRICS

- [ ] 50%+ file count reduction
- [ ] All transformations in SQL
- [ ] API endpoints execute SQL directly  
- [ ] Airflow uses SQL operators only
- [ ] Tests pass after simplification

---

**Remember**: Start with Issue #12 (complexity reduction) before implementing new features!
