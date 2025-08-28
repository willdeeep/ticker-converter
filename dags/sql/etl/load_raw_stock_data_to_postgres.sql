-- Load raw stock data from JSON files to dimensional model
-- This query processes JSON files from dags/raw_data/stocks/ and loads them into the star schema

-- Step 1: Create temporary table for JSON processing
DROP TABLE IF EXISTS temp_json_stock_data;
CREATE TEMP TABLE temp_json_stock_data (
    json_data JSONB
);

-- Step 2: Load JSON data from files (this will be populated by Python in the DAG)
-- Note: The actual file loading is handled by the Python operator that calls this SQL

-- Step 3: Insert into raw_stock_data staging table
INSERT INTO raw_stock_data (
    symbol, 
    data_date, 
    open_price, 
    high_price, 
    low_price, 
    close_price, 
    volume,
    source,
    created_at
)
SELECT 
    (json_data->>'symbol')::VARCHAR(10) as symbol,
    (json_data->>'data_date')::DATE as data_date,
    (json_data->>'open_price')::DECIMAL(10,4) as open_price,
    (json_data->>'high_price')::DECIMAL(10,4) as high_price,
    (json_data->>'low_price')::DECIMAL(10,4) as low_price,
    (json_data->>'close_price')::DECIMAL(10,4) as close_price,
    (json_data->>'volume')::BIGINT as volume,
    COALESCE(json_data->>'source', 'alpha_vantage') as source,
    COALESCE(
        (json_data->>'created_at')::TIMESTAMP,
        CURRENT_TIMESTAMP
    ) as created_at
FROM temp_json_stock_data
ON CONFLICT (symbol, data_date, source) 
DO UPDATE SET
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume,
    created_at = EXCLUDED.created_at;

-- Step 4: Load dates into dim_date if they don't exist
INSERT INTO dim_date (
    date_value, 
    year, 
    quarter, 
    month, 
    day, 
    day_of_week, 
    day_of_year, 
    week_of_year, 
    is_weekend, 
    is_holiday
)
SELECT DISTINCT
    data_date as date_value,
    EXTRACT(YEAR FROM data_date) as year,
    EXTRACT(QUARTER FROM data_date) as quarter,
    EXTRACT(MONTH FROM data_date) as month,
    EXTRACT(DAY FROM data_date) as day,
    EXTRACT(DOW FROM data_date) as day_of_week,
    EXTRACT(DOY FROM data_date) as day_of_year,
    EXTRACT(WEEK FROM data_date) as week_of_year,
    CASE WHEN EXTRACT(DOW FROM data_date) IN (0, 6) THEN TRUE ELSE FALSE END as is_weekend,
    FALSE as is_holiday  -- Default to false, can be updated later
FROM raw_stock_data
WHERE data_date IS NOT NULL
ON CONFLICT (date_value) DO NOTHING;

-- Step 5: Calculate daily returns and load into fact_stock_prices
INSERT INTO fact_stock_prices (
    stock_id,
    date_id,
    opening_price,
    high_price,
    low_price,
    closing_price,
    volume,
    adjusted_close,
    daily_return
)
SELECT 
    ds.stock_id,
    dd.date_id,
    rsd.open_price as opening_price,
    rsd.high_price,
    rsd.low_price,
    rsd.close_price as closing_price,
    rsd.volume,
    rsd.close_price as adjusted_close,  -- Using close_price as adjusted_close for now
    CASE 
        WHEN LAG(rsd.close_price) OVER (PARTITION BY ds.stock_id ORDER BY dd.date_value) IS NOT NULL
        THEN ((rsd.close_price / LAG(rsd.close_price) OVER (PARTITION BY ds.stock_id ORDER BY dd.date_value)) - 1)
        ELSE NULL
    END as daily_return
FROM raw_stock_data rsd
JOIN dim_stocks ds ON rsd.symbol = ds.symbol
JOIN dim_date dd ON rsd.data_date = dd.date_value
WHERE rsd.open_price IS NOT NULL 
  AND rsd.close_price IS NOT NULL
  AND rsd.volume IS NOT NULL
ON CONFLICT (stock_id, date_id) 
DO UPDATE SET
    opening_price = EXCLUDED.opening_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    closing_price = EXCLUDED.closing_price,
    volume = EXCLUDED.volume,
    adjusted_close = EXCLUDED.adjusted_close,
    daily_return = EXCLUDED.daily_return,
    updated_at = CURRENT_TIMESTAMP;

-- Step 6: Provide summary of loaded data
SELECT 
    'Stock data loading completed' as status,
    COUNT(*) as records_processed,
    MIN(data_date) as earliest_date,
    MAX(data_date) as latest_date,
    COUNT(DISTINCT symbol) as symbols_processed
FROM raw_stock_data
WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '1 hour');
