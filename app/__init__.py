
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def get_db_connection():
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(dbname="statdata")

from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

QUERIES = {
    "inflation": """
        SELECT date, value, unit FROM cpi
        WHERE region = 'Canada'
        ORDER BY date DESC LIMIT 1
    """,
    "interest_rates": """
        SELECT date, value, unit FROM interest_rates
        WHERE indicator = 'Target rate'
        ORDER BY date DESC LIMIT 1
    """,
    "exchange_rates": """
        SELECT date, value, unit FROM exchange_rates
        WHERE currency = 'USD'
        ORDER BY date DESC LIMIT 1
    """,
    "employment": """
        SELECT date, value, unit FROM employment
        WHERE region = 'Canada'
        AND indicator = 'Unemployment rate'
        ORDER BY date DESC LIMIT 1
    """,
    "gdp": """
        SELECT date, value, unit FROM gdp
        WHERE industry = 'All industries'
        ORDER BY date DESC LIMIT 1
    """,
    "population": """
        SELECT date, value, unit FROM population
        WHERE region = 'Canada'
        ORDER BY date DESC LIMIT 1
    """
}

QUERIES["inflation_rate"] = "SELECT date, value, unit FROM inflation_yoy ORDER BY date DESC LIMIT 1"

@app.route("/health")
def home():
    return jsonify({
        "project": "STATDATA.CA",
        "status": "running",
        "datasets": 6
    })

@app.route("/api/overview")
def overview():
    results = {}

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for name, query in QUERIES.items():
                cur.execute(query)
                row = cur.fetchone()

                results[name] = {
                    "date": row["date"].isoformat(),
                    "value": float(row["value"]),
                    "unit": row["unit"]
                } if row else None

    return jsonify(results)

@app.route("/api/history/<dataset>")
def history(dataset):
    queries = {
        "inflation": "SELECT date, value FROM cpi WHERE region = 'Canada'",
        "inflation_rate": "SELECT date, value FROM inflation_yoy",
        "interest_rates": "SELECT date, value FROM interest_rates WHERE indicator = 'Target rate'",
        "exchange_rates": "SELECT date, value FROM exchange_rates WHERE currency = 'USD'",
        "employment": "SELECT date, value FROM employment WHERE region = 'Canada' AND indicator = 'Unemployment rate'",
        "gdp": "SELECT date, value FROM gdp WHERE industry = 'All industries'",
        "population": "SELECT date, value FROM population WHERE region = 'Canada'"
    }

    if dataset not in queries:
        return jsonify({"error": "Unknown dataset"}), 404

    query = queries[dataset] + " ORDER BY date DESC LIMIT 120"

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return jsonify([
        {"date": row["date"].isoformat(), "value": float(row["value"])}
        for row in reversed(rows)
    ])

from flask import render_template

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Historical chart data with date-range filters
from flask import request

@app.route("/api/chart/<dataset>")
def chart_data(dataset):
    sources = {
        "inflation": "SELECT date, value FROM cpi WHERE region = 'Canada'",
        "inflation_rate": "SELECT date, value FROM inflation_yoy",
        "interest_rates": "SELECT date, value FROM interest_rates WHERE indicator = 'Target rate'",
        "exchange_rates": "SELECT date, value FROM exchange_rates WHERE currency = 'USD'",
        "employment": "SELECT date, value FROM employment WHERE region = 'Canada' AND indicator = 'Unemployment rate'",
        "gdp": "SELECT date, value FROM gdp WHERE industry = 'All industries'",
        "population": "SELECT date, value FROM population WHERE region = 'Canada'"
    }

    if dataset not in sources:
        return jsonify({"error": "Unknown dataset"}), 404

    period = request.args.get("range", "10Y").upper()
    years = {"1Y": 1, "5Y": 5, "10Y": 10, "ALL": None}

    if period not in years:
        return jsonify({"error": "Invalid range"}), 400

    source = sources[dataset]

    if years[period] is None:
        query = f"SELECT date, value FROM ({source}) s ORDER BY date"
        params = ()
    else:
        query = f"""
            WITH series AS ({source})
            SELECT date, value FROM series
            WHERE date >= (
                SELECT MAX(date) FROM series
            ) - (%s * INTERVAL '1 year')
            ORDER BY date
        """
        params = (years[period],)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return jsonify([
        {"date": row["date"].isoformat(), "value": float(row["value"])}
        for row in rows
    ])

@app.route("/api/regions/<dataset>")
def regional_comparison(dataset):
    queries = {
        "employment": {
            "table": "employment",
            "filter": "indicator = 'Unemployment rate'",
            "regions": 10,
        },
        "population": {
            "table": "population",
            "filter": "TRUE",
            "regions": 13,
        },
    }

    if dataset not in queries:
        return jsonify({"error": "Unknown dataset"}), 404

    config = queries[dataset]
    table = config["table"]
    condition = config["filter"]

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT date
                FROM {table}
                WHERE region != 'Canada' AND {condition}
                GROUP BY date
                HAVING COUNT(DISTINCT region) = %s
                ORDER BY date DESC
                LIMIT 1
            """, (config["regions"],))

            latest = cur.fetchone()

            if not latest:
                return jsonify({"error": "No complete regional data"}), 404

            cur.execute(f"""
                SELECT region, value
                FROM {table}
                WHERE date = %s
                  AND region != 'Canada'
                  AND {condition}
                ORDER BY value DESC
            """, (latest["date"],))

            rows = cur.fetchall()

    return jsonify({
        "date": latest["date"].isoformat(),
        "dataset": dataset,
        "regions": [
            {"region": r["region"], "value": float(r["value"])}
            for r in rows
        ]
    })

from datetime import date
from dateutil.relativedelta import relativedelta
from statistics import mean

@app.route("/api/analytics/<dataset>")
def analytics(dataset):
    sources = {
        "inflation": "SELECT date, value FROM cpi WHERE region = 'Canada'",
        "inflation_rate": "SELECT date, value FROM inflation_yoy",
        "interest_rates": "SELECT date, value FROM interest_rates WHERE indicator = 'Target rate'",
        "exchange_rates": "SELECT date, value FROM exchange_rates WHERE currency = 'USD'",
        "employment": "SELECT date, value FROM employment WHERE region = 'Canada' AND indicator = 'Unemployment rate'",
        "gdp": "SELECT date, value FROM gdp WHERE industry = 'All industries'",
        "population": "SELECT date, value FROM population WHERE region = 'Canada'"
    }

    if dataset not in sources:
        return jsonify({"error": "Unknown dataset"}), 404

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sources[dataset] + " ORDER BY date")
            rows = [(d, float(v)) for d, v in cur.fetchall()]

    if not rows:
        return jsonify({"error": "No observations"}), 404

    latest_date, latest_value = rows[-1]
    cutoff = latest_date - relativedelta(years=1)

    annual = [v for d, v in rows if d > cutoff]
    previous = next(
        (v for d, v in reversed(rows) if d <= cutoff),
        None
    )

    rate_datasets = {"inflation_rate", "interest_rates", "employment"}

    if previous is None:
        change = None
    elif dataset in rate_datasets:
        change = latest_value - previous
    elif previous != 0:
        change = (latest_value / previous - 1) * 100
    else:
        change = None

    return jsonify({
        "dataset": dataset,
        "date": latest_date.isoformat(),
        "latest": latest_value,
        "average_12m": round(mean(annual), 3),
        "minimum_12m": min(annual),
        "maximum_12m": max(annual),
        "annual_change": round(change, 2) if change is not None else None,
        "change_unit": "percentage points" if dataset in rate_datasets else "%",
        "observations_12m": len(annual)
    })

# CSV data exports
import csv
import io
from flask import Response

@app.route("/api/export/<dataset>")
def export_csv(dataset):
    sources = {
        "inflation": (
            "SELECT date, value FROM cpi WHERE region = 'Canada'",
            "18-10-0004-01", "CPI (2002=100)"
        ),
        "inflation_rate": (
            "SELECT date, value FROM inflation_yoy",
            "18-10-0004-01 (derived)", "Percent"
        ),
        "interest_rates": (
            "SELECT date, value FROM interest_rates WHERE indicator = 'Target rate'",
            "10-10-0139-01", "Percent"
        ),
        "exchange_rates": (
            "SELECT date, value FROM exchange_rates WHERE currency = 'USD'",
            "33-10-0036-01", "CAD per USD"
        ),
        "employment": (
            "SELECT date, value FROM employment WHERE region = 'Canada' AND indicator = 'Unemployment rate'",
            "14-10-0287-01", "Percent"
        ),
        "gdp": (
            "SELECT date, value FROM gdp WHERE industry = 'All industries'",
            "36-10-0434-01", "Millions of chained 2017 CAD, annualized"
        ),
        "population": (
            "SELECT date, value FROM population WHERE region = 'Canada'",
            "17-10-0009-01", "Persons"
        )
    }

    if dataset not in sources:
        return jsonify({"error": "Unknown dataset"}), 404

    period = request.args.get("range", "10Y").upper()
    years = {"1Y": 1, "5Y": 5, "10Y": 10, "ALL": None}

    if period not in years:
        return jsonify({"error": "Invalid range"}), 400

    source, table_id, unit = sources[dataset]

    if years[period] is None:
        query = f"SELECT date, value FROM ({source}) s ORDER BY date"
        params = ()
    else:
        query = f"""
            WITH series AS ({source})
            SELECT date, value FROM series
            WHERE date >= (
                SELECT MAX(date) FROM series
            ) - (%s * INTERVAL '1 year')
            ORDER BY date
        """
        params = (years[period],)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    lang = request.args.get("lang", "fr").lower()
    if lang not in ("fr", "en"):
        return jsonify({"error": "Invalid language"}), 400

    french_units = {
        "CPI (2002=100)": "IPC (2002=100)",
        "Percent": "Pourcentage",
        "CAD per USD": "CAD par USD",
        "Millions of chained 2017 CAD, annualized":
            "Millions de dollars enchaînés de 2017, taux annuel",
        "Persons": "Personnes",
    }
    if lang == "fr":
        unit = french_units.get(unit, unit)

    writer.writerow(
        ["date", "valeur", "unite", "tableau_source"] if lang == "fr"
        else ["date", "value", "unit", "source_table"]
    )

    for date, value in rows:
        writer.writerow([date.isoformat(), value, unit, table_id])

    filename = f"statdata_{dataset}_{period.lower()}.csv"

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@app.route("/api/region-history/<dataset>")
def region_history(dataset):
    from dateutil.relativedelta import relativedelta

    sources = {
        "employment": (
            "employment",
            "AND indicator = 'Unemployment rate'"
        ),
        "population": ("population", "")
    }

    if dataset not in sources:
        return jsonify({"error": "Unknown dataset"}), 404

    region = request.args.get("region", "Quebec")
    period = request.args.get("range", "10Y").upper()
    years = {"1Y": 1, "5Y": 5, "10Y": 10, "ALL": None}

    if period not in years:
        return jsonify({"error": "Invalid range"}), 400

    table, condition = sources[dataset]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT date, region, value
                FROM {table}
                WHERE region IN (%s, %s)
                {condition}
                ORDER BY date
            """, ("Canada", region))
            rows = cur.fetchall()

    national = {}
    regional = {}

    for date, geo, value in rows:
        if geo == "Canada":
            national[date] = float(value)
        else:
            regional[date] = float(value)

    dates = sorted(set(national) & set(regional))

    if not dates:
        return jsonify({"error": "No matching data"}), 404

    if years[period] is not None:
        cutoff = dates[-1] - relativedelta(years=years[period])
        dates = [d for d in dates if d >= cutoff]

    region_values = [regional[d] for d in dates]
    canada_values = [national[d] for d in dates]

    if dataset == "population":
        region_base = region_values[0]
        canada_base = canada_values[0]

        region_values = [
            round(v / region_base * 100, 3)
            for v in region_values
        ]
        canada_values = [
            round(v / canada_base * 100, 3)
            for v in canada_values
        ]

    return jsonify({
        "region": region,
        "dataset": dataset,
        "unit": "Index (start = 100)" if dataset == "population" else "Percent",
        "dates": [d.isoformat() for d in dates],
        "region_values": region_values,
        "canada_values": canada_values
    })


@app.route("/about")
@app.route("/a-propos")
def about_page():
    return render_template("about.html")
