-- Data Quality Checks for ETL Pipeline
-- Validation queries to ensure data integrity

-- Check 1: Verify no duplicate stock prices for same stock/date
SELECT
    'Duplicate stock prices' AS check_name,
    COUNT(*) AS violation_count,
    'CRITICAL' AS severity
FROM (
    SELECT
        stock_id,
        date_id,
        COUNT(*) AS row_count
    FROM fact_stock_prices
    GROUP BY stock_id, date_id
    HAVING COUNT(*) > 1
) AS duplicates
UNION ALL

-- Check 2: Verify no negative stock prices
SELECT
    'Negative stock prices' AS check_name,
    COUNT(*) AS violation_count,
    'CRITICAL' AS severity
FROM fact_stock_prices
WHERE opening_price <= 0 OR high_price <= 0 OR low_price <= 0 OR closing_price <= 0
UNION ALL

-- Check 3: Verify price relationships (high >= low, etc.)
SELECT
    'Invalid price relationships' AS check_name,
    COUNT(*) AS violation_count,
    'CRITICAL' AS severity
FROM fact_stock_prices
WHERE high_price < low_price
   OR closing_price > high_price
   OR closing_price < low_price
   OR opening_price > high_price
   OR opening_price < low_price
UNION ALL

-- Check 4: Verify reasonable daily returns (within -50% to +50%)
SELECT
    'Extreme daily returns' AS check_name,
    COUNT(*) AS violation_count,
    'WARNING' AS severity
FROM fact_stock_prices
WHERE daily_return < -50 OR daily_return > 50
UNION ALL

-- Check 5: Verify currency rates are positive
SELECT
    'Invalid currency rates' AS check_name,
    COUNT(*) AS violation_count,
    'CRITICAL' AS severity
FROM fact_currency_rates
WHERE exchange_rate <= 0
UNION ALL

-- Check 6: Verify recent data availability (within last 7 days)
SELECT
    'Missing recent data' AS check_name,
    CASE WHEN MAX(dd.date_value) < CURRENT_DATE - INTERVAL '7 days' THEN 1 ELSE 0 END AS violation_count,
    'WARNING' AS severity
FROM fact_stock_prices AS fsp
INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
UNION ALL

-- Check 7: Verify all Magnificent Seven stocks have data
SELECT
    'Missing stock data' AS check_name,
    (7 - COUNT(DISTINCT ds.symbol)) AS violation_count,
    'WARNING' AS severity
FROM dim_stocks AS ds
INNER JOIN fact_stock_prices AS fsp ON ds.stock_id = fsp.stock_id
INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
WHERE ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
AND dd.date_value >= CURRENT_DATE - INTERVAL '30 days';

-- Summary quality score
SELECT
    'OVERALL_QUALITY_SCORE' AS metric_name,
    CASE
        WHEN critical_issues.count > 0 THEN 0.0
        WHEN warning_issues.count > 5 THEN 0.7
        WHEN warning_issues.count > 0 THEN 0.9
        ELSE 1.0
    END AS quality_score
FROM
    (SELECT COUNT(*) AS count FROM fact_stock_prices
WHERE opening_price <= 0 OR high_price <= 0 OR low_price <= 0 OR closing_price <= 0) AS critical_issues,
    (SELECT COUNT(*) AS count FROM fact_stock_prices
WHERE daily_return < -50 OR daily_return > 50) AS warning_issues;
