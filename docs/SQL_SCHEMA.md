# PostgreSQL Database Schema Documentation

## Overview

The ticker-converter project implements a star schema dimensional model in PostgreSQL, optimized for NYSE stock market data analytics with USD/GBP currency conversion capabilities.

## Schema Design

### Dimensional Model Architecture

The PostgreSQL database follows a star schema pattern with clearly separated dimension and fact tables, enabling efficient analytical queries and maintaining data integrity through proper normalization.

## Dimension Tables

### dim_stocks
Primary dimension for stock market securities.

```sql
CREATE TABLE dim_stocks (
    stock_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    exchange VARCHAR(50) DEFAULT 'NYSE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Master reference for all stock symbols in the system.
**Scope**: Limited to 5-10 major NYSE stocks (AAPL, MSFT, GOOGL, TSLA, NVDA).

### dim_dates
Date dimension for time-based analytics.

```sql
CREATE TABLE dim_dates (
    date_id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_trading_day BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Enables time-based filtering and aggregation for stock market analysis.
**Scope**: Daily granularity only, with trading day indicators.

### dim_currencies
Currency reference for conversion operations.

```sql
CREATE TABLE dim_currencies (
    currency_id INTEGER PRIMARY KEY,
    code VARCHAR(3) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Reference table for currency conversion operations.
**Scope**: USD and GBP only for simplified conversion requirements.

## Fact Tables

### fact_stock_prices
Central fact table storing daily stock market data.

```sql
CREATE TABLE fact_stock_prices (
    price_id INTEGER PRIMARY KEY,
    date_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    open_usd DECIMAL(10,2) NOT NULL,
    high_usd DECIMAL(10,2) NOT NULL,
    low_usd DECIMAL(10,2) NOT NULL,
    close_usd DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_id) REFERENCES dim_dates(date_id),
    FOREIGN KEY (stock_id) REFERENCES dim_stocks(stock_id),
    UNIQUE(date_id, stock_id)
);
```

**Purpose**: Stores daily OHLCV data for NYSE stocks in USD.
**Constraints**: Unique constraint prevents duplicate entries per stock per day.

### fact_currency_rates
Exchange rate data for currency conversion.

```sql
CREATE TABLE fact_currency_rates (
    rate_id INTEGER PRIMARY KEY,
    date_id INTEGER NOT NULL,
    from_currency_id INTEGER NOT NULL,
    to_currency_id INTEGER NOT NULL,
    exchange_rate DECIMAL(10,6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_id) REFERENCES dim_dates(date_id),
    FOREIGN KEY (from_currency_id) REFERENCES dim_currencies(currency_id),
    FOREIGN KEY (to_currency_id) REFERENCES dim_currencies(currency_id),
    UNIQUE(date_id, from_currency_id, to_currency_id)
);
```

**Purpose**: Daily USD/GBP exchange rates for price conversion calculations.
**Scope**: Single currency pair (USD to GBP) with daily frequency.

## Analytical Views

### v_stock_performance
Pre-calculated performance metrics using SQL window functions.

```sql
CREATE VIEW v_stock_performance AS
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    LAG(p.close_usd) OVER (PARTITION BY p.stock_id ORDER BY d.date) as prev_close,
    ROUND(
        (p.close_usd - LAG(p.close_usd) OVER (PARTITION BY p.stock_id ORDER BY d.date)) / 
        LAG(p.close_usd) OVER (PARTITION BY p.stock_id ORDER BY d.date) * 100, 4
    ) as daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
ORDER BY d.date DESC, s.symbol;
```

### v_stocks_gbp
Currency-converted stock prices for GBP analysis.

```sql
CREATE VIEW v_stocks_gbp AS
SELECT 
    s.symbol,
    d.date,
    p.open_usd,
    p.high_usd,
    p.low_usd,
    p.close_usd,
    ROUND(p.close_usd * cr.exchange_rate, 2) as close_gbp,
    p.volume
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN fact_currency_rates cr ON d.date_id = cr.date_id
JOIN dim_currencies c1 ON cr.from_currency_id = c1.currency_id
JOIN dim_currencies c2 ON cr.to_currency_id = c2.currency_id
WHERE c1.code = 'USD' AND c2.code = 'GBP';
```

### v_top_performers
Optimized view for top-performing stocks query.

```sql
CREATE VIEW v_top_performers AS
SELECT 
    symbol,
    daily_return_pct,
    close_usd,
    date
FROM v_stock_performance
WHERE daily_return_pct IS NOT NULL
ORDER BY daily_return_pct DESC;
```

## Performance Optimization

### Indexes
```sql
-- Primary performance indexes
CREATE INDEX idx_stock_prices_date_stock ON fact_stock_prices(date_id, stock_id);
CREATE INDEX idx_currency_rates_date ON fact_currency_rates(date_id);
CREATE INDEX idx_stocks_symbol ON dim_stocks(symbol);
CREATE INDEX idx_dates_date ON dim_dates(date);

-- Analytical query optimization
CREATE INDEX idx_stock_prices_close ON fact_stock_prices(close_usd);
CREATE INDEX idx_stock_performance ON fact_stock_prices(stock_id, date_id);
```

## Data Integrity

### Constraints
- Primary keys ensure unique record identification
- Foreign keys maintain referential integrity between dimensions and facts
- Unique constraints prevent duplicate data entry
- NOT NULL constraints ensure data completeness for critical fields

### Data Validation
- Price values must be positive (enforced at application layer)
- Volume must be non-negative
- Exchange rates must be positive
- Date ranges validated for trading days

## Usage Patterns

### Common Queries
1. **Top Performers**: ORDER BY daily_return_pct DESC LIMIT 5
2. **Price Ranges**: WHERE close_usd BETWEEN min_price AND max_price  
3. **Currency Conversion**: JOIN with fact_currency_rates table
4. **Time Series**: WHERE date BETWEEN start_date AND end_date

### ETL Operations
1. **Extract**: Raw data insertion into fact tables
2. **Transform**: View materialization and metric calculation
3. **Load**: Dimension population and fact table updates

This schema design supports efficient analytical queries while maintaining data integrity and enabling straightforward currency conversion operations for the simplified NYSE stock analysis requirements.
