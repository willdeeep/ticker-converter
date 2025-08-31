-- Purpose: Create performance indexes to optimize query performance for NYSE stock analytics
-- Performance Indexes for NYSE Stock Analytics
-- Creates indexes to optimize query performance

-- Primary lookup indexes for fact tables
CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_stock_date
    ON fact_stock_prices (stock_id, date_id);

CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_date
    ON fact_stock_prices (date_id);

CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_symbol_date
    ON fact_stock_prices (stock_id, date_id DESC);

-- Currency rate lookup indexes
CREATE INDEX IF NOT EXISTS idx_fact_currency_rates_date
    ON fact_currency_rates (date_id);

CREATE INDEX IF NOT EXISTS idx_fact_currency_rates_currencies_date
    ON fact_currency_rates (from_currency_id, to_currency_id, date_id);

-- Date dimension indexes for time-based queries
CREATE INDEX IF NOT EXISTS idx_dim_date_value
    ON dim_date (date_value);

CREATE INDEX IF NOT EXISTS idx_dim_date_year_month
    ON dim_date (year, month);

-- Stock dimension indexes
CREATE INDEX IF NOT EXISTS idx_dim_stocks_symbol
    ON dim_stocks (symbol);

CREATE INDEX IF NOT EXISTS idx_dim_stocks_active
    ON dim_stocks (is_active) WHERE is_active = TRUE;

-- Performance indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_daily_return
    ON fact_stock_prices (daily_return DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_volume
    ON fact_stock_prices (volume DESC);

CREATE INDEX IF NOT EXISTS idx_fact_stock_prices_closing_price
    ON fact_stock_prices (closing_price);
