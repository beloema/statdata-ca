import pandas as pd

source = "data/raw/18100004.csv"
destination = "data/processed/cpi.csv"

df = pd.read_csv(source, low_memory=False)

# Select Canada's overall CPI
df = df[
    (df["GEO"] == "Canada") &
    (df["Products and product groups"] == "All-items") &
    (df["TERMINATED"].isna())
].copy()

# Keep relevant columns
df = df[["REF_DATE", "GEO", "UOM", "VALUE"]]

# Normalize
df.columns = ["date", "region", "unit", "value"]
df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# Remove missing values and duplicates
df = df.dropna(subset=["date", "value"])
df = df.drop_duplicates(subset=["date", "region", "unit"])
df = df.sort_values("date")

# Save cleaned dataset
df.to_csv(destination, index=False)

print(f"Cleaned records: {len(df):,}")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print("\nLatest 5 records:")
print(df.tail().to_string(index=False))
