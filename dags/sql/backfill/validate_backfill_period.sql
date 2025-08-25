-- Validate backfill period and check for existing data
-- This query validates the requested backfill period and identifies any existing data

WITH backfill_validation AS (
    SELECT 
        '{{ params.start_date }}' AS requested_start_date,
        '{{ params.end_date }}' AS requested_end_date,
        CURRENT_DATE AS validation_date,
        CASE 
            WHEN '{{ params.start_date }}'::date >= CURRENT_DATE THEN 'ERROR: Start date cannot be in the future'
            WHEN '{{ params.end_date }}'::date > CURRENT_DATE THEN 'ERROR: End date cannot be in the future' 
            WHEN '{{ params.start_date }}'::date >= '{{ params.end_date }}'::date THEN 'ERROR: Start date must be before end date'
            ELSE 'VALID'
        END AS validation_status,
        ('{{ params.end_date }}'::date - '{{ params.start_date }}'::date) AS backfill_days
),
existing_data_check AS (
    SELECT 
        COUNT(*) AS existing_stock_records,
        MIN(date) AS earliest_stock_date,
        MAX(date) AS latest_stock_date
    FROM stock_prices 
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
existing_exchange_check AS (
    SELECT 
        COUNT(*) AS existing_exchange_records,
        MIN(date) AS earliest_exchange_date,
        MAX(date) AS latest_exchange_date  
    FROM exchange_rates
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
)
SELECT 
    bv.*,
    edc.existing_stock_records,
    edc.earliest_stock_date,
    edc.latest_stock_date,
    eec.existing_exchange_records,
    eec.earliest_exchange_date,
    eec.latest_exchange_date,
    CASE 
        WHEN bv.validation_status != 'VALID' THEN bv.validation_status
        WHEN edc.existing_stock_records > 0 OR eec.existing_exchange_records > 0 THEN 'WARNING: Existing data found in range'
        ELSE 'READY_FOR_BACKFILL'
    END AS final_status
FROM backfill_validation bv
CROSS JOIN existing_data_check edc
CROSS JOIN existing_exchange_check eec;
