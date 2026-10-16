"""Offline tests for daily ETL orchestration and connection safety."""

from unittest.mock import MagicMock, patch

import pytest

from etl.db import get_connection
import update_all


def test_neon_url_is_used_when_supplied(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://sample:placeholder@localhost:5432/sample")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with patch("etl.db.psycopg2.connect") as connect:
        result = get_connection()
        assert result is connect.return_value
        connect.assert_called_once_with(
            "postgresql://sample:placeholder@localhost:5432/sample", connect_timeout=20
        )


def test_actions_requires_secret(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_connection()


def test_local_postgres_fallback(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with patch("etl.db.psycopg2.connect") as connect:
        get_connection()
        connect.assert_called_once_with(dbname="statdata")


def test_update_all_runs_all_six_scripts(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    with patch.object(update_all, "download") as download, patch.object(update_all, "run") as run:
        update_all.main()
    assert download.call_count == 3
    assert run.call_count == 6
    assert [call.args[0] for call in run.call_args_list] == [
        "update_cpi.py", "update_interest_rates.py", "update_exchange_rates.py",
        "update_employment.py", "update_gdp.py", "update_population.py",
    ]
    assert (tmp_path / "data" / "raw").is_dir()
    assert (tmp_path / "data" / "processed").is_dir()


def test_failed_etl_process_causes_failure():
    from subprocess import CalledProcessError
    with patch.object(update_all.subprocess, "run", side_effect=CalledProcessError(1, "etl")):
        with pytest.raises(CalledProcessError):
            update_all.run("update_cpi.py")
