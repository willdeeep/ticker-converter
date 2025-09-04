-- Stock Data with USD/GBP Currency Conversion
-- Used by FastAPI endpoint: /api/stocks/data-with-currency
-- Returns stock data with side-by-side USD and GBP prices based on the day's exchange rate

SELECT
    ds.symbol,
    ds.company_name,
    dd.date_value AS trade_date,
    fsp.closing_price AS price_usd,
    fcr.exchange_rate AS usd_to_gbp_rate,
    fsp.volume,
    fsp.daily_return,
    ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, NULL), 4) AS price_gbp,
    -- Calculate market cap if shares outstanding is available
    CASE
        WHEN fsp.shares_outstanding IS NOT NULL
        THEN ROUND(fsp.closing_price * fsp.shares_outstanding, 2)
    END AS market_cap_usd,
    CASE
        WHEN fsp.shares_outstanding IS NOT NULL AND fcr.exchange_rate IS NOT NULL
        THEN ROUND(fsp.closing_price * fsp.shares_outstanding * fcr.exchange_rate, 2)
    END AS market_cap_gbp
FROM fact_stock_prices AS fsp
    INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
    INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
    LEFT JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
        AND fcr.from_currency_id = (
            SELECT dc.currency_id
            FROM dim_currency AS dc
            WHERE dc.currency_code = 'USD'
        )
        AND fcr.to_currency_id = (
            SELECT dc.currency_id
            FROM dim_currency AS dc
            WHERE dc.currency_code = 'GBP'
        )
WHERE
    ds.is_active = TRUE
    AND ($1 IS NULL OR ds.symbol = $1)  -- Optional parameter: specific symbol
    AND ($2 IS NULL OR dd.date_value = $2)  -- Optional parameter: specific date
ORDER BY dd.date_value DESC, ds.symbol ASC;
