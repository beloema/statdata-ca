"""Post-update checks: non-empty datasets, uniqueness, and observation dates."""

import os
from pathlib import Path
import sys

# Allow running directly as python tools/check_daily_update.py.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from psycopg2 import sql
from etl.db import get_connection

KEYS = {
    "cpi": ("date", "region", "unit"),
    "interest_rates": ("date", "indicator"),
    "exchange_rates": ("date", "currency"),
    "employment": ("date", "region", "indicator"),
    "gdp": ("date", "industry"),
    "population": ("date", "region"),
}


def check():
    results = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            for table, keys in KEYS.items():
                cur.execute(
                    sql.SQL("SELECT COUNT(*), MAX(date) FROM {}").format(
                        sql.Identifier(table)
                    )
                )
                count, latest = cur.fetchone()
                if count == 0 or latest is None:
                    raise RuntimeError(f"{table}: dataset is empty")

                cur.execute(
                    sql.SQL("""
                        SELECT EXISTS (
                            SELECT 1 FROM {}
                            GROUP BY {}
                            HAVING COUNT(*) > 1
                            LIMIT 1
                        )
                    """).format(
                        sql.Identifier(table),
                        sql.SQL(", ").join(map(sql.Identifier, keys)),
                    )
                )
                if cur.fetchone()[0]:
                    raise RuntimeError(f"{table}: duplicate composite keys detected")

                print(f"PASS {table}: {count:,} rows; newest observation {latest}", flush=True)
                results.append((table, count, str(latest)))

    total = sum(row[1] for row in results)
    print(f"PASS all 6 datasets: {total:,} records, no duplicate keys", flush=True)

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("## STATDATA.CA — Daily ETL validation\n\n")
            output.write("| Dataset | Rows | Latest observation |\n")
            output.write("| --- | ---: | --- |\n")
            for table, count, latest in results:
                output.write(f"| {table} | {count:,} | {latest} |\n")
            output.write(f"\n**Total: {total:,} records. Duplicate keys: 0.**\n")


if __name__ == "__main__":
    check()
