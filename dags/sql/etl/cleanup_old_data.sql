-- Data Retention Management
-- Cleanup old data according to retention policies

-- Delete raw stock data older than 90 days
DELETE FROM raw_stock_data
WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

-- Delete raw currency data older than 90 days  
DELETE FROM raw_currency_data
WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

-- Archive old fact data to separate tables (optional)
-- Keep 2 years of fact data, archive older data

-- Clean up dimension dates older than 5 years (keep only recent history)
DELETE FROM dim_date
WHERE date_value < CURRENT_DATE - INTERVAL '5 years'
AND date_id NOT IN (
    SELECT DISTINCT date_id FROM fact_stock_prices
    UNION
    SELECT DISTINCT date_id FROM fact_currency_rates
);

-- Update statistics after cleanup
ANALYZE fact_stock_prices;
ANALYZE fact_currency_rates;
ANALYZE raw_stock_data;
ANALYZE raw_currency_data;

-- Log cleanup completion
INSERT INTO dim_date (date_value, year, quarter, month, day, day_of_week, day_of_year, week_of_year, is_weekend)
SELECT
    CURRENT_DATE AS date_value,
    EXTRACT(YEAR FROM CURRENT_DATE) AS year_value,
    EXTRACT(QUARTER FROM CURRENT_DATE) AS quarter_value,
    EXTRACT(MONTH FROM CURRENT_DATE) AS month_value,
    EXTRACT(DAY FROM CURRENT_DATE) AS day_value,
    EXTRACT(DOW FROM CURRENT_DATE) AS day_of_week,
    EXTRACT(DOY FROM CURRENT_DATE) AS day_of_year,
    EXTRACT(WEEK FROM CURRENT_DATE) AS week_of_year,
    COALESCE(EXTRACT(DOW FROM CURRENT_DATE) IN (0, 6), FALSE) AS is_weekend
ON CONFLICT (date_value) DO NOTHING;
