import pytest
import psycopg2
from app import app

TABLES = [
    "cpi", "interest_rates", "exchange_rates",
    "employment", "gdp", "population"
]

DATASETS = [
    "inflation", "inflation_rate", "interest_rates",
    "exchange_rates", "employment", "gdp", "population"
]

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_homepage(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "running"


def test_dashboard(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"STATDATA" in response.data
    assert b"i18n.js" in response.data


def test_all_datasets():
    with psycopg2.connect(dbname="statdata") as conn:
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                assert cur.fetchone()[0] > 0


def test_overview(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    for dataset in DATASETS:
        assert response.json[dataset] is not None


@pytest.mark.parametrize("dataset", DATASETS)
def test_historical_data(client, dataset):
    response = client.get(
        f"/api/chart/{dataset}?range=5Y"
    )
    assert response.status_code == 200
    assert len(response.json) > 0


@pytest.mark.parametrize("dataset", ["employment", "population"])
def test_regional_data(client, dataset):
    response = client.get(f"/api/regions/{dataset}")
    assert response.status_code == 200
    assert len(response.json["regions"]) > 0


def test_regional_comparison(client):
    response = client.get(
        "/api/region-history/population"
        "?region=Quebec&range=5Y"
    )
    assert response.status_code == 200
    data = response.json
    assert len(data["dates"]) > 0
    assert len(data["region_values"]) == len(data["canada_values"])


@pytest.mark.parametrize("dataset", DATASETS)
def test_csv_export(client, dataset):
    response = client.get(
        f"/api/export/{dataset}?range=1Y&lang=en"
    )
    assert response.status_code == 200
    assert "text/csv" in response.content_type
    assert b"source_table" in response.data


def test_invalid_date_range(client):
    response = client.get("/api/chart/gdp?range=INVALID")
    assert response.status_code == 400


@pytest.mark.parametrize("dataset", DATASETS)
def test_french_csv_export(client, dataset):
    response = client.get(f"/api/export/{dataset}?range=1Y&lang=fr")
    assert response.status_code == 200
    assert b"tableau_source" in response.data
    assert b"valeur" in response.data


def test_invalid_export_language(client):
    response = client.get("/api/export/gdp?lang=invalid")
    assert response.status_code == 400


def test_root_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"STATDATA" in response.data


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Emanuel Belony" in response.data
    assert b"emanuelbelony.com" in response.data
    assert b"statdata-language" in response.data

def test_about_french_alias(client):
    response = client.get("/a-propos")
    assert response.status_code == 200
