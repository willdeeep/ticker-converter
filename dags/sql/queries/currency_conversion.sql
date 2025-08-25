-- USD to GBP Price Conversion
-- Used by FastAPI endpoint: /api/currency/convert

SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value AS rate_date,
    fsp.closing_price AS price_usd,
    fcr.exchange_rate AS usd_to_gbp_rate,
    ROUND(fsp.closing_price * fcr.exchange_rate, 4) AS price_gbp
FROM fact_stock_prices AS fsp
    INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
    INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
    INNER JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
WHERE fcr.from_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
        WHERE dc.currency_code = 'GBP')
    AND dd.date_value = (
        SELECT MAX(dd2.date_value)
        FROM dim_date AS dd2
            INNER JOIN fact_currency_rates AS fcr2 ON dd2.date_id = fcr2.date_id
        WHERE fcr2.from_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
                WHERE dc.currency_code = 'USD')
            AND fcr2.to_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
                WHERE dc.currency_code = 'GBP')
    )
    AND ds.is_active = TRUE
    AND ($1 IS NULL OR ds.symbol = $1)  -- Optional parameter: specific symbol
ORDER BY ds.symbol;
