import io
import zipfile
import requests
import pandas as pd
from db import get_connection
from psycopg2.extras import execute_values

URL = "https://www150.statcan.gc.ca/n1/tbl/csv/10100139-eng.zip"

INDICATORS = [
    "Bank rate",
    "Target rate",
    "Government of Canada benchmark bond yields, 2 year",
    "Government of Canada benchmark bond yields, 5 year",
    "Government of Canada benchmark bond yields, 10 year",
    "Treasury Bills, 3-month",
]

print("1. Downloading interest rate data...")

response = requests.get(URL, timeout=120)
response.raise_for_status()

print("2. Extracting data...")

with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
    with archive.open("10100139.csv") as file:
        df = pd.read_csv(file, low_memory=False)

print("3. Cleaning data...")

df = df[
    (df["GEO"] == "Canada")
    & (df["Financial market statistics"].isin(INDICATORS))
    & (df["TERMINATED"].isna())
].copy()

df = df[
    ["REF_DATE", "Financial market statistics", "UOM", "VALUE"]
]

df.columns = ["date", "indicator", "unit", "value"]

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "value"])
    .drop_duplicates(subset=["date", "indicator"])
    .sort_values(["indicator", "date"])
)

if df.empty:
    raise ValueError("No valid interest_rates observations matched Statistics Canada filters")

df.to_csv("data/processed/interest_rates.csv", index=False)

print("4. Updating PostgreSQL...")

records = [
    (r.date.date(), r.indicator, r.unit, float(r.value))
    for r in df.itertuples(index=False)
]

with get_connection() as conn:
    with conn.cursor() as cur:

        cur.execute("""
            CREATE TABLE IF NOT EXISTS interest_rates (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                indicator TEXT NOT NULL,
                unit TEXT NOT NULL,
                value NUMERIC NOT NULL,
                UNIQUE (date, indicator)
            )
        """)

        execute_values(cur, """
            INSERT INTO interest_rates
                (date, indicator, unit, value)
            VALUES %s
            ON CONFLICT (date, indicator)
            DO UPDATE SET
                unit = EXCLUDED.unit,
                value = EXCLUDED.value
            WHERE interest_rates.value IS DISTINCT FROM EXCLUDED.value
               OR interest_rates.unit IS DISTINCT FROM EXCLUDED.unit
        """, records)

        cur.execute("SELECT COUNT(*) FROM interest_rates")
        total = cur.fetchone()[0]

print(f"Success! {total:,} records in PostgreSQL.")
print(f"Indicators: {df['indicator'].nunique()}")
print(f"Latest observation: {df['date'].max().date()}")
