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

## Project structure

[to be filled as code is added]

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

## Limitations 

[to be filled]