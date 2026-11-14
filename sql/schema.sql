-- Schema for the US economy database
-- rebuilt every time you run load.py

DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS states;

--- one row per state (+ DC) with its Census region for regional comparison
CREATE TABLE states (
    state_code TEXT PRIMARY KEY,
    state_name TEXT NOT NULL,
    region TEXT NOT NULL
);

-- one row per FRED series, including what it is, its units and which state (for state series)
CREATE TABLE series (
    series_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    units TEXT,
    frequency TEXT,
    seasonal_adjustment TEXT,
    last_updated TEXT,
    state_code TEXT REFERENCES states (state_code)
);

-- one roe per series per month, includes the actual data points
CREATE TABLE observations (
    series_id TEXT NOT NULL REFERENCES series (series_id),
    obs_date TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (series_id, obs_date)
);

-- speed up queries that filter by date range
CREATE INDEX idx_observations_date ON observations (obs_date);
