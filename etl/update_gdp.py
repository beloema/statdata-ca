import pandas as pd
from db import get_connection
from psycopg2.extras import execute_values

SOURCE = "data/raw/36100434.csv"
DESTINATION = "data/processed/gdp.csv"

INDUSTRIES = {
    "All industries [T001]": "All industries",
    "Goods-producing industries [T002]": "Goods-producing industries",
    "Services-producing industries [T003]": "Services-producing industries",
}

print("1. Reading and cleaning GDP data...")

chunks = []

for chunk in pd.read_csv(
    SOURCE, chunksize=100000, low_memory=False
):
    filtered = chunk[
        (chunk["GEO"] == "Canada")
        & (chunk["Seasonal adjustment"]
           == "Seasonally adjusted at annual rates")
        & (chunk["Prices"] == "Chained (2017) dollars")
        & (chunk[
            "North American Industry Classification System (NAICS)"
        ].isin(INDUSTRIES))
        & (chunk["TERMINATED"].isna())
    ].copy()

    if not filtered.empty:
        chunks.append(filtered)

if not chunks:
    raise ValueError("No matching GDP observations found.")

df = pd.concat(chunks, ignore_index=True)

df = df[
    [
        "REF_DATE",
        "North American Industry Classification System (NAICS)",
        "VALUE",
    ]
]

df.columns = ["date", "industry", "value"]

df["industry"] = df["industry"].map(INDUSTRIES)
df["date"] = pd.to_datetime(
    df["date"], format="%Y-%m", errors="coerce"
)
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = (
    df.dropna(subset=["date", "industry", "value"])
    .drop_duplicates(subset=["date", "industry"])
    .sort_values(["industry", "date"])
)

df["unit"] = "Millions of chained 2017 CAD, annualized"

df = df[["date", "industry", "unit", "value"]]
if df.empty:
    raise ValueError("No valid gdp observations matched Statistics Canada filters")

df.to_csv(DESTINATION, index=False)

print("2. Updating PostgreSQL...")

records = [
    (r.date.date(), r.industry, r.unit, float(r.value))
    for r in df.itertuples(index=False)
]

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gdp (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                industry TEXT NOT NULL,
                unit TEXT NOT NULL,
                value NUMERIC NOT NULL,
                UNIQUE (date, industry)
            )
        """)

        execute_values(cur, """
            INSERT INTO gdp
                (date, industry, unit, value)
            VALUES %s
            ON CONFLICT (date, industry)
            DO UPDATE SET
                unit = EXCLUDED.unit,
                value = EXCLUDED.value
            WHERE gdp.value IS DISTINCT FROM EXCLUDED.value
               OR gdp.unit IS DISTINCT FROM EXCLUDED.unit
        """, records, page_size=1000)

        cur.execute("SELECT COUNT(*) FROM gdp")
        total = cur.fetchone()[0]

print(f"Success! {total:,} records in PostgreSQL.")
print(f"Industries: {df['industry'].nunique()}")
print(f"Latest observation: {df['date'].max().date()}")

print("\nLatest GDP observations:")
latest = df.sort_values("date").groupby("industry").tail(1)
print(latest.to_string(index=False))
