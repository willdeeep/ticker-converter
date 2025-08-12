-- Load Date Dimension from Raw Data
-- Populates date dimension table with required dates

-- Ensure date dimension has required dates from stock data
INSERT INTO dim_date (date_value, year, quarter, month, day, day_of_week, day_of_year, week_of_year, is_weekend)
SELECT DISTINCT
    rsd.data_date as date_value,
    EXTRACT(YEAR FROM rsd.data_date) as year,
    EXTRACT(QUARTER FROM rsd.data_date) as quarter,
    EXTRACT(MONTH FROM rsd.data_date) as month,
    EXTRACT(DAY FROM rsd.data_date) as day,
    EXTRACT(DOW FROM rsd.data_date) as day_of_week,
    EXTRACT(DOY FROM rsd.data_date) as day_of_year,
    EXTRACT(WEEK FROM rsd.data_date) as week_of_year,
    CASE WHEN EXTRACT(DOW FROM rsd.data_date) IN (0,6) THEN TRUE ELSE FALSE END as is_weekend
FROM raw_stock_data rsd
WHERE rsd.data_date NOT IN (SELECT date_value FROM dim_date)

UNION

-- Ensure date dimension has required dates from currency data
SELECT DISTINCT
    rcd.data_date as date_value,
    EXTRACT(YEAR FROM rcd.data_date) as year,
    EXTRACT(QUARTER FROM rcd.data_date) as quarter,
    EXTRACT(MONTH FROM rcd.data_date) as month,
    EXTRACT(DAY FROM rcd.data_date) as day,
    EXTRACT(DOW FROM rcd.data_date) as day_of_week,
    EXTRACT(DOY FROM rcd.data_date) as day_of_year,
    EXTRACT(WEEK FROM rcd.data_date) as week_of_year,
    CASE WHEN EXTRACT(DOW FROM rcd.data_date) IN (0,6) THEN TRUE ELSE FALSE END as is_weekend
FROM raw_currency_data rcd
WHERE rcd.data_date NOT IN (SELECT date_value FROM dim_date);
