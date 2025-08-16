-- Detailed Performance Metrics for Magnificent Seven
-- Used by FastAPI endpoint: /api/stocks/performance-details

WITH latest_date AS (
    SELECT MAX(dd.date_value) as latest_trading_date
    FROM dim_date dd
    JOIN fact_stock_prices fsp ON dd.date_id = fsp.date_id
),
stock_metrics AS (
    SELECT 
        ds.symbol,
        ds.company_name,
        fsp.closing_price as price_usd,
        ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, 1), 4) as price_gbp,
        ROUND(fsp.daily_return, 4) as daily_return,
        fsp.volume,
        dd.date_value as trade_date,
        -- 30-day metrics
        AVG(fsp.closing_price) OVER (
            PARTITION BY ds.symbol 
            ORDER BY dd.date_value 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as avg_price_30d,
        AVG(fsp.volume) OVER (
            PARTITION BY ds.symbol 
            ORDER BY dd.date_value 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as avg_volume_30d,
        -- Price change over 30 days
        LAG(fsp.closing_price, 30) OVER (
            PARTITION BY ds.symbol 
            ORDER BY dd.date_value
        ) as price_30d_ago,
        -- Volatility (standard deviation of returns)
        STDDEV(fsp.daily_return) OVER (
            PARTITION BY ds.symbol 
            ORDER BY dd.date_value 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as volatility_30d,
        -- Performance rank
        RANK() OVER (ORDER BY fsp.daily_return DESC) as performance_rank
    FROM fact_stock_prices fsp
    JOIN dim_stocks ds ON fsp.stock_id = ds.stock_id
    JOIN dim_date dd ON fsp.date_id = dd.date_id
    LEFT JOIN fact_currency_rates fcr ON fcr.date_id = dd.date_id
        AND fcr.from_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'USD')
        AND fcr.to_currency_id = (SELECT currency_id FROM dim_currency WHERE currency_code = 'GBP')
    WHERE ds.is_active = TRUE
    AND ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
)
SELECT 
    sm.symbol,
    sm.company_name,
    sm.price_usd,
    sm.price_gbp,
    sm.daily_return,
    sm.volume,
    sm.trade_date,
    ROUND(sm.avg_price_30d, 4) as avg_price_30d_usd,
    ROUND(sm.avg_volume_30d::bigint) as avg_volume_30d,
    CASE 
        WHEN sm.price_30d_ago IS NOT NULL AND sm.price_30d_ago > 0 
        THEN ROUND(((sm.price_usd - sm.price_30d_ago) / sm.price_30d_ago * 100), 4)
        ELSE NULL 
    END as price_change_30d_pct,
    ROUND(sm.volatility_30d, 6) as volatility_30d,
    sm.performance_rank
FROM stock_metrics sm
JOIN latest_date ld ON sm.trade_date = ld.latest_trading_date
ORDER BY sm.daily_return DESC;
