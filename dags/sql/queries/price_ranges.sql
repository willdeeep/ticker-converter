-- Stock Filtering by Price Range
-- Used by FastAPI endpoint: /api/stocks/price-range

SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value AS trade_date,
    fsp.closing_price AS price_usd,
    fsp.daily_return,
    fsp.volume,
    fsp.opening_price,
    fsp.high_price,
    fsp.low_price,
    ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, 1), 4) AS price_gbp
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
    AND fsp.closing_price BETWEEN $1 AND $2  -- Parameters: min_price, max_price
ORDER BY fsp.closing_price DESC;
