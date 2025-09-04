-- Load historical exchange rate data from JSON files into staging table
-- This query processes backfill JSON files and loads them into the database

-- Create temporary staging table for historical exchange data
CREATE TEMP TABLE IF NOT EXISTS historical_exchange_staging (
    from_currency VARCHAR(3),
    to_currency VARCHAR(3),
    date DATE,
    exchange_rate DECIMAL(10, 6),
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
    hes.from_currency,
    hes.to_currency,
    hes.date,
    hes.exchange_rate,
    hes.backfill_timestamp,
    hes.backfill_timestamp
FROM historical_exchange_staging AS hes
WHERE hes.date BETWEEN '{{ params.start_date }}'::TIMESTAMP AND '{{ params.end_date }}'::TIMESTAMP
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
    'BACKFILL' AS operation_type,
    'exchange_rates' AS table_name,
    NOW() AS operation_timestamp,
    COUNT(*) AS records_affected,
    'COMPLETED' AS status,
    FORMAT('Historical exchange rate backfill for %s to %s',
           '{{ params.start_date }}',
           '{{ params.end_date }}') AS details
FROM historical_exchange_staging;
