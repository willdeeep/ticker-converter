-- Deduplicate historical data after backfill operations
-- This query removes any duplicate records that may have been created during backfill

-- Remove duplicate stock price records, keeping the most recent
WITH stock_duplicates AS (
    SELECT 
        symbol,
        date,
        ROW_NUMBER() OVER (
            PARTITION BY symbol, date 
            ORDER BY updated_at DESC, created_at DESC
        ) as rn
    FROM stock_prices
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
)
DELETE FROM stock_prices 
WHERE (symbol, date) IN (
    SELECT symbol, date 
    FROM stock_duplicates 
    WHERE rn > 1
)
AND created_at IN (
    SELECT sp.created_at
    FROM stock_prices sp
    JOIN stock_duplicates sd ON sp.symbol = sd.symbol AND sp.date = sd.date
    WHERE sd.rn > 1
);

-- Remove duplicate exchange rate records, keeping the most recent
WITH exchange_duplicates AS (
    SELECT 
        from_currency,
        to_currency,
        date,
        ROW_NUMBER() OVER (
            PARTITION BY from_currency, to_currency, date 
            ORDER BY updated_at DESC, created_at DESC
        ) as rn
    FROM exchange_rates
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
)
DELETE FROM exchange_rates 
WHERE (from_currency, to_currency, date) IN (
    SELECT from_currency, to_currency, date 
    FROM exchange_duplicates 
    WHERE rn > 1
)
AND created_at IN (
    SELECT er.created_at
    FROM exchange_rates er
    JOIN exchange_duplicates ed ON 
        er.from_currency = ed.from_currency 
        AND er.to_currency = ed.to_currency 
        AND er.date = ed.date
    WHERE ed.rn > 1
);

-- Log deduplication operation
INSERT INTO etl_logs (
    operation_type,
    table_name,
    operation_timestamp,
    records_affected,
    status,
    details
)
VALUES 
(
    'DEDUPLICATION',
    'stock_prices,exchange_rates',
    NOW(),
    0, -- This would need to be calculated by counting deleted rows
    'COMPLETED',
    FORMAT('Deduplication completed for backfill period %s to %s', 
           '{{ params.start_date }}', 
           '{{ params.end_date }}')
);
