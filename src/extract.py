"""
Extract step: download economic time series data from the 
FRED API and save the raw responses to a data file (data/raw/) as 
a JSON file (one file per series)

to run: python -m src.extract
"""

#set up/load libraries and set up api settings
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

FRED_BASE = "https://api.stlouisfed.org/fred"
START_DATE = "2000-01-01" #chosen date: covers 2008 financial crisis, 2020 pandemic, 2022 inflation surge
RAW_DIR = Path("data/raw")

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC"
]

STATE_SERIES = [f"{state}UR" for state in STATES]

NATIONAL_SERIES = ["UNRATE", "CPIAUCSL", "FEDFUNDS"]

def get_api_key():
    #read api key from .env file andd check that its set
    load_dotenv()
    key = os.environ.get("FRED_API_KEY")
    if not key or key == "your_key_here":
        sys.exit("FRED_API_KEY is missing")
    return key

def fred_get(endpoint, params, api_key):
    #call FRED enspoint and return parsed JSON
    url = f"{FRED_BASE}/{endpoint}"
    params = {**params, "api_key": api_key, "file_type": "json"}

    #if rate limited, wait and retry after 30 secs
    for _ in range(3):
        resp = requests.get(url, params=params, timeout=30)

        if resp.status_code == 429:
            print("Rate limited, waiting 30 seconds")
            time.sleep(30)
            continue

        if not resp.ok:
            #if not responding, exit system with message
            sys.exit(
                f"FRED request failed ({resp.status_code}) for {endpoint} "
                f"{params.get('series_id', '')}: {resp.text[:200]}"
            )
        return resp.json()
    
    sys.exit(f"Gave up on {endpoint}")
    
def fetch_series(series_id, api_key):
    #get series' metadata (titles, units, frequency) and it's observations
    meta = fred_get("series", {"series_id": series_id}, api_key)["seriess"][0]
    obs = fred_get(
        "series/observations",
        {"series_id": series_id, "observation_start": START_DATE},
        api_key,
    )["observations"]
    return {"series": meta, "observations": obs}

def main():
    api_key = get_api_key()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_ids = NATIONAL_SERIES + STATE_SERIES
    for i, series_id in enumerate(all_ids, start=1):
        data = fetch_series(series_id, api_key)
        (RAW_DIR/ f"{series_id}.json").write_text(json.dumps(data))
        print(f"[{i}/{len(all_ids)}] {series_id}: {len(data['observations'])} observations")
        time.sleep(0.5)
    
    print(f"Saved {len(all_ids)} files to {RAW_DIR}")

if __name__ == "__main__":
    main()