-- Generate comprehensive backfill completion report
-- This query creates a detailed report of the backfill operation

WITH backfill_summary AS (
    SELECT 
        '{{ params.start_date }}' as backfill_start_date,
        '{{ params.end_date }}' as backfill_end_date,
        NOW() as report_generated_at,
        ('{{ params.end_date }}'::date - '{{ params.start_date }}'::date) as backfill_period_days
),
stock_summary AS (
    SELECT 
        COUNT(*) as total_stock_records,
        COUNT(DISTINCT symbol) as symbols_loaded,
        COUNT(DISTINCT date) as trading_days_loaded,
        MIN(date) as first_trading_date,
        MAX(date) as last_trading_date,
        ROUND(AVG(volume)) as avg_daily_volume,
        ROUND(AVG(close_price), 2) as avg_close_price
    FROM stock_prices 
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
exchange_summary AS (
    SELECT 
        COUNT(*) as total_exchange_records,
        COUNT(DISTINCT from_currency || '-' || to_currency) as currency_pairs_loaded,
        COUNT(DISTINCT date) as exchange_days_loaded,
        MIN(date) as first_exchange_date,
        MAX(date) as last_exchange_date,
        ROUND(AVG(rate), 4) as avg_exchange_rate
    FROM exchange_rates 
    WHERE date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
data_quality_summary AS (
    SELECT 
        CASE 
            WHEN COUNT(CASE WHEN close_price <= 0 OR volume < 0 THEN 1 END) = 0 
            THEN 'PASSED'
            ELSE 'FAILED'
        END as stock_quality_check,
        COUNT(CASE WHEN close_price <= 0 OR volume < 0 THEN 1 END) as stock_quality_issues,
        
        CASE 
            WHEN COUNT(CASE WHEN rate <= 0 THEN 1 END) = 0 
            THEN 'PASSED'
            ELSE 'FAILED' 
        END as exchange_quality_check,
        COUNT(CASE WHEN rate <= 0 THEN 1 END) as exchange_quality_issues
    FROM stock_prices sp
    FULL OUTER JOIN exchange_rates er ON sp.date = er.date
    WHERE sp.date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
       OR er.date BETWEEN '{{ params.start_date }}'::date AND '{{ params.end_date }}'::date
),
etl_log_summary AS (
    SELECT 
        COUNT(*) as backfill_operations,
        SUM(records_affected) as total_records_processed,
        string_agg(DISTINCT status, ', ') as operation_statuses
    FROM etl_logs 
    WHERE operation_type = 'BACKFILL'
      AND operation_timestamp >= CURRENT_DATE
      AND details LIKE '%{{ params.start_date }}%'
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
    dqs.stock_quality_check,
    dqs.stock_quality_issues,
    dqs.exchange_quality_check,
    dqs.exchange_quality_issues,
    
    -- ETL Operations Summary
    els.backfill_operations,
    els.total_records_processed,
    els.operation_statuses,
    
    -- Overall Status
    CASE 
        WHEN dqs.stock_quality_check = 'PASSED' 
         AND dqs.exchange_quality_check = 'PASSED'
         AND ss.total_stock_records > 0
         AND es.total_exchange_records > 0
        THEN 'SUCCESS'
        WHEN dqs.stock_quality_check = 'FAILED' 
          OR dqs.exchange_quality_check = 'FAILED'
        THEN 'COMPLETED_WITH_QUALITY_ISSUES'
        WHEN ss.total_stock_records = 0 
          OR es.total_exchange_records = 0
        THEN 'COMPLETED_WITH_MISSING_DATA'
        ELSE 'UNKNOWN'
    END as backfill_status,
    
    -- Recommendations
    CASE 
        WHEN dqs.stock_quality_issues > 0 OR dqs.exchange_quality_issues > 0
        THEN 'Review data quality issues and consider re-running backfill for affected periods'
        WHEN ss.symbols_loaded < 7
        THEN 'Some expected symbols may be missing - verify data sources'
        WHEN ss.trading_days_loaded < (bs.backfill_period_days * 0.7)
        THEN 'Lower than expected trading days loaded - check for weekends/holidays'
        ELSE 'Backfill completed successfully - no action required'
    END as recommendations

FROM backfill_summary bs
CROSS JOIN stock_summary ss
CROSS JOIN exchange_summary es  
CROSS JOIN data_quality_summary dqs
CROSS JOIN etl_log_summary els;
