-- Load Currency Dimension from Raw Data
-- Populates currency dimension table from staging tables

-- Update currency dimension with any new currency codes
INSERT INTO dim_currency (currency_code, currency_name, is_base_currency, is_active)
SELECT DISTINCT
    rcd.from_currency as currency_code,
    CASE 
        WHEN rcd.from_currency = 'USD' THEN 'US Dollar'
        WHEN rcd.from_currency = 'GBP' THEN 'British Pound'
        WHEN rcd.from_currency = 'EUR' THEN 'Euro'
        ELSE CONCAT(rcd.from_currency, ' Currency')
    END as currency_name,
    CASE WHEN rcd.from_currency = 'USD' THEN TRUE ELSE FALSE END as is_base_currency,
    TRUE as is_active
FROM raw_currency_data rcd
WHERE rcd.from_currency NOT IN (SELECT currency_code FROM dim_currency)

UNION

SELECT DISTINCT
    rcd.to_currency as currency_code,
    CASE 
        WHEN rcd.to_currency = 'USD' THEN 'US Dollar'
        WHEN rcd.to_currency = 'GBP' THEN 'British Pound'
        WHEN rcd.to_currency = 'EUR' THEN 'Euro'
        ELSE CONCAT(rcd.to_currency, ' Currency')
    END as currency_name,
    CASE WHEN rcd.to_currency = 'USD' THEN TRUE ELSE FALSE END as is_base_currency,
    TRUE as is_active
FROM raw_currency_data rcd
WHERE rcd.to_currency NOT IN (SELECT currency_code FROM dim_currency)

ON CONFLICT (currency_code) DO NOTHING;
