import io
import zipfile
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

URL = "https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip"

print("1. Downloading Statistics Canada CPI data...")

response = requests.get(URL, timeout=120)
response.raise_for_status()

print("2. Extracting data...")

with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
    with archive.open("18100004.csv") as file:
        df = pd.read_csv(file, low_memory=False)

print("3. Cleaning data...")

df = df[
    (df["GEO"] == "Canada")
    & (df["Products and product groups"] == "All-items")
    & (df["TERMINATED"].isna())
].copy()

df = df[["REF_DATE", "GEO", "UOM", "VALUE"]]
df.columns = ["date", "region", "unit", "value"]

df["date"] = pd.to_datetime(
    df["date"], format="%Y-%m", errors="coerce"
)
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "value"])
    .drop_duplicates(subset=["date", "region", "unit"])
    .sort_values("date")
)

df.to_csv("data/processed/cpi.csv", index=False)

print("4. Updating PostgreSQL...")

records = [
    (row.date.date(), row.region, row.unit, float(row.value))
    for row in df.itertuples(index=False)
]

with psycopg2.connect(dbname="statdata") as connection:
    with connection.cursor() as cursor:
        execute_values(
            cursor,
            """
            INSERT INTO cpi (date, region, unit, value)
            VALUES %s
            ON CONFLICT (date, region, unit)
            DO UPDATE SET value = EXCLUDED.value
            WHERE cpi.value IS DISTINCT FROM EXCLUDED.value
            """,
            records,
        )

        cursor.execute("SELECT COUNT(*) FROM cpi")
        total = cursor.fetchone()[0]

print(f"Success! {total:,} CPI records in PostgreSQL.")
print(f"Latest observation: {df['date'].max().date()}")
