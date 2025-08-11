-- USD to GBP Price Conversion
-- Used by FastAPI endpoint: /api/currency/convert

SELECT 
    ds.symbol,
    ds.company_name,
    fsp.closing_price as price_usd,
    fcr.exchange_rate as usd_to_gbp_rate,
    ROUND(fsp.closing_price * fcr.exchange_rate, 4) as price_gbp,
    dd.date_value as rate_date
FROM fact_stock_prices fsp
JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
JOIN dim_date dd ON fsp.date_id = dd.date_id
JOIN fact_currency_rates fcr ON fcr.date_id = dd.date_id
    AND fcr.from_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'USD')
    AND fcr.to_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'GBP')
WHERE dd.date_value = (
    SELECT MAX(dd2.date_value) 
    FROM dim_date dd2 
    JOIN fact_currency_rates fcr2 ON dd2.date_id = fcr2.date_id
    WHERE fcr2.from_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'USD')
    AND fcr2.to_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'GBP')
)
AND ds.is_active = TRUE
AND ($1 IS NULL OR ds.symbol = $1)  -- Optional parameter: specific symbol
ORDER BY ds.symbol;
