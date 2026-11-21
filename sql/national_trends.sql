-- How have unemployment rate, inflation, and interest rates moved together?

-- Output: one row per month with:
-- unemployement_rate : national unemployment rate (%)
-- fed_funds_rate : federal funds rate (%)
-- inflation_rate : year over year change in CPI (%)
-- real_fed_funds_rate : fed funds rate minus inflation (approximate)

-- Pivot: turn three series stored as rows into three columns, one row per column
WITH national AS (
    SELECT
        obs_date,
        MAX(CASE WHEN series_id = 'UNRATE' THEN value END) AS unemployment,
        MAX(CASE WHEN series_id = 'CPIAUCSL' THEN value END) AS cpi,
        MAX(CASE WHEN series_id = 'FEDFUNDS' THEN value END) AS fed_funds_rate
    FROM observations
    WHERE series_id IN ('UNRATE', 'CPIAUCSL', 'FEDFUNDS')
    GROUP BY obs_date
)
SELECT
    cur.obs_date,
    cur.unemployment_rate,
    cur.fed_funds_rate,
    -- inflation defeined as how much CPI index rose compared with the same month last year
    ROUND((cur.cpi / prev.cpi - 1) * 100, 2) AS inflation_rate,
    ROUND(cur.fed_funds_rate - (cur.cpi / prev.cpi - 1) * 100, 2) AS real_fed_funds_rate
FROM national cur
Join national prev 
    ON prev.obs_date = date(cur.obs_date, '-12 months')
WHERE cur.cpi IS NOT NULL
    AND prev.cpi IS NOT NULL
ORDER BY cur.obs_date;