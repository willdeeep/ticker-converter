-- Top 5 Stock Performers by Daily Return
-- Used by FastAPI endpoint: /api/top-performers

SELECT 
    ds.symbol,
    ds.company_name,
    fsp.closing_price as price_usd,
    ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, 1), 4) as price_gbp,
    fsp.daily_return,
    fsp.volume,
    dd.date_value as trade_date,
    RANK() OVER (ORDER BY fsp.daily_return DESC) as performance_rank
FROM fact_stock_prices fsp
JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
JOIN dim_date dd ON fsp.date_id = dd.date_id
LEFT JOIN fact_currency_rates fcr ON fcr.date_id = dd.date_id
    AND fcr.from_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'GBP')
WHERE dd.date_value = (
    SELECT MAX(date_value) 
    FROM dim_date dd2 
    JOIN fact_stock_prices fsp2 ON dd2.date_id = fsp2.date_id
)
AND ds.is_active = TRUE
AND fsp.daily_return IS NOT NULL
ORDER BY fsp.daily_return DESC
LIMIT 5;
