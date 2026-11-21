-- How do the four regions compare over time

-- Output: one row per region per month:
-- avg_unemployement_rate : average unemployment rate (%) of states in the region
-- states_reporting : # of states in the average
-- national rate : national rate that month (%)
-- gap_vs_national : region average minus national rate (% points)

-- region table breaking down region stats: average rate, # states, etc.
WITH regional AS (
    SELECT
        st.region,
        o.obs_date,
        ROUND(AVG(o.value), 2) AS avg_unemployment_rate,
        COUNT(*) AS states_reporting
    FROM observations o
    JOIN series ser
        ON ser.series_id = o.series_id
    JOIN states st
        ON st.state_code = ser.state_code
    WHERE o.value IS NOT NULL
    GROUP BY st.region, o.obs_date
),
national AS (
    -- national table 
    SELECT  
        obs_date,
        value AS national_rate
    FROM observations
    WHERE series_id = 'UNRATE'
)
SELECT
    r.region,
    r.obs_date,
    r.avg_unemployment_rate,
    r.states_reporting,
    n.national_rate,
    ROUND(r.avg_unemployment_rate - n.national_rate, 2) AS gap_vs_national
FROM regional r
JOIN national n
    ON n.obs_date = r.obs_date
ORDER BY r.obs_date, r.region;