import io
import zipfile
import requests
import pandas as pd
from db import get_connection
from psycopg2.extras import execute_values

URL = "https://www150.statcan.gc.ca/n1/tbl/csv/33100036-eng.zip"

CURRENCIES = {
    "U.S. dollar, daily average": "USD",
    "European euro, daily average": "EUR",
    "U.K. pound sterling, daily average": "GBP",
    "Japanese yen, daily average": "JPY",
    "Swiss franc, daily average": "CHF",
    "Australian dollar, daily average": "AUD",
}

print("1. Downloading exchange rates...")

response = requests.get(URL, timeout=120)
response.raise_for_status()

print("2. Extracting data...")

with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
    with archive.open("33100036.csv") as file:
        df = pd.read_csv(file, low_memory=False)

print("3. Cleaning data...")

df = df[
    (df["GEO"] == "Canada")
    & (df["Type of currency"].isin(CURRENCIES))
    & (df["TERMINATED"].isna())
].copy()

df = df[["REF_DATE", "Type of currency", "UOM", "VALUE"]]
df.columns = ["date", "currency_name", "unit", "value"]

df["currency"] = df["currency_name"].map(CURRENCIES)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "currency", "value"])
    .drop_duplicates(subset=["date", "currency"])
    .sort_values(["currency", "date"])
)

df = df[["date", "currency", "unit", "value"]]
if df.empty:
    raise ValueError("No valid exchange_rates observations matched Statistics Canada filters")

df.to_csv("data/processed/exchange_rates.csv", index=False)

print("4. Updating PostgreSQL...")

records = [
    (r.date.date(), r.currency, r.unit, float(r.value))
    for r in df.itertuples(index=False)
]

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                currency TEXT NOT NULL,
                unit TEXT NOT NULL,
                value NUMERIC NOT NULL,
                UNIQUE (date, currency)
            )
        """)

        execute_values(cur, """
            INSERT INTO exchange_rates
                (date, currency, unit, value)
            VALUES %s
            ON CONFLICT (date, currency)
            DO UPDATE SET
                unit = EXCLUDED.unit,
                value = EXCLUDED.value
            WHERE exchange_rates.value IS DISTINCT FROM EXCLUDED.value
               OR exchange_rates.unit IS DISTINCT FROM EXCLUDED.unit
        """, records, page_size=1000)

        cur.execute("SELECT COUNT(*) FROM exchange_rates")
        total = cur.fetchone()[0]

print(f"Success! {total:,} records in PostgreSQL.")
print(f"Currencies: {df['currency'].nunique()}")
print(f"Latest observation: {df['date'].max().date()}")
print("\nLatest rates:")
print(df.sort_values("date").groupby("currency").tail(1).to_string(index=False))
