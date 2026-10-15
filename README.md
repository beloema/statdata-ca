# STATDATA.CA — Step 43: bilingual UI + source validation

This patch upgrades the existing project; it does **not** replace your dashboard or database.

## Install

Open Terminal in `~/Desktop/statdata-ca`, with its `.venv` activated, then run:

```bash
unzip -o ~/Downloads/statdata_step43.zip -d .
python tools/apply_upgrade.py
python -m pytest tests/ -v
```

Restart Flask if its debug auto-reloader did not restart, and hard-refresh
`http://127.0.0.1:5000/dashboard`.

## Validate against Statistics Canada

```bash
python tools/validate_official.py
```

This fetches new copies of all six official table CSV files through the Statistics
Canada Web Data Service, checks every filtered official value against PostgreSQL,
checks annual CPI inflation, and independently recomputes overview and descriptive
statistics. It also checks Quebec-vs-Canada population indexing.

For an offline comparison against the CSV files you already downloaded:

```bash
python tools/validate_official.py --local
```

If the live validation reports missing observations because Statistics Canada has
published more data since your last run, update the database and run validation again:

```bash
python update_all.py
python tools/validate_official.py
```

CSV exports use French headers and units when FR is selected; English otherwise.
The `date` column remains ISO 8601 and numeric fields stay machine-readable in
both languages. The browser translates display dates and formats chart numbers.

## Safety and recovery

The installer creates `*.before-step43` copies beside each modified file.
To roll back, restore those backups and hard-refresh the browser. Existing
`app/static/i18n.js` is retained but no longer loaded.

No domain/DNS or hosting configuration is changed by this patch.

The CPI inflation view is aligned with the **one-decimal** year-over-year rate
used in Statistics Canada publications (for example, 3.0% in August 2026).
