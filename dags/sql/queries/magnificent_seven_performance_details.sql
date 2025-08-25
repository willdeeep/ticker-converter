-- Detailed Performance Metrics for Magnificent Seven
-- Used by FastAPI endpoint: /api/stocks/performance-details

WITH latest_date AS (
    SELECT MAX(dd.date_value) AS latest_trading_date
    FROM dim_date AS dd
        INNER JOIN fact_stock_prices AS fsp ON dd.date_id = fsp.date_id
),

stock_metrics AS (
    SELECT
        ds.symbol,
        ds.company_name,
        dd.date_value AS trade_date,
        fsp.closing_price AS price_usd,
        fsp.daily_return,
        fsp.volume,
        ROUND(fsp.closing_price * COALESCE(fcr.exchange_rate, 1), 4) AS price_gbp,
        -- 30-day metrics
        AVG(fsp.closing_price) OVER (
            PARTITION BY ds.symbol
            ORDER BY dd.date_value
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_price_30d,
        AVG(fsp.volume) OVER (
            PARTITION BY ds.symbol
            ORDER BY dd.date_value
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_volume_30d,
        -- Price change over 30 days
        LAG(fsp.closing_price, 30) OVER (
            PARTITION BY ds.symbol
            ORDER BY dd.date_value
        ) AS price_30d_ago,
        -- Volatility (standard deviation of returns)
        STDDEV(fsp.daily_return) OVER (
            PARTITION BY ds.symbol
            ORDER BY dd.date_value
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS volatility_30d,
        -- Performance rank
        RANK() OVER (ORDER BY fsp.daily_return DESC) AS performance_rank
    FROM fact_stock_prices AS fsp
        INNER JOIN dim_stocks AS ds ON fsp.stock_id = ds.stock_id
        INNER JOIN dim_date AS dd ON fsp.date_id = dd.date_id
        LEFT JOIN fact_currency_rates AS fcr ON dd.date_id = fcr.date_id
    WHERE fcr.from_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
            WHERE dc.currency_code = 'USD')
        AND fcr.to_currency_id = (SELECT dc.currency_id FROM dim_currency AS dc
            WHERE dc.currency_code = 'GBP')
        AND ds.is_active = TRUE
        AND ds.symbol IN ('AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA')
)

SELECT
    sm.symbol,
    sm.company_name,
    sm.trade_date,
    sm.price_usd,
    sm.price_gbp,
    sm.daily_return,
    sm.volume,
    sm.performance_rank,
    ROUND(sm.avg_price_30d, 4) AS avg_price_30d_usd,
    ROUND(sm.avg_volume_30d::bigint) AS avg_volume_30d,
    ROUND(sm.volatility_30d, 6) AS volatility_30d,
    CASE
        WHEN sm.price_30d_ago IS NOT NULL AND sm.price_30d_ago > 0
        THEN ROUND(((sm.price_usd - sm.price_30d_ago) / sm.price_30d_ago * 100), 4)
    END AS price_change_30d_pct
FROM stock_metrics AS sm
    INNER JOIN latest_date AS ld ON sm.trade_date = ld.latest_trading_date
ORDER BY sm.daily_return DESC;
