-- Daily Transform: Load fact tables and calculate performance metrics
-- Transforms raw data into dimensional model with currency conversion

-- Load stock price facts from raw data
INSERT INTO fact_stock_prices (
    stock_id, 
    date_id, 
    opening_price, 
    high_price, 
    low_price, 
    closing_price, 
    volume,
    daily_return
)
SELECT 
    ds.stock_id,
    dd.date_id,
    rsd.open_price,
    rsd.high_price,
    rsd.low_price,
    rsd.close_price,
    rsd.volume,
    -- Calculate daily return (percentage change from previous day)
    CASE 
        WHEN LAG(rsd.close_price) OVER (PARTITION BY rsd.symbol ORDER BY rsd.data_date) IS NOT NULL
        THEN ROUND(
            ((rsd.close_price - LAG(rsd.close_price) OVER (PARTITION BY rsd.symbol ORDER BY rsd.data_date)) 
             / LAG(rsd.close_price) OVER (PARTITION BY rsd.symbol ORDER BY rsd.data_date)) * 100, 
            6
        )
        ELSE NULL
    END as daily_return
FROM raw_stock_data rsd
JOIN dim_stocks ds ON rsd.symbol = ds.symbol
JOIN dim_date dd ON rsd.data_date = dd.date_value
WHERE NOT EXISTS (
    SELECT 1 FROM fact_stock_prices fsp 
    WHERE fsp.stock_id = ds.stock_id AND fsp.date_id = dd.date_id
);

-- Load currency rate facts from raw data
INSERT INTO fact_currency_rates (
    from_currency_id,
    to_currency_id,
    date_id,
    exchange_rate
)
SELECT 
    dc_from.currency_id as from_currency_id,
    dc_to.currency_id as to_currency_id,
    dd.date_id,
    rcd.exchange_rate
FROM raw_currency_data rcd
JOIN dim_currency dc_from ON rcd.from_currency = dc_from.currency_code
JOIN dim_currency dc_to ON rcd.to_currency = dc_to.currency_code
JOIN dim_date dd ON rcd.data_date = dd.date_value
WHERE NOT EXISTS (
    SELECT 1 FROM fact_currency_rates fcr 
    WHERE fcr.from_currency_id = dc_from.currency_id 
    AND fcr.to_currency_id = dc_to.currency_id 
    AND fcr.date_id = dd.date_id
);

-- Update daily returns for existing records where missing
UPDATE fact_stock_prices 
SET daily_return = subq.calculated_return,
    updated_at = CURRENT_TIMESTAMP
FROM (
    SELECT 
        fsp.price_id,
        CASE 
            WHEN LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value) IS NOT NULL
            THEN ROUND(
                ((fsp.closing_price - LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value)) 
                 / LAG(fsp.closing_price) OVER (PARTITION BY fsp.stock_id ORDER BY dd.date_value)) * 100, 
                6
            )
            ELSE NULL
        END as calculated_return
    FROM fact_stock_prices fsp
    JOIN dim_date dd ON fsp.date_id = dd.date_id
    WHERE fsp.daily_return IS NULL
) subq
WHERE fact_stock_prices.price_id = subq.price_id
AND subq.calculated_return IS NOT NULL;
