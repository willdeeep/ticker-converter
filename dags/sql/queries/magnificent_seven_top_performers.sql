-- Top 3 Magnificent Seven Stock Performers
-- Used by FastAPI endpoint: /api/stocks/top-performers

SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value AS trade_date,
    fsp.closing_price AS price_usd,
    fsp.daily_return,
    fsp.volume,
    ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, 1), 4) AS price_gbp,
    RANK() OVER (ORDER BY fsp.daily_return DESC) AS performance_rank
FROM fact_stock_prices AS fsp
    INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
    INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
    LEFT JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
WHERE fcr.from_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'GBP')
    AND dd.date_value = (
        SELECT MAX(dd2.date_value)
        FROM dim_date AS dd2
            INNER JOIN fact_stock_prices AS fsp2 ON dd2.date_id = fsp2.date_id
    )
    AND ds.is_active = TRUE
    AND fsp.daily_return IS NOT NULL
    -- Filter for Magnificent Seven companies only
    AND ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
ORDER BY fsp.daily_return DESC
LIMIT 3;
