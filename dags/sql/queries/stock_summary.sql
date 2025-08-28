-- Daily Stock Summary Statistics
-- Used by FastAPI endpoint: /api/summary

SELECT
    dd.date_value AS summary_date,
    fcr.exchange_rate AS usd_to_gbp_rate,
    COUNT(fsp.stock_id) AS stocks_count,
    SUM(fsp.volume) AS total_volume,
    ROUND(AVG(fsp.closing_price), 4) AS avg_closing_price_usd,
    ROUND(MIN(fsp.closing_price), 4) AS min_closing_price_usd,
    ROUND(MAX(fsp.closing_price), 4) AS max_closing_price_usd,
    ROUND(AVG(fsp.daily_return), 6) AS avg_daily_return_pct,
    ROUND(MIN(fsp.daily_return), 6) AS min_daily_return_pct,
    ROUND(MAX(fsp.daily_return), 6) AS max_daily_return_pct,
    ROUND(AVG(fsp.volume), 0) AS avg_volume,
    -- GBP summary if exchange rate available
    ROUND(AVG(fsp.closing_price * COALESCE(fcr.exchange_rate, 1)), 4) AS avg_closing_price_gbp
FROM fact_stock_prices AS fsp
    INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
    INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
    LEFT JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
WHERE fcr.from_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'GBP')
    AND ds.is_active = TRUE
    AND dd.date_value >= CURRENT_DATE - INTERVAL '30 days'  -- Last 30 days
GROUP BY dd.date_value, fcr.exchange_rate
ORDER BY dd.date_value DESC
LIMIT 30;
