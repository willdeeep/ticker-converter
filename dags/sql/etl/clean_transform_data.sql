-- Clean and transform data
-- Note: Data cleaning and validation is now handled during direct fact loading
-- This is a placeholder SQL file for additional post-processing transformations

SELECT 'Data cleaning handled during direct fact loading...' AS status;

-- Data cleaning and validation is now performed in Python during direct insertion:
-- 1. Validation functions in load_raw_to_db.py check data quality before insertion
-- 2. DatabaseManager handles type conversion and dimensional lookups
-- 3. Invalid records are logged and skipped, not inserted into fact tables

-- Example of post-processing transformations that could be added:
-- WITH stock_metrics AS (
--   SELECT 
--     fsp.stock_id,
--     fsp.date_id,
--     fsp.closing_price,
--     AVG(fsp.closing_price) OVER (
--       PARTITION BY fsp.stock_id 
--       ORDER BY dd.date_value 
--       ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
--     ) AS moving_avg_20d,
--     AVG(fsp.volume) OVER (
--       PARTITION BY fsp.stock_id 
--       ORDER BY dd.date_value 
--       ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
--     ) AS avg_volume_10d
--   FROM fact_stock_prices fsp
--   JOIN dim_date dd ON fsp.date_id = dd.date_id
--   WHERE dd.date_value = '{{ ds }}'
-- )
-- UPDATE fact_stock_prices 
-- SET 
--   additional_metrics = jsonb_build_object(
--     'moving_avg_20d', sm.moving_avg_20d,
--     'avg_volume_10d', sm.avg_volume_10d
--   )
-- FROM stock_metrics sm
-- WHERE fact_stock_prices.stock_id = sm.stock_id 
-- AND fact_stock_prices.date_id = sm.date_id;
