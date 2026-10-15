import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

SOURCE = "data/raw/17100009.csv"
DESTINATION = "data/processed/population.csv"

REGIONS = [
    "Canada",
    "Newfoundland and Labrador",
    "Prince Edward Island",
    "Nova Scotia",
    "New Brunswick",
    "Quebec",
    "Ontario",
    "Manitoba",
    "Saskatchewan",
    "Alberta",
    "British Columbia",
    "Yukon",
    "Northwest Territories",
    "Nunavut",
]

print("1. Reading population data...")

df = pd.read_csv(SOURCE, low_memory=False)

print("2. Cleaning data...")

df = df[
    (df["GEO"].isin(REGIONS))
    & (df["UOM"] == "Persons")
    & (df["TERMINATED"].isna())
].copy()

df = df[["REF_DATE", "GEO", "UOM", "VALUE"]]
df.columns = ["date", "region", "unit", "value"]

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "region", "value"])
    .drop_duplicates(subset=["date", "region"])
    .sort_values(["region", "date"])
)

df["value"] = df["value"].astype("int64")

df.to_csv(DESTINATION, index=False)

print("3. Updating PostgreSQL...")

records = [
    (r.date.date(), r.region, r.unit, int(r.value))
    for r in df.itertuples(index=False)
]

with psycopg2.connect(dbname="statdata") as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS population (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                region TEXT NOT NULL,
                unit TEXT NOT NULL,
                value BIGINT NOT NULL,
                UNIQUE (date, region)
            )
        """)

        execute_values(cur, """
            INSERT INTO population
                (date, region, unit, value)
            VALUES %s
            ON CONFLICT (date, region)
            DO UPDATE SET
                unit = EXCLUDED.unit,
                value = EXCLUDED.value
            WHERE population.value IS DISTINCT FROM EXCLUDED.value
               OR population.unit IS DISTINCT FROM EXCLUDED.unit
        """, records, page_size=1000)

        cur.execute("SELECT COUNT(*) FROM population")
        total = cur.fetchone()[0]

print(f"Success! {total:,} records in PostgreSQL.")
print(f"Regions: {df['region'].nunique()}")
print(f"Latest observation: {df['date'].max().date()}")

print("\nLatest population estimates:")
latest = df.sort_values("date").groupby("region").tail(1)
print(latest.sort_values("region").to_string(index=False))
