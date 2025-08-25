-- Load Dimensions from Raw Data
-- Populates dimension tables from staging tables

-- Ensure date dimension has required dates
INSERT INTO dim_date (date_value, year_num, quarter_num, month_num, day_num, day_of_week, day_of_year, week_of_year, is_weekend)
SELECT DISTINCT
    rsd.data_date AS date_value,
    EXTRACT(YEAR FROM rsd.data_date) AS year_num,
    EXTRACT(QUARTER FROM rsd.data_date) AS quarter_num,
    EXTRACT(MONTH FROM rsd.data_date) AS month_num,
    EXTRACT(DAY FROM rsd.data_date) AS day_num,
    EXTRACT(DOW FROM rsd.data_date) AS day_of_week,
    EXTRACT(DOY FROM rsd.data_date) AS day_of_year,
    EXTRACT(WEEK FROM rsd.data_date) AS week_of_year,
    COALESCE(EXTRACT(DOW FROM rsd.data_date) IN (0, 6), FALSE) AS is_weekend
FROM raw_stock_data AS rsd
WHERE rsd.date_value NOT IN (SELECT dd.date_value FROM dim_date AS dd)

UNION

SELECT DISTINCT
    rcd.data_date AS date_value,
    EXTRACT(YEAR FROM rcd.data_date) AS year_num,
    EXTRACT(QUARTER FROM rcd.data_date) AS quarter_num,
    EXTRACT(MONTH FROM rcd.data_date) AS month_num,
    EXTRACT(DAY FROM rcd.data_date) AS day_num,
    EXTRACT(DOW FROM rcd.data_date) AS day_of_week,
    EXTRACT(DOY FROM rcd.data_date) AS day_of_year,
    EXTRACT(WEEK FROM rcd.data_date) AS week_of_year,
    COALESCE(EXTRACT(DOW FROM rcd.data_date) IN (0, 6), FALSE) AS is_weekend
FROM raw_currency_data AS rcd
WHERE rcd.date_value NOT IN (SELECT dd.date_value FROM dim_date AS dd);

-- Update stock dimension with any new symbols
INSERT INTO dim_stocks (symbol, company_name, sector, market_cap_category)
SELECT DISTINCT
    symbol,
    'Unknown Company' AS company_name,
    'Unknown Sector' AS sector,
    'Unknown Cap' AS market_cap_category
FROM raw_stock_data
WHERE symbol NOT IN (SELECT ds.symbol FROM dim_stocks AS ds)
ON CONFLICT (symbol) DO NOTHING;
