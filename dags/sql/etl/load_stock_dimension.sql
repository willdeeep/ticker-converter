-- Load Stock Dimension from Raw Data
-- Populates stock dimension table from staging tables

-- Update stock dimension with any new symbols
INSERT INTO dim_stocks (symbol, company_name, sector, market_cap_category)
SELECT DISTINCT
    rsd.symbol,
    'Unknown Company' as company_name,
    'Unknown Sector' as sector,
    'Unknown Cap' as market_cap_category
FROM raw_stock_data rsd
WHERE rsd.symbol NOT IN (SELECT symbol FROM dim_stocks)
ON CONFLICT (symbol) DO NOTHING;
