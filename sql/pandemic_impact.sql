-- Which states were hit the hardest in 2020 and how fast did they recover?

-- Output: one row per state:
-- baseline_rate : unemployment rate in feb 2020
-- peak_rate : highest rate between march 2020 and december 2021
-- peak_date : month of peak
-- increase : peak - baseline
-- recovery_date : first month after peak back within 0.5 points of baseline
-- months_to_recover : months from the peak to recovery
-- rank_by_increase : 1 = largest increase

-- state table
WITH state_obs AS (
    SELECT
        ser.state_code,
        o.obs_date,
        o.value
    FROM observations o
    JOIN series ser
        ON ser.series_id = o.series_id
    WHERE ser.series_id IS NOT NULL
        AND o.value IS NOT NULL
),
baseline AS (
    -- pre-pandemic 
    SELECT
        state_code,
        obs_date,
        value AS baseline_rate
    FROM state_obs
    WHERE obs_date = '2020-02-01'
),
peak AS (
    -- worst rate during pandemic shock
    SELECT
        state_code,
        MAX(value) AS peak_rate
    FROM state_obs
    WHERE obs_date BETWEEN '2020-03-01' AND '2021-12-31'
    GROUP BY state_code
),
peak_date AS (
    -- first date where worst rate happened
    SELECT
        p.state_code,
        p.peak_rate,
        MIN(s.obs_date) AS peak_date
    FROM peak p
    JOIN state_obs s
        ON s.state_code = p.state_code
        AND s.value = p.peak_rate
        AND s.obs_date BETWEEN '2020-03-01' AND '2021-12-31'
    GROUP BY p.state_code, p.peak_rate
),
recovery AS (
    -- first month after peak where rate is back near baseline (0.5)
    SELECT
        pd.state_code, 
        MIN(s.obs_date) AS recovery_date
    FROM peak_date pd
    JOIN baseline b
        ON b.state_code = pd.state_code
    JOIN state_obs s 
        ON s.state_code = pd.state_code
        AND s.obs_date > pd.peak_date
        AND s.value <= b.baseline_rate + 0.5
    GROUP BY pd.state_code
)
SELECT
    s.state_code,
    s.state_name,
    s.region,
    b.baseline_rate,
    pd.peak_rate,
    ROUND(pd.peak_rate - b.baseline_rate, 1) AS increase,
    pd.peak_date,
    r.recovery_date,
    -- months between peak and recovery date
    (CAST(strftime('%Y', r.recovery_date) AS INTEGER) - CAST(strftime('%Y', pd.peak_date) AS INTEGER)) * 12
    + (CAST(strftime('%m', r.recovery_date) AS INTEGER) - CAST(strftime('%m', pd.peak_date) AS INTEGER)) 
    AS months_to_recover,
    RANK() OVER (ORDER BY pd.peak_rate - b.baseline_rate DESC) AS rank_by_increase
FROM peak_date pd 
JOIN baseline b 
    ON b.state_code = pd.state_code
JOIN states s 
    ON s.state_code = pd.state_code
LEFT JOIN recovery r -- Null for states that have no recovery
    ON r.state_code = pd.state_code
ORDER BY rank_by_increase, s.state_name;

