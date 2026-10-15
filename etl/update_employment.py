import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

SOURCE = "data/raw/14100287.csv"
DESTINATION = "data/processed/employment.csv"

INDICATORS = [
    "Employment",
    "Unemployment",
    "Unemployment rate",
    "Employment rate",
    "Participation rate",
]

print("1. Reading employment data...")

df = pd.read_csv(SOURCE, low_memory=False)

print("2. Cleaning data...")

df = df[
    (df["Labour force characteristics"].isin(INDICATORS))
    & (df["Gender"] == "Total - Gender")
    & (df["Age group"] == "15 years and over")
    & (df["Statistics"] == "Estimate")
    & (df["Data type"] == "Seasonally adjusted")
    & (df["TERMINATED"].isna())
].copy()

df = df[
    ["REF_DATE", "GEO", "Labour force characteristics", "UOM", "VALUE"]
]

df.columns = ["date", "region", "indicator", "unit", "value"]

df["date"] = pd.to_datetime(
    df["date"], format="%Y-%m", errors="coerce"
)
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "value"])
    .drop_duplicates(subset=["date", "region", "indicator"])
    .sort_values(["region", "indicator", "date"])
)

df.to_csv(DESTINATION, index=False)

print("3. Updating PostgreSQL...")

records = [
    (r.date.date(), r.region, r.indicator, r.unit, float(r.value))
    for r in df.itertuples(index=False)
]

with psycopg2.connect(dbname="statdata") as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employment (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                region TEXT NOT NULL,
                indicator TEXT NOT NULL,
                unit TEXT NOT NULL,
                value NUMERIC NOT NULL,
                UNIQUE (date, region, indicator)
            )
        """)

        execute_values(cur, """
            INSERT INTO employment
                (date, region, indicator, unit, value)
            VALUES %s
            ON CONFLICT (date, region, indicator)
            DO UPDATE SET
                unit = EXCLUDED.unit,
                value = EXCLUDED.value
            WHERE employment.value IS DISTINCT FROM EXCLUDED.value
               OR employment.unit IS DISTINCT FROM EXCLUDED.unit
        """, records, page_size=1000)

        cur.execute("SELECT COUNT(*) FROM employment")
        total = cur.fetchone()[0]

print(f"Success! {total:,} records in PostgreSQL.")
print(f"Indicators: {df['indicator'].nunique()}")
print(f"Regions: {df['region'].nunique()}")
print(f"Latest observation: {df['date'].max().date()}")

print("\nLatest Canadian indicators:")
latest = df[df["region"] == "Canada"]
latest = latest.sort_values("date").groupby("indicator").tail(1)
print(latest.to_string(index=False))
