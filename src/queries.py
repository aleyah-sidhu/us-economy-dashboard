'''
Find the database and open as read-only
Run SQL files from sql/ by name and return a pandas DataFrame, converting date columns to real dates from text
The dashboard will call these functions.

to run: python -m src.queries
'''

import sqlite3
from pathlib import Path
import pandas as pd

#build paths for database and sql
DB_PATH = Path("data/economy.db")
SQL_PATH = Path("sql")

#define query files for dashboard use
QUERY_NAMES = ["national_trends", "state_latest", "region_trends", "pandemic_impact"]
#columns in queries that hold dates
DATE_COLUMNS = ["obs_date", "as_of_date", "peak_date", "recovery_date"]

#connection function to open database in read-only mode
def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Run 'python -m src.extract' and then 'python -m src.load'"
        )
    return sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)

#run sql query function
def run_query(name):
    #run sql/name.sql
    sql_path = SQL_PATH / f"{name}.sql"
    if not sql_path.exists():
        raise FileNotFoundError(F"No SQL file named {sql_path.name} in {SQL_PATH}")
    
    conn = get_connection()
    try:
        #return as dataframes
        df = pd.read_sql_query(sql_path.read_text(), conn)
    finally:
        conn.close()
    
    #convert date columns from text to datetime
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df

def national_trends():
    return run_query("national_trends")

def state_latest():
    return run_query("state_latest")

def region_trends():
    return run_query("region_trends")

def pandemic_impact():
    return run_query("pandemic_impact")

if __name__ == "__main__":
    for query_name in QUERY_NAMES:
        result = run_query(query_name)
        print(f"{query_name}: {len(result)} rows, {len(result.columns)} columns")
        print(result.head(3).to_string(index=False))

