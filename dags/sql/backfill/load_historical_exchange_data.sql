-- Load historical exchange rate data from JSON files into staging table
-- This query processes backfill JSON files and loads them into the database

-- Create temporary staging table for historical exchange data
CREATE TEMP TABLE IF NOT EXISTS historical_exchange_staging (
    from_currency VARCHAR(3),
    to_currency VARCHAR(3),
    date DATE,
    exchange_rate DECIMAL(10,6),
    backfill_timestamp TIMESTAMP,
    source_file VARCHAR(255)
);

-- Note: The actual JSON file processing would need to be implemented 
-- using a Python task or COPY command depending on the PostgreSQL setup
-- This is a template for the SQL operations needed

-- Insert historical exchange data into main exchange_rates table
INSERT INTO exchange_rates (
    from_currency,
    to_currency,
    date,
    rate,
    created_at,
    updated_at
)
SELECT 
    from_currency,
    to_currency,
    date,
    exchange_rate,
    backfill_timestamp,
    backfill_timestamp
FROM historical_exchange_staging
WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
ON CONFLICT (from_currency, to_currency, date) DO UPDATE SET
    rate = EXCLUDED.rate,
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
    'exchange_rates' as table_name,
    NOW() as operation_timestamp,
    COUNT(*) as records_affected,
    'COMPLETED' as status,
    FORMAT('Historical exchange rate backfill for %s to %s', 
           '{{ params.start_date }}', 
           '{{ params.end_date }}') as details
FROM historical_exchange_staging;
