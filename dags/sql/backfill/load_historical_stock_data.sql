-- Load historical stock data from JSON files into staging table
-- This query processes backfill JSON files and loads them into the database

-- Create temporary staging table for historical stock data
CREATE TEMP TABLE IF NOT EXISTS historical_stock_staging (
    symbol VARCHAR(10),
    date DATE,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    adjusted_close DECIMAL(10,2),
    backfill_timestamp TIMESTAMP,
    source_file VARCHAR(255)
);

-- Note: The actual JSON file processing would need to be implemented
-- using a Python task or COPY command depending on the PostgreSQL setup
-- This is a template for the SQL operations needed

-- Insert historical data into main stock_prices table
INSERT INTO stock_prices (
    symbol,
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    adjusted_close,
    created_at,
    updated_at
)
SELECT
    symbol,
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    adjusted_close,
    backfill_timestamp,
    backfill_timestamp
FROM historical_stock_staging
WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
ON CONFLICT (symbol, date) DO UPDATE SET
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume,
    adjusted_close = EXCLUDED.adjusted_close,
    updated_at = EXCLUDED.updated_at;

-- Log backfill operation
INSERT INTO etl_logs (
    operation_type,
    table_name,
    operation_timestamp,
    records_affected,
    status,
    details
)
SELECT
    'BACKFILL' as operation_type,
    'stock_prices' as table_name,
    NOW() as operation_timestamp,
    COUNT(*) as records_affected,
    'COMPLETED' as status,
    FORMAT('Historical stock data backfill for %s to %s',
           '{{ params.start_date }}',
           '{{ params.end_date }}') as details
FROM historical_stock_staging;
