-- Daily Transform: Direct fact table loading with calculated metrics
-- Note: Raw staging tables have been removed. Data is now loaded directly into fact tables
-- via Python helpers with dimensional lookups and automatic date dimension creation.

-- The following transformations are now handled during direct insertion:
-- 1. Dimensional lookups (stock_id, currency_id, date_id)
-- 2. Data validation and type conversion
-- 3. Automatic date dimension population
-- 4. Conflict resolution (ON CONFLICT DO NOTHING)

-- Post-processing calculations that still require SQL transforms:

-- Update daily return calculations for newly inserted stock prices
-- This runs after direct fact loading to calculate performance metrics
WITH daily_returns AS (
    SELECT 
        fsp.stock_id,
        fsp.date_id,
        fsp.closing_price,
        LAG(fsp.closing_price) OVER (
            PARTITION BY fsp.stock_id 
            ORDER BY dd.date_value
        ) AS prev_close,
        CASE 
            WHEN LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value) IS NOT NULL
            THEN ROUND(
                ((fsp.closing_price - LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value))
                 / LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value)) * 100,
                6
            )
        END AS calculated_daily_return
    FROM fact_stock_prices fsp
    JOIN dim_date dd ON fsp.date_id = dd.date_id
    WHERE fsp.daily_return IS NULL  -- Only calculate for records without daily_return
)
UPDATE fact_stock_prices 
SET daily_return = dr.calculated_daily_return
FROM daily_returns dr
WHERE fact_stock_prices.stock_id = dr.stock_id 
AND fact_stock_prices.date_id = dr.date_id
AND dr.calculated_daily_return IS NOT NULL;

-- Update daily returns for existing records where missing
UPDATE fact_stock_prices
SET daily_return = subq.calculated_return,
    updated_at = CURRENT_TIMESTAMP
FROM (
    SELECT
        fsp.price_id,
        CASE
            WHEN LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value) IS NOT NULL
            THEN ROUND(
                ((fsp.closing_price - LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value))
                 / LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value)) * 100,
                6
            )
        END AS calculated_return
    FROM fact_stock_prices AS fsp
    INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
    WHERE fsp.daily_return IS NULL
) AS subq
WHERE fact_stock_prices.price_id = subq.price_id
AND subq.calculated_return IS NOT NULL;
