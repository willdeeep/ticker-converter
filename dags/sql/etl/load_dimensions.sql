-- Load Dimensions: Direct Insertion Support
-- Note: Dimension loading is now handled automatically during direct fact loading
-- This file contains maintenance queries for dimension completeness

-- Dimension loading is now handled by the Python DatabaseManager:
-- 1. ensure_date_dimension() automatically creates dates during fact insertion
-- 2. Stock and currency dimensions are populated during system initialization
-- 3. Dimensional lookups happen during direct fact table insertion

-- Manual dimension maintenance (optional) - Ensure dimension integrity
-- Update any missing dates that might be needed for reporting
-- This query adds a range of dates if needed for calendar tables

-- Generate date range for current year (if not already present)
INSERT INTO dim_date (date_value, year, quarter, month, day, day_of_week, day_of_year, week_of_year, is_weekend)
SELECT
    generate_series::date AS date_value,
    EXTRACT(YEAR FROM generate_series) AS year,
    EXTRACT(QUARTER FROM generate_series) AS quarter,
    EXTRACT(MONTH FROM generate_series) AS month,
    EXTRACT(DAY FROM generate_series) AS day,
    EXTRACT(DOW FROM generate_series) AS day_of_week,
    EXTRACT(DOY FROM generate_series) AS day_of_year,
    EXTRACT(WEEK FROM generate_series) AS week_of_year,
    CASE WHEN EXTRACT(DOW FROM generate_series) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(
    DATE_TRUNC('year', CURRENT_DATE),  -- Start of current year
    DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' - INTERVAL '1 day',  -- End of current year
    '1 day'::interval
) AS generate_series
ON CONFLICT (date_value) DO NOTHING;

-- Optional: Add future dates for forecasting (next 30 days)
INSERT INTO dim_date (date_value, year, quarter, month, day, day_of_week, day_of_year, week_of_year, is_weekend)
SELECT
    (CURRENT_DATE + generate_series)::date AS date_value,
    EXTRACT(YEAR FROM CURRENT_DATE + generate_series) AS year,
    EXTRACT(QUARTER FROM CURRENT_DATE + generate_series) AS quarter,
    EXTRACT(MONTH FROM CURRENT_DATE + generate_series) AS month,
    EXTRACT(DAY FROM CURRENT_DATE + generate_series) AS day,
    EXTRACT(DOW FROM CURRENT_DATE + generate_series) AS day_of_week,
    EXTRACT(DOY FROM CURRENT_DATE + generate_series) AS day_of_year,
    EXTRACT(WEEK FROM CURRENT_DATE + generate_series) AS week_of_year,
    CASE WHEN EXTRACT(DOW FROM CURRENT_DATE + generate_series) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(1, 30) AS generate_series
ON CONFLICT (date_value) DO NOTHING;
