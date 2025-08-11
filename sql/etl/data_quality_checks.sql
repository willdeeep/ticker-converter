-- Data Quality Checks for ETL Pipeline
-- Validation queries to ensure data integrity

-- Check 1: Verify no duplicate stock prices for same stock/date
SELECT 
    'Duplicate stock prices' as check_name,
    COUNT(*) as violation_count,
    'CRITICAL' as severity
FROM (
    SELECT stock_id, date_id, COUNT(*)
    FROM fact_stock_prices
    GROUP BY stock_id, date_id
    HAVING COUNT(*) > 1
) duplicates
UNION ALL

-- Check 2: Verify no negative stock prices
SELECT 
    'Negative stock prices' as check_name,
    COUNT(*) as violation_count,
    'CRITICAL' as severity
FROM fact_stock_prices
WHERE opening_price <= 0 OR high_price <= 0 OR low_price <= 0 OR closing_price <= 0
UNION ALL

-- Check 3: Verify price relationships (high >= low, etc.)
SELECT 
    'Invalid price relationships' as check_name,
    COUNT(*) as violation_count,
    'CRITICAL' as severity
FROM fact_stock_prices
WHERE high_price < low_price 
   OR closing_price > high_price 
   OR closing_price < low_price
   OR opening_price > high_price 
   OR opening_price < low_price
UNION ALL

-- Check 4: Verify reasonable daily returns (within -50% to +50%)
SELECT 
    'Extreme daily returns' as check_name,
    COUNT(*) as violation_count,
    'WARNING' as severity
FROM fact_stock_prices
WHERE daily_return < -50 OR daily_return > 50
UNION ALL

-- Check 5: Verify currency rates are positive
SELECT 
    'Invalid currency rates' as check_name,
    COUNT(*) as violation_count,
    'CRITICAL' as severity
FROM fact_currency_rates
WHERE exchange_rate <= 0
UNION ALL

-- Check 6: Verify recent data availability (within last 7 days)
SELECT 
    'Missing recent data' as check_name,
    CASE WHEN MAX(dd.date_value) < CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END as violation_count,
    'WARNING' as severity
FROM fact_stock_prices fsp
JOIN dim_date dd ON fsp.date_id = dd.date_id
UNION ALL

-- Check 7: Verify all Magnificent Seven stocks have data
SELECT 
    'Missing stock data' as check_name,
    (7 - COUNT(DISTINCT ds.symbol)) as violation_count,
    'WARNING' as severity
FROM dim_stocks ds
JOIN fact_stock_prices fsp ON ds.stock_id = fsp.stock_id
JOIN dim_date dd ON fsp.date_id = dd.date_id
WHERE ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
AND dd.date_value >= CURRENT_DATE - INTERVAL '30 days';

-- Summary quality score
SELECT 
    'OVERALL_QUALITY_SCORE' as metric_name,
    CASE 
        WHEN critical_issues.count > 0 THEN 0.0
        WHEN warning_issues.count > 5 THEN 0.7
        WHEN warning_issues.count > 0 THEN 0.9
        ELSE 1.0
    END as quality_score
FROM 
    (SELECT COUNT(*) as count FROM fact_stock_prices WHERE opening_price <= 0 OR high_price <= 0 OR low_price <= 0 OR closing_price <= 0) critical_issues,
    (SELECT COUNT(*) as count FROM fact_stock_prices WHERE daily_return < -50 OR daily_return > 50) warning_issues;
