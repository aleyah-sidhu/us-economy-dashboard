-- What states have the highest unemployment now and who's improving?

-- Output: one row per state for most recent month in the data:
-- unemployement_rate : latest unemployment rate (%)
-- rate_year_go : unemployment rate 12 months earlier (%)
-- change_vs_year_ago : difference in percentage points
-- trend : Improving / Worsening / Flat
-- rank_highest_unemployment : 1 = highest unemployment

-- every states unemployment rate with state code attached
WITH state_obs AS (
    SELECT
        se.state_code,
        o.obs_date,
        o.value
    FROM observations o
    JOIN series se
        ON se.series_id = o.series_id
    WHERE se.state_code IS NOT NULL
        AND o.value IS NOT NULL
),
latest AS ( 
    -- the most recent month available so that every state is compared on the same date
    SELECT MAX(obs_date) AS obs_date
    FROM state_obs
)
SELECT
    st.state_code,
    st.state_name,
    st.region,
    cur.obs_date AS as_of_date,
    cur.value AS unemployment_rate,
    prev.value AS rate_year_ago,
    ROUND(cur.value - prev.value, 1) AS change_vs_year_ago,
    CASE
        WHEN cur.value < prev.value THEN 'Improving'
        WHEN cur.value > prev.value THEN 'Worsening'
        ELSE 'Flat'
    END AS trend,
    RANK() OVER (ORDER BY cur.value DESC) AS rank_highest_unemployment
FROM state_obs cur
JOIN latest 
    ON cur.obs_date = latest.obs_date
JOIN states st 
    ON st.state_code = cur.state_code
LEFT JOIN state_obs prev 
    ON prev.state_code = cur.state_code
    AND prev.obs_date = date(cur.obs_date, '-12 months')
ORDER BY rank_highest_unemployment, st.state_name;
