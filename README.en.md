# STATDATA.CA

**Bilingual dashboard for Canadian statistical data**  
**Tableau de bord bilingue — [Version française](README.md)**

[Live application](https://statdata.ca) · [Technical documentation](docs/ARCHITECTURE.md#english) · [Sources](docs/SOURCES.md#english)

Built by **Emanuel Belony** for **SCI 1402 — Data Science Project**, Université TÉLUQ, Certificate in Data Science (4865).

## Overview

Statistics Canada publishes a broad range of open data, but combining several official tables requires extraction and normalization. STATDATA.CA brings together **six official Statistics Canada tables** in a bilingual interface for historical trends, regional comparisons and CSV exports. Reference dates and source units are preserved.

## Features

- Interactive charts, time-range filters and summary metrics.
- Canadian and regional comparisons where data supports them.
- JSON endpoints for charts, statistics and time series.
- French- and English-language CSV exports.
- FR/EN interface with light and dark modes.
- Daily GitHub Actions data refresh with duplicate-key validation.

## Data sources

| Subject | Statistics Canada table | Selected scope |
| --- | --- | --- |
| Consumer Price Index | `18-10-0004-01` | Canada, all-items, monthly |
| Interest rates | `10-10-0139-01` | Canada, six indicators, daily |
| Exchange rates | `33-10-0036-01` | Canada, six currencies, daily |
| Labour market | `14-10-0287-01` | Canada and available regions, five indicators, monthly |
| Real GDP | `36-10-0434-01` | Canada, three industry groups, monthly |
| Population | `17-10-0009-01` | Canada, provinces and territories, quarterly |

See [data sources and filters](docs/SOURCES.md#english).

## Technology and data flow

Python · Pandas · Flask · PostgreSQL (Neon) · SQL · HTML/CSS/JavaScript · Chart.js · GitHub Actions · Render

```text
Statistics Canada CSV / API
            ↓
      Python + Pandas ETL
            ↓
Neon PostgreSQL (upserts and unique keys)
            ↓
      Flask JSON API
            ↓
STATDATA.CA charts / comparisons / CSV
```

## Verified milestone

The manually triggered GitHub Actions update completed on **October 16, 2026**, in **2 min 8 s**. Its validation summary reported **127,664 rows and 0 duplicate keys** across six tables. Scheduled execution is configured but should be checked after its first unattended run. Counts are a point-in-time snapshot.

## Setup

See [Installation and testing](docs/INSTALLATION.md#english) before connecting to a database.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests/test_daily_update.py
```

## Documentation

- [Installation and tests](docs/INSTALLATION.md#english)
- [Architecture and API](docs/ARCHITECTURE.md#english)
- [Data sources and filtering](docs/SOURCES.md#english)
- [ETL, daily refresh and checks](docs/ETL.md#english)
- [Deployment and operations](docs/DEPLOYMENT.md#english)
- [Security and professor access](docs/ACCESS.md#english)

## Academic use and attribution

An independent academic project using official **Statistics Canada** data. Data selection, transformation, application development and presentation are project work. Dates and revisions of the underlying official tables remain important when interpreting trends.
