# US Economy Dashboard

An interactive dashboard tracking US unemployment, inflation, and interest rates. Built on a SQL database fed by the Federal Reserve's FRED API.

Live app: [to be filled once live]

## Question

How have the US labor market, inflation, and interest rates moved together, and how do states compare?

## Data

Source: [FRED](https://fred.stlouisfed.org/)

| Series | What it measures |
| UNRATE | National unemployment rate |
| CPIAUCSL | Consumer Price Index (used to compute inflation)
| FEDFUNDS | Federal funds rate |
| [STATE]UR | State unemployment rates |

## How it works

FRED API --> extract (raw files) --> load (SQLite) --> SQL queries -> Streamlit dashboard

## Setup

```bash
git clone https://github.com/aleyah-sidhu/us-economy-dashboard.git
cd us-economy-dashboard
python3 -m venv .venv
source .venv/bin/activate #windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env #windows: copy .env.ex
# add your FRED API key to .env
```

## Analysis

Each question is answered by one SQL file in `sql/`, run through `src/queries.py`

| Question | File | SQL Techniques |
| --- | --- | --- |
| How have unemployment rate, inflation, and interest rates moved together? | `national_trends.sql` | CTEs, table pivot, self-joins |
| Which states were hit the hardest in 2020 and how fast did they recover? | `pandemic_impact.sql` | Chained CTEs, date functions, RANK () |
| How do the four regions compare over time? | `region_trends.sql` | Three-table join, GROUP BY with AVG |
| What states have the highest unemployment now and who's improving? | `state_latest.sql` | Joins, RANK() window function, CASE |

## Limitations 

- Regional figures are simple averages of state rates, not weighted by population or labor force
- Inflation is the year-over-year change in all-items CPI meaning first inflation figure is Jan 2001
- The "real" fed funds rate is the fed funds rate minus trailing inflation
- "Recovered" in the pandemic analysis means back within 0.5 percentage points of the Feb 2020 rate. Threshold is a choice and can be changed
- Data is a snapshot of the last pipeline run