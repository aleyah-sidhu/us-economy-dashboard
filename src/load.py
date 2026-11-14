# read raw FRED JSON files from data/raw/ and build SQLite 
# database in data/economy.db using the schema defined in sql/schema.sql

# run after running src/extract using: python -m src.load

import json
import sqlite3
import sys
from pathlib import Path

from src.extract import NATIONAL_SERIES

RAW_DIR = Path("data/raw")
DB_DIR = Path("data/economy.db")
SCHEMA_DIR = Path("sql/schema.sql")

# state codes and census regions
STATES = {
    "AL": ("Alabama", "South"), "AK": ("Alaska", "West"),
    "AZ": ("Arizona", "West"), "AR": ("Arkansas", "South"),
    "CA": ("California", "West"), "CO": ("Colorado", "West"),
    "CT": ("Connecticut", "Northeast"), "DE": ("Delaware", "South"),
    "FL": ("Florida", "South"), "GA": ("Georgia", "South"),
    "HI": ("Hawaii", "West"), "ID": ("Idaho", "West"),
    "IL": ("Illinois", "Midwest"), "IN": ("Indiana", "Midwest"),
    "IA": ("Iowa", "Midwest"), "KS": ("Kansas", "Midwest"),
    "KY": ("Kentucky", "South"), "LA": ("Louisiana", "South"),
    "ME": ("Maine", "Northeast"), "MD": ("Maryland", "South"),
    "MA": ("Massachusetts", "Northeast"), "MI": ("Michigan", "Midwest"),
    "MN": ("Minnesota", "Midwest"), "MS": ("Mississippi", "South"),
    "MO": ("Missouri", "Midwest"), "MT": ("Montana", "West"),
    "NE": ("Nebraska", "Midwest"), "NV": ("Nevada", "West"),
    "NH": ("New Hampshire", "Northeast"), "NJ": ("New Jersey", "Northeast"),
    "NM": ("New Mexico", "West"), "NY": ("New York", "Northeast"),
    "NC": ("North Carolina", "South"), "ND": ("North Dakota", "Midwest"),
    "OH": ("Ohio", "Midwest"), "OK": ("Oklahoma", "South"),
    "OR": ("Oregon", "West"), "PA": ("Pennsylvania", "Northeast"),
    "RI": ("Rhode Island", "Northeast"), "SC": ("South Carolina", "South"),
    "SD": ("South Dakota", "Midwest"), "TN": ("Tennessee", "South"),
    "TX": ("Texas", "South"), "UT": ("Utah", "West"),
    "VT": ("Vermont", "Northeast"), "VA": ("Virginia", "South"),
    "WA": ("Washington", "West"), "WV": ("West Virginia", "South"),
    "WI": ("Wisconsin", "Midwest"), "WY": ("Wyoming", "West"),
    "DC": ("District of Columbia", "South"),
}

#parse for values, returning missing values as null else return float of raw value
def parse_value(raw):
    if raw in (None, "", "."):
        return None
    return float(raw)

#read raw json file saved during extract step
def read_raw_files():
    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        sys.exit("No files in data/raw. Run 'python -m src.extract'")
    return files

#turn the raw json into list of rows for insertions
def build_rows(files):
    series_rows, observation_rows = [], []

    #for each file in files
    for path in files:
        data = json.loads(path.read_text())
        meta = data["series"]
        series_id = meta["id"]

        #extract state code from series_id
        state_code = None if series_id in NATIONAL_SERIES else series_id[:2]

        #add series info to series_rows
        series_rows.append((
            series_id,
            meta["title"],
            meta.get("units"),
            meta.get("frequency"),
            meta.get("seasonal_adjustment"),
            meta.get("last_updated"),
            state_code,
        ))
        #for each observation in raw data add values to observation_rows
        observation_rows.extend(
            (series_id, obs["date"], parse_value(obs["value"]))
            for obs in data["observations"]
        )

    return series_rows, observation_rows

#check that the load works
def run_checks(conn):
    def one(sql):
        return conn.execute(sql).fetchone()[0]
    
    print('Checks:')
    print(f"States: {one('SELECT COUNT(*) FROM states')} (expected 51)")
    print(f"Series: {one('SELECT COUNT(*) FROM series')} (expected 54)")
    print(f"State series: {one('SELECT COUNT(*) FROM series WHERE state_code IS NOT NULL')} (expected 51)")
    print(f"Observations: {one('SELECT COUNT(*) FROM observations'):,}")
    print(f"Missing values: {one('SELECT COUNT(*) FROM observations WHERE value IS NULL')}")
    print(f"Date range: {one('SELECT MIN(obs_date) FROM observations')} to "
          f"{one('SELECT MAX(obs_date) FROM observations')}")
    
    latest = conn.execute(
        "SELECT obs_date, value FROM observations "
        "WHERE series_id = 'UNRATE' AND value IS NOT NULL "
        "ORDER BY obs_date DESC LIMIT 1"
    ).fetchone()
    print(f"Latest national unemployment rate: {latest[1]}% ({latest[0]})")

def main():
    files = read_raw_files()
    series_rows, observation_rows = build_rows(files)

    DB_DIR.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_DIR)
    try:
        #make SQLite enforece link between tables
        conn.execute("PRAGMA foreign_keys = ON")
        #drop and recreate all tables
        conn.executescript(SCHEMA_DIR.read_text())

        with conn:
            conn.executemany(
                "INSERT INTO states (state_code, state_name, region) VALUES (?, ?, ?)",
                [(code, name, region) for code, (name, region) in STATES.items()],
            )
            conn.executemany(
                "INSERT INTO series (series_id, title, units, frequency, seasonal_adjustment, last_updated, state_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                series_rows,
            )
            conn.executemany(
                "INSERT INTO observations (series_id, obs_date, value) VALUES (?, ?, ?)",
                observation_rows,
            )
        print(f"Built {DB_DIR}")
        run_checks(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()


