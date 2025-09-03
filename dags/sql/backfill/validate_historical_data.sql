-- Validate historical data quality after backfill
-- This query performs comprehensive validation of backfilled data

-- Stock data validation
WITH stock_validation AS (
    SELECT
        '{{ params.start_date }}' as backfill_start,
        '{{ params.end_date }}' as backfill_end,
        COUNT(*) as total_stock_records,
        COUNT(DISTINCT symbol) as unique_symbols,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,

        -- Data quality checks
        COUNT(CASE WHEN open_price <= 0 THEN 1 END) as invalid_open_prices,
        COUNT(CASE WHEN high_price <= 0 THEN 1 END) as invalid_high_prices,
        COUNT(CASE WHEN low_price <= 0 THEN 1 END) as invalid_low_prices,
        COUNT(CASE WHEN close_price <= 0 THEN 1 END) as invalid_close_prices,
        COUNT(CASE WHEN volume < 0 THEN 1 END) as invalid_volumes,

        -- Logical consistency checks
        COUNT(CASE WHEN high_price < low_price THEN 1 END) as high_less_than_low,
        COUNT(CASE WHEN high_price < open_price THEN 1 END) as high_less_than_open,
        COUNT(CASE WHEN high_price < close_price THEN 1 END) as high_less_than_close,
        COUNT(CASE WHEN low_price > open_price THEN 1 END) as low_greater_than_open,
        COUNT(CASE WHEN low_price > close_price THEN 1 END) as low_greater_than_close

    FROM stock_prices
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
exchange_validation AS (
    SELECT
        COUNT(*) as total_exchange_records,
        COUNT(DISTINCT from_currency) as unique_from_currencies,
        COUNT(DISTINCT to_currency) as unique_to_currencies,
        COUNT(DISTINCT date) as unique_exchange_dates,
        MIN(date) as earliest_exchange_date,
        MAX(date) as latest_exchange_date,

        -- Data quality checks
        COUNT(CASE WHEN rate <= 0 THEN 1 END) as invalid_rates,
        COUNT(CASE WHEN rate > 1000 THEN 1 END) as suspicious_high_rates,
        COUNT(CASE WHEN from_currency = to_currency THEN 1 END) as self_conversions

    FROM exchange_rates
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
expected_symbols AS (
    SELECT unnest(ARRAY['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']) as symbol
),
missing_symbols AS (
    SELECT
        es.symbol,
        CASE WHEN sp.symbol IS NULL THEN 'MISSING' ELSE 'PRESENT' END as status
    FROM expected_symbols es
    LEFT JOIN (
        SELECT DISTINCT symbol
        FROM stock_prices
        WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
    ) sp ON es.symbol = sp.symbol
)
SELECT
    sv.*,
    ev.total_exchange_records,
    ev.unique_from_currencies,
    ev.unique_to_currencies,
    ev.unique_exchange_dates,
    ev.earliest_exchange_date,
    ev.latest_exchange_date,
    ev.invalid_rates,
    ev.suspicious_high_rates,
    ev.self_conversions,

    -- Overall data quality score
    CASE
        WHEN sv.invalid_open_prices + sv.invalid_high_prices + sv.invalid_low_prices +
             sv.invalid_close_prices + sv.invalid_volumes + sv.high_less_than_low +
             sv.high_less_than_open + sv.high_less_than_close + sv.low_greater_than_open +
             sv.low_greater_than_close + ev.invalid_rates + ev.self_conversions = 0
        THEN 'EXCELLENT'
        WHEN sv.invalid_open_prices + sv.invalid_high_prices + sv.invalid_low_prices +
             sv.invalid_close_prices + sv.invalid_volumes + sv.high_less_than_low +
             sv.high_less_than_open + sv.high_less_than_close + sv.low_greater_than_open +
             sv.low_greater_than_close + ev.invalid_rates + ev.self_conversions <= 5
        THEN 'GOOD'
        WHEN sv.invalid_open_prices + sv.invalid_high_prices + sv.invalid_low_prices +
             sv.invalid_close_prices + sv.invalid_volumes + sv.high_less_than_low +
             sv.high_less_than_open + sv.high_less_than_close + sv.low_greater_than_open +
             sv.low_greater_than_close + ev.invalid_rates + ev.self_conversions <= 20
        THEN 'FAIR'
        ELSE 'POOR'
    END as data_quality_score,

    -- Missing symbols summary
    (SELECT string_agg(symbol, ', ') FROM missing_symbols WHERE status = 'MISSING') as missing_symbols,
    (SELECT COUNT(*) FROM missing_symbols WHERE status = 'MISSING') as missing_symbol_count

FROM stock_validation sv
CROSS JOIN exchange_validation ev;
