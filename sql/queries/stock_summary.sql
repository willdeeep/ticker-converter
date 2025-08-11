-- Daily Stock Summary Statistics
-- Used by FastAPI endpoint: /api/summary

SELECT 
    dd.date_value as summary_date,
    COUNT(fsp.stock_id) as stocks_count,
    ROUND(AVG(fsp.closing_price), 4) as avg_closing_price_usd,
    ROUND(MIN(fsp.closing_price), 4) as min_closing_price_usd,
    ROUND(MAX(fsp.closing_price), 4) as max_closing_price_usd,
    ROUND(AVG(fsp.daily_return), 6) as avg_daily_return_pct,
    ROUND(MIN(fsp.daily_return), 6) as min_daily_return_pct,
    ROUND(MAX(fsp.daily_return), 6) as max_daily_return_pct,
    SUM(fsp.volume) as total_volume,
    ROUND(AVG(fsp.volume), 0) as avg_volume,
    -- GBP summary if exchange rate available
    ROUND(AVG(fsp.closing_price * COALESCE(fcr.exchange_rate, 1)), 4) as avg_closing_price_gbp,
    fcr.exchange_rate as usd_to_gbp_rate
FROM fact_stock_prices fsp
JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
JOIN dim_date dd ON fsp.date_id = dd.date_id
LEFT JOIN fact_currency_rates fcr ON fcr.date_id = dd.date_id
    AND fcr.from_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'GBP')
WHERE ds.is_active = TRUE
AND dd.date_value >= CURRENT_DATE - INTERVAL '30 days'  -- Last 30 days
GROUP BY dd.date_value, fcr.exchange_rate
ORDER BY dd.date_value DESC
LIMIT 30;
