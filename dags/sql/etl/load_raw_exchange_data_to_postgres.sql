-- Load raw exchange rate data from JSON files to dimensional model
-- This query processes JSON files from dags/raw_data/exchange/ and loads them into the star schema

-- Step 1: Create temporary table for JSON processing
DROP TABLE IF EXISTS temp_json_exchange_data;
CREATE TEMP TABLE temp_json_exchange_data (
    json_data JSONB
);

-- Step 2: Load JSON data from files (this will be populated by Python in the DAG)
-- Note: The actual file loading is handled by the Python operator that calls this SQL

-- Step 3: Insert into raw_currency_data staging table
INSERT INTO raw_currency_data (
    from_currency,
    to_currency,
    data_date,
    exchange_rate,
    source,
    created_at
)
SELECT 
    (json_data->>'from_currency')::VARCHAR(3) as from_currency,
    (json_data->>'to_currency')::VARCHAR(3) as to_currency,
    (json_data->>'data_date')::DATE as data_date,
    (json_data->>'exchange_rate')::DECIMAL(10,6) as exchange_rate,
    COALESCE(json_data->>'source', 'alpha_vantage') as source,
    COALESCE(
        (json_data->>'created_at')::TIMESTAMP,
        CURRENT_TIMESTAMP
    ) as created_at
FROM temp_json_exchange_data
ON CONFLICT (from_currency, to_currency, data_date, source) 
DO UPDATE SET
    exchange_rate = EXCLUDED.exchange_rate,
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
FROM raw_currency_data
WHERE data_date IS NOT NULL
ON CONFLICT (date_value) DO NOTHING;

-- Step 5: Load currency codes into dim_currency if they don't exist
INSERT INTO dim_currency (currency_code, currency_name, is_base_currency, is_active)
SELECT DISTINCT
    from_currency as currency_code,
    CASE 
        WHEN from_currency = 'USD' THEN 'US Dollar'
        WHEN from_currency = 'GBP' THEN 'British Pound'
        WHEN from_currency = 'EUR' THEN 'Euro'
        WHEN from_currency = 'JPY' THEN 'Japanese Yen'
        WHEN from_currency = 'CAD' THEN 'Canadian Dollar'
        WHEN from_currency = 'AUD' THEN 'Australian Dollar'
        ELSE from_currency || ' Currency'
    END as currency_name,
    CASE WHEN from_currency = 'USD' THEN TRUE ELSE FALSE END as is_base_currency,
    TRUE as is_active
FROM raw_currency_data
WHERE from_currency IS NOT NULL
UNION
SELECT DISTINCT
    to_currency as currency_code,
    CASE 
        WHEN to_currency = 'USD' THEN 'US Dollar'
        WHEN to_currency = 'GBP' THEN 'British Pound'
        WHEN to_currency = 'EUR' THEN 'Euro'
        WHEN to_currency = 'JPY' THEN 'Japanese Yen'
        WHEN to_currency = 'CAD' THEN 'Canadian Dollar'
        WHEN to_currency = 'AUD' THEN 'Australian Dollar'
        ELSE to_currency || ' Currency'
    END as currency_name,
    CASE WHEN to_currency = 'USD' THEN TRUE ELSE FALSE END as is_base_currency,
    TRUE as is_active
FROM raw_currency_data
WHERE to_currency IS NOT NULL
ON CONFLICT (currency_code) DO NOTHING;

-- Step 6: Load exchange rates into fact_currency_rates
INSERT INTO fact_currency_rates (
    from_currency_id,
    to_currency_id,
    date_id,
    exchange_rate
)
SELECT 
    dc_from.currency_id as from_currency_id,
    dc_to.currency_id as to_currency_id,
    dd.date_id,
    rcd.exchange_rate
FROM raw_currency_data rcd
JOIN dim_currency dc_from ON rcd.from_currency = dc_from.currency_code
JOIN dim_currency dc_to ON rcd.to_currency = dc_to.currency_code
JOIN dim_date dd ON rcd.data_date = dd.date_value
WHERE rcd.exchange_rate IS NOT NULL
ON CONFLICT (from_currency_id, to_currency_id, date_id) 
DO UPDATE SET
    exchange_rate = EXCLUDED.exchange_rate,
    updated_at = CURRENT_TIMESTAMP;

-- Step 7: Provide summary of loaded data
SELECT 
    'Exchange rate data loading completed' as status,
    COUNT(*) as records_processed,
    MIN(data_date) as earliest_date,
    MAX(data_date) as latest_date,
    COUNT(DISTINCT from_currency || '-' || to_currency) as currency_pairs_processed
FROM raw_currency_data
WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '1 hour');
