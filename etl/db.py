"""PostgreSQL connection for the Statistics Canada ETL jobs."""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Local development may use .env; GitHub Actions injects DATABASE_URL as a secret.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_connection():
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return psycopg2.connect(url, connect_timeout=20)

    # Never silently write to a GitHub runner's local PostgreSQL database.
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        raise RuntimeError("DATABASE_URL GitHub Actions secret is missing")

    # Keep the original local development workflow working.
    return psycopg2.connect(dbname="statdata")
