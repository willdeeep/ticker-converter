# SQL Query Examples

## Overview

This document provides comprehensive SQL query examples for the ticker-converter pipeline, demonstrating the SQL-first approach for all data transformations and analytical operations.

## Table of Contents

1. [Top Performers Queries](#top-performers-queries)
2. [Currency Conversion Examples](#currency-conversion-examples)
3. [Data Quality Validation](#data-quality-validation)
4. [Performance Optimization](#performance-optimization)
5. [Common Analytics Patterns](#common-analytics-patterns)

## Top Performers Queries

### Daily Top 5 Performers
```sql
-- Get top 5 stocks by daily return percentage
SELECT 
    s.symbol,
    s.company_name,
    d.date,
    p.close_usd,
    ROUND(
        ((p.close_usd - LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) 
         / LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date)) * 100, 
        2
    ) as daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date = CURRENT_DATE - INTERVAL '1 day'
  AND LAG(p.close_usd) OVER (PARTITION BY s.symbol ORDER BY d.date) IS NOT NULL
ORDER BY daily_return_pct DESC
LIMIT 5;
```

### Weekly Top Performers
```sql
-- Get top performers over the last 7 trading days
WITH weekly_performance AS (
    SELECT 
        s.symbol,
        s.company_name,
        MIN(p.close_usd) as week_start_price,
        MAX(p.close_usd) as week_end_price,
        COUNT(*) as trading_days
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    JOIN dim_dates d ON p.date_id = d.date_id
    WHERE d.date >= CURRENT_DATE - INTERVAL '7 days'
      AND d.is_trading_day = TRUE
    GROUP BY s.symbol, s.company_name
    HAVING COUNT(*) >= 5  -- At least 5 trading days
)
SELECT 
    symbol,
    company_name,
    week_start_price,
    week_end_price,
    ROUND(
        ((week_end_price - week_start_price) / week_start_price) * 100, 
        2
    ) as weekly_return_pct
FROM weekly_performance
ORDER BY weekly_return_pct DESC;
```

### Top Performers by Volume
```sql
-- Find stocks with highest volume and positive returns
SELECT 
    s.symbol,
    d.date,
    p.volume,
    p.close_usd,
    sp.daily_return_pct
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN v_stock_performance sp ON s.symbol = sp.symbol AND d.date = sp.date
WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
  AND sp.daily_return_pct > 0
ORDER BY p.volume DESC, sp.daily_return_pct DESC
LIMIT 10;
```

## Currency Conversion Examples

### Stock Prices in GBP
```sql
-- Convert all stock prices to GBP using daily exchange rates
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    cr.exchange_rate as usd_to_gbp_rate,
    ROUND(p.close_usd / cr.exchange_rate, 4) as close_gbp,
    ROUND(p.open_usd / cr.exchange_rate, 4) as open_gbp,
    ROUND(p.high_usd / cr.exchange_rate, 4) as high_gbp,
    ROUND(p.low_usd / cr.exchange_rate, 4) as low_gbp
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN fact_currency_rates cr ON d.date_id = cr.date_id
WHERE cr.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
  AND cr.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP')
  AND d.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY s.symbol, d.date;
```

### Currency Rate Trends
```sql
-- Analyze USD/GBP exchange rate trends over time
SELECT 
    d.date,
    cr.exchange_rate,
    LAG(cr.exchange_rate) OVER (ORDER BY d.date) as prev_rate,
    ROUND(
        ((cr.exchange_rate - LAG(cr.exchange_rate) OVER (ORDER BY d.date)) 
         / LAG(cr.exchange_rate) OVER (ORDER BY d.date)) * 100, 
        4
    ) as rate_change_pct,
    CASE 
        WHEN cr.exchange_rate > LAG(cr.exchange_rate) OVER (ORDER BY d.date) THEN 'USD Strengthening'
        WHEN cr.exchange_rate < LAG(cr.exchange_rate) OVER (ORDER BY d.date) THEN 'USD Weakening'
        ELSE 'No Change'
    END as trend_direction
FROM fact_currency_rates cr
JOIN dim_dates d ON cr.date_id = d.date_id
WHERE cr.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
  AND cr.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP')
  AND d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY d.date;
```

### Price Range Queries in Multiple Currencies
```sql
-- Get stocks within price range, shown in both USD and GBP
SELECT 
    s.symbol,
    s.company_name,
    d.date,
    p.close_usd,
    ROUND(p.close_usd / cr.exchange_rate, 4) as close_gbp
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN fact_currency_rates cr ON d.date_id = cr.date_id
WHERE cr.from_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'USD')
  AND cr.to_currency_id = (SELECT currency_id FROM dim_currencies WHERE code = 'GBP')
  AND p.close_usd BETWEEN 100.00 AND 300.00  -- Price range filter
  AND d.date = CURRENT_DATE - INTERVAL '1 day'
ORDER BY p.close_usd DESC;
```

## Data Quality Validation

### Missing Data Detection
```sql
-- Identify missing trading days or stock data
WITH expected_trading_days AS (
    SELECT DISTINCT date_id, date
    FROM dim_dates
    WHERE is_trading_day = TRUE
      AND date >= CURRENT_DATE - INTERVAL '30 days'
),
actual_data AS (
    SELECT DISTINCT 
        p.date_id, 
        s.symbol,
        COUNT(*) OVER (PARTITION BY p.date_id) as stocks_reported
    FROM fact_stock_prices p
    JOIN dim_stocks s ON p.stock_id = s.stock_id
    WHERE p.date_id IN (SELECT date_id FROM expected_trading_days)
)
SELECT 
    etd.date,
    COALESCE(ad.stocks_reported, 0) as stocks_reported,
    (SELECT COUNT(*) FROM dim_stocks) as expected_stocks,
    CASE 
        WHEN COALESCE(ad.stocks_reported, 0) < (SELECT COUNT(*) FROM dim_stocks) 
        THEN 'INCOMPLETE DATA'
        ELSE 'COMPLETE'
    END as data_status
FROM expected_trading_days etd
LEFT JOIN actual_data ad ON etd.date_id = ad.date_id
ORDER BY etd.date DESC;
```

### Price Anomaly Detection
```sql
-- Detect unusual price movements (>20% daily change)
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    sp.daily_return_pct,
    CASE 
        WHEN ABS(sp.daily_return_pct) > 20 THEN 'HIGH VOLATILITY'
        WHEN ABS(sp.daily_return_pct) > 10 THEN 'MEDIUM VOLATILITY'
        ELSE 'NORMAL'
    END as volatility_flag
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
JOIN v_stock_performance sp ON s.symbol = sp.symbol AND d.date = sp.date
WHERE ABS(sp.daily_return_pct) > 10
  AND d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY ABS(sp.daily_return_pct) DESC;
```

### Data Consistency Checks
```sql
-- Verify OHLC data consistency (High >= Low, etc.)
SELECT 
    s.symbol,
    d.date,
    p.open_usd,
    p.high_usd,
    p.low_usd,
    p.close_usd,
    CASE 
        WHEN p.high_usd < p.low_usd THEN 'ERROR: High < Low'
        WHEN p.high_usd < p.open_usd THEN 'ERROR: High < Open'
        WHEN p.high_usd < p.close_usd THEN 'ERROR: High < Close'
        WHEN p.low_usd > p.open_usd THEN 'ERROR: Low > Open'
        WHEN p.low_usd > p.close_usd THEN 'ERROR: Low > Close'
        ELSE 'VALID'
    END as data_validation
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE NOT (
    p.high_usd >= p.low_usd 
    AND p.high_usd >= p.open_usd 
    AND p.high_usd >= p.close_usd
    AND p.low_usd <= p.open_usd 
    AND p.low_usd <= p.close_usd
)
ORDER BY d.date DESC, s.symbol;
```

## Performance Optimization

### Recommended Indexes
```sql
-- Primary indexes for fact tables
CREATE INDEX idx_fact_stock_prices_date_stock ON fact_stock_prices(date_id, stock_id);
CREATE INDEX idx_fact_stock_prices_stock_date ON fact_stock_prices(stock_id, date_id);
CREATE INDEX idx_fact_currency_rates_date ON fact_currency_rates(date_id);

-- Indexes for common WHERE clauses
CREATE INDEX idx_dim_dates_date ON dim_dates(date);
CREATE INDEX idx_dim_dates_trading_day ON dim_dates(is_trading_day, date);
CREATE INDEX idx_dim_stocks_symbol ON dim_stocks(symbol);
CREATE INDEX idx_dim_currencies_code ON dim_currencies(code);

-- Composite indexes for JOIN performance
CREATE INDEX idx_fact_stock_prices_composite ON fact_stock_prices(date_id, stock_id, close_usd);
CREATE INDEX idx_fact_currency_rates_composite ON fact_currency_rates(date_id, from_currency_id, to_currency_id);
```

### Query Performance Analysis
```sql
-- Analyze table sizes and growth
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_stat_get_tuples_returned(c.oid) as rows_read,
    pg_stat_get_tuples_fetched(c.oid) as rows_fetched
FROM pg_tables pt
JOIN pg_class c ON c.relname = pt.tablename
WHERE schemaname = 'public'
  AND tablename LIKE 'fact_%' OR tablename LIKE 'dim_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Partitioning Strategy (Future Enhancement)
```sql
-- Example: Partition fact_stock_prices by date range
-- (For when data volume grows significantly)
CREATE TABLE fact_stock_prices_2024 PARTITION OF fact_stock_prices
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE fact_stock_prices_2025 PARTITION OF fact_stock_prices
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

## Common Analytics Patterns

### Moving Averages (SQL Window Functions)
```sql
-- Calculate 5-day and 20-day moving averages
SELECT 
    s.symbol,
    d.date,
    p.close_usd,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_5_day,
    ROUND(
        AVG(p.close_usd) OVER (
            PARTITION BY s.symbol 
            ORDER BY d.date 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ), 2
    ) as ma_20_day
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE d.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY s.symbol, d.date;
```

### Stock Correlation Analysis
```sql
-- Calculate correlation between two stocks
WITH stock_returns AS (
    SELECT 
        d.date,
        s.symbol,
        sp.daily_return_pct
    FROM v_stock_performance sp
    JOIN dim_stocks s ON sp.symbol = s.symbol
    JOIN dim_dates d ON sp.date = d.date
    WHERE s.symbol IN ('AAPL', 'MSFT')
      AND sp.daily_return_pct IS NOT NULL
      AND d.date >= CURRENT_DATE - INTERVAL '90 days'
),
paired_returns AS (
    SELECT 
        a.date,
        a.daily_return_pct as aapl_return,
        m.daily_return_pct as msft_return
    FROM stock_returns a
    JOIN stock_returns m ON a.date = m.date
    WHERE a.symbol = 'AAPL' AND m.symbol = 'MSFT'
)
SELECT 
    COUNT(*) as observations,
    ROUND(CORR(aapl_return, msft_return)::numeric, 4) as correlation_coefficient,
    CASE 
        WHEN CORR(aapl_return, msft_return) > 0.7 THEN 'Strong Positive'
        WHEN CORR(aapl_return, msft_return) > 0.3 THEN 'Moderate Positive'
        WHEN CORR(aapl_return, msft_return) > -0.3 THEN 'Weak Correlation'
        WHEN CORR(aapl_return, msft_return) > -0.7 THEN 'Moderate Negative'
        ELSE 'Strong Negative'
    END as correlation_strength
FROM paired_returns;
```

### Market Summary Statistics
```sql
-- Daily market summary across all tracked stocks
SELECT 
    d.date,
    COUNT(DISTINCT s.symbol) as stocks_tracked,
    ROUND(AVG(p.close_usd), 2) as avg_close_price,
    ROUND(AVG(sp.daily_return_pct), 2) as avg_daily_return,
    COUNT(CASE WHEN sp.daily_return_pct > 0 THEN 1 END) as stocks_up,
    COUNT(CASE WHEN sp.daily_return_pct < 0 THEN 1 END) as stocks_down,
    MAX(sp.daily_return_pct) as best_performer_return,
    MIN(sp.daily_return_pct) as worst_performer_return,
    SUM(p.volume) as total_volume
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
LEFT JOIN v_stock_performance sp ON s.symbol = sp.symbol AND d.date = sp.date
WHERE d.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY d.date
ORDER BY d.date DESC;
```

## API Query Templates

### FastAPI Endpoint Queries

**Top Performers Endpoint**
```sql
-- File: sql/queries/top_performers.sql
SELECT symbol, daily_return_pct, close_usd, date 
FROM v_top_performers 
WHERE daily_return_pct IS NOT NULL 
ORDER BY daily_return_pct DESC 
LIMIT 5;
```

**Price Range Endpoint**
```sql
-- File: sql/queries/price_ranges.sql
SELECT 
    s.symbol,
    s.company_name,
    p.close_usd,
    d.date
FROM fact_stock_prices p
JOIN dim_stocks s ON p.stock_id = s.stock_id
JOIN dim_dates d ON p.date_id = d.date_id
WHERE p.close_usd BETWEEN $1 AND $2
  AND d.date = (SELECT MAX(date) FROM dim_dates WHERE is_trading_day = TRUE)
ORDER BY p.close_usd DESC;
```

**Currency Conversion Endpoint**
```sql
-- File: sql/queries/currency_conversion.sql
SELECT 
    symbol,
    date,
    close_usd,
    close_gbp,
    exchange_rate
FROM v_stocks_gbp
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY symbol, date DESC;
```

## Best Practices

### Query Optimization
1. **Use appropriate indexes** for WHERE and JOIN clauses
2. **Limit result sets** with proper LIMIT clauses
3. **Use views** for complex, reusable calculations
4. **Partition large tables** by date when volume grows
5. **Analyze query plans** with EXPLAIN for optimization

### Data Quality
1. **Implement CHECK constraints** on fact tables
2. **Use NOT NULL constraints** for critical fields
3. **Create validation views** for data quality monitoring
4. **Set up alerts** for data anomalies

### Maintainability
1. **Store complex queries** in separate .sql files
2. **Document query logic** with comments
3. **Use consistent naming** conventions
4. **Version control** all SQL scripts
5. **Test queries** with sample data before production
