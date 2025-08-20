-- Purpose: Create fact tables for storing stock prices and currency exchange rates
-- Fact Tables for NYSE Stock Data
-- Creates tables for price data and currency rates

-- Fact: Stock Prices (daily OHLCV data)
CREATE TABLE IF NOT EXISTS fact_stock_prices (
    price_id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES dim_stocks(stock_id),
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    opening_price DECIMAL(10,4) NOT NULL,
    high_price DECIMAL(10,4) NOT NULL,
    low_price DECIMAL(10,4) NOT NULL,
    closing_price DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    adjusted_close DECIMAL(10,4),
    daily_return DECIMAL(8,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date_id)
);

-- Fact: Currency Exchange Rates (daily USD/GBP)
CREATE TABLE IF NOT EXISTS fact_currency_rates (
    rate_id SERIAL PRIMARY KEY,
    from_currency_id INTEGER NOT NULL REFERENCES dim_currency(currency_id),
    to_currency_id INTEGER NOT NULL REFERENCES dim_currency(currency_id),
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    exchange_rate DECIMAL(10,6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency_id, to_currency_id, date_id)
);

-- Raw staging tables for API data
CREATE TABLE IF NOT EXISTS raw_stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    data_date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT,
    source VARCHAR(50) DEFAULT 'alpha_vantage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_date, source)
);

CREATE TABLE IF NOT EXISTS raw_currency_data (
    id SERIAL PRIMARY KEY,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    data_date DATE NOT NULL,
    exchange_rate DECIMAL(10,6) NOT NULL,
    source VARCHAR(50) DEFAULT 'alpha_vantage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, data_date, source)
);
