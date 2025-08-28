-- Generate comprehensive backfill completion report
-- This query creates a detailed report of the backfill operation

WITH backfill_summary AS (
    SELECT
        '{{ params.start_date }}' AS backfill_start_date,  -- noqa: TMP
        '{{ params.end_date }}' AS backfill_end_date,      -- noqa: TMP
        NOW() AS report_generated_at,
        ('{{ params.end_date }}'::date - '{{ params.start_date }}'::date) AS backfill_period_days  -- noqa: TMP
),

stock_summary AS (
    SELECT
        COUNT(*) AS total_stock_records,
        COUNT(DISTINCT symbol) AS symbols_loaded,
        COUNT(DISTINCT date) AS trading_days_loaded,
        MIN(date) AS first_trading_date,
        MAX(date) AS last_trading_date,
        ROUND(AVG(volume)) AS avg_daily_volume,
        ROUND(AVG(close_price), 2) AS avg_close_price
    FROM stock_prices AS sp
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date  -- noqa: TMP
),

exchange_summary AS (
    SELECT
        COUNT(*) AS total_exchange_records,
        COUNT(DISTINCT from_currency || '-' || to_currency) AS currency_pairs_loaded,
        COUNT(DISTINCT date) AS exchange_days_loaded,
        MIN(date) AS first_exchange_date,
        MAX(date) AS last_exchange_date,
        ROUND(AVG(rate), 4) AS avg_exchange_rate
    FROM exchange_rates AS er
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date  -- noqa: TMP
),

data_quality_summary AS (
    SELECT
        sp.close_price,
        sp.volume,
        er.rate
    FROM stock_prices AS sp
    FULL OUTER JOIN exchange_rates AS er ON sp.date = er.date
    WHERE sp.date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date  -- noqa: TMP
       OR er.date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date  -- noqa: TMP
),

quality_checks AS (
    SELECT
        CASE
            WHEN COUNT(CASE WHEN close_price <= 0 OR volume < 0 THEN 1 END) = 0
            THEN 'PASSED'
            ELSE 'FAILED'
        END AS stock_quality_check,
        COUNT(CASE WHEN close_price <= 0 OR volume < 0 THEN 1 END) AS stock_quality_issues,
        CASE
            WHEN COUNT(CASE WHEN rate <= 0 THEN 1 END) = 0
            THEN 'PASSED'
            ELSE 'FAILED'
        END AS exchange_quality_check,
        COUNT(CASE WHEN rate <= 0 THEN 1 END) AS exchange_quality_issues
    FROM data_quality_summary AS dqs
),

etl_log_summary AS (
    SELECT
        COUNT(*) AS backfill_operations,
        SUM(records_affected) AS total_records_processed,
        STRING_AGG(DISTINCT status, ', ') AS operation_statuses
    FROM etl_logs AS els
    WHERE operation_type = 'BACKFILL'
      AND operation_timestamp >= CURRENT_DATE
      AND details LIKE '%{{ params.start_date }}%'  -- noqa: TMP
)

SELECT
    -- Backfill Overview
    bs.backfill_start_date,
    bs.backfill_end_date,
    bs.backfill_period_days,
    bs.report_generated_at,

    -- Stock Data Summary
    ss.total_stock_records,
    ss.symbols_loaded,
    ss.trading_days_loaded,
    ss.first_trading_date,
    ss.last_trading_date,
    ss.avg_daily_volume,
    ss.avg_close_price,

    -- Exchange Data Summary
    es.total_exchange_records,
    es.currency_pairs_loaded,
    es.exchange_days_loaded,
    es.first_exchange_date,
    es.last_exchange_date,
    es.avg_exchange_rate,

    -- Data Quality Results
    qc.stock_quality_check,
    qc.stock_quality_issues,
    qc.exchange_quality_check,
    qc.exchange_quality_issues,

    -- ETL Operations Summary
    els.backfill_operations,
    els.total_records_processed,
    els.operation_statuses,

    -- Overall Status
    CASE
        WHEN qc.stock_quality_check = 'PASSED'
         AND qc.exchange_quality_check = 'PASSED'
         AND ss.total_stock_records > 0
         AND es.total_exchange_records > 0
        THEN 'SUCCESS'
        WHEN qc.stock_quality_check = 'FAILED'
          OR qc.exchange_quality_check = 'FAILED'
        THEN 'COMPLETED_WITH_QUALITY_ISSUES'
        WHEN ss.total_stock_records = 0
          OR es.total_exchange_records = 0
        THEN 'COMPLETED_WITH_MISSING_DATA'
        ELSE 'UNKNOWN'
    END AS backfill_status,

    -- Recommendations
    CASE
        WHEN qc.stock_quality_issues > 0 OR qc.exchange_quality_issues > 0
        THEN 'Review data quality issues and consider re-running backfill for affected periods'
        WHEN ss.symbols_loaded < 7
        THEN 'Some expected symbols may be missing - verify data sources'
        WHEN ss.trading_days_loaded < (bs.backfill_period_days * 0.7)
        THEN 'Lower than expected trading days loaded - check for weekends/holidays'
        ELSE 'Backfill completed successfully - no action required'
    END AS recommendations

FROM backfill_summary AS bs
CROSS JOIN stock_summary AS ss
CROSS JOIN exchange_summary AS es
CROSS JOIN quality_checks AS qc
CROSS JOIN etl_log_summary AS els;
