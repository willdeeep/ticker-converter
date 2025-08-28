-- Purpose: Create analytical views for FastAPI endpoints and data analysis
-- Analytical Views for FastAPI Endpoints
-- Creates materialized views for common queries

-- View: Latest Stock Prices with GBP Conversion
CREATE OR REPLACE VIEW vw_latest_stock_prices AS
SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value,
    fsp.closing_price AS price_usd,
    fsp.volume,
    fsp.daily_return,
    fsp.opening_price,
    fsp.high_price,
    fsp.low_price,
    ROUND(fsp.closing_price * fcr.exchange_rate, 4) AS price_gbp
FROM fact_stock_prices AS fsp
INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
LEFT JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
    AND fcr.from_currency_id = (SELECT currency_id FROM dim_currency
WHERE currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT currency_id FROM dim_currency
WHERE currency_code = 'GBP')
WHERE ds.is_active = TRUE
ORDER BY dd.date_value DESC, ds.symbol ASC;

-- View: Daily Performance Summary
CREATE OR REPLACE VIEW vw_daily_performance AS
SELECT
    dd.date_value,
    COUNT(fsp.stock_id) AS stocks_traded,
    AVG(fsp.daily_return) AS avg_daily_return,
    MAX(fsp.daily_return) AS max_daily_return,
    MIN(fsp.daily_return) AS min_daily_return,
    SUM(fsp.volume) AS total_volume,
    AVG(fsp.closing_price) AS avg_closing_price
FROM fact_stock_prices AS fsp
INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
WHERE ds.is_active = TRUE
GROUP BY dd.date_value
ORDER BY dd.date_value DESC;

-- View: Stock Performance Rankings
CREATE OR REPLACE VIEW vw_stock_rankings AS
SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value,
    fsp.closing_price,
    fsp.daily_return,
    fsp.volume,
    RANK() OVER (PARTITION BY dd.date_value ORDER BY fsp.daily_return DESC) AS return_rank,
    RANK() OVER (PARTITION BY dd.date_value ORDER BY fsp.volume DESC) AS volume_rank
FROM fact_stock_prices AS fsp
INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
WHERE ds.is_active = TRUE
ORDER BY dd.date_value DESC, fsp.daily_return DESC;
