-- Purpose: Create dimension tables for NYSE stock analysis data warehouse
-- Dimension Tables for NYSE Stock Analysis
-- Creates lookup tables for stocks, dates, and currencies

-- Dimension: Stocks (Magnificent Seven focus)
CREATE TABLE IF NOT EXISTS dim_stocks (
    stock_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    market_cap_category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    date_value DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Currency
CREATE TABLE IF NOT EXISTS dim_currency (
    currency_id SERIAL PRIMARY KEY,
    currency_code VARCHAR(3) NOT NULL UNIQUE,
    currency_name VARCHAR(50) NOT NULL,
    is_base_currency BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Magnificent Seven stocks
INSERT INTO dim_stocks (symbol, company_name, sector, market_cap_category) VALUES
    ('AAPL', 'Apple Inc.', 'Technology', 'Large Cap'),
    ('MSFT', 'Microsoft Corporation', 'Technology', 'Large Cap'),
    ('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'Large Cap'),
    ('GOOGL', 'Alphabet Inc.', 'Technology', 'Large Cap'),
    ('META', 'Meta Platforms Inc.', 'Technology', 'Large Cap'),
    ('NVDA', 'NVIDIA Corporation', 'Technology', 'Large Cap'),
    ('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'Large Cap')
ON CONFLICT (symbol) DO NOTHING;

-- Insert supported currencies
INSERT INTO dim_currency (currency_code, currency_name, is_base_currency) VALUES
    ('USD', 'US Dollar', TRUE),
    ('GBP', 'British Pound', FALSE)
ON CONFLICT (currency_code) DO NOTHING;
