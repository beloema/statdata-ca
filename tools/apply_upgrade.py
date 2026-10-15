"""STATDATA.CA step 43, v2. Tolerant of cosmetic changes in dashboard.html."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'app/templates/dashboard.html'
BACKEND = ROOT / 'app/__init__.py'
EXPORT_JS = ROOT / 'app/static/export.js'
REGIONAL_JS = ROOT / 'app/static/region-trend.js'
TESTS = ROOT / 'tests/test_app.py'
LOCALIZATION_JS = ROOT / 'app/static/statdata-i18n.js'
REQUIRED = [HTML, BACKEND, EXPORT_JS, REGIONAL_JS, LOCALIZATION_JS]
for file in REQUIRED:
    if not file.exists():
        raise SystemExit(f'Missing file: {file}')

html = HTML.read_text(encoding='utf-8')
backend = BACKEND.read_text(encoding='utf-8')
export_js = EXPORT_JS.read_text(encoding='utf-8')
regional_js = REGIONAL_JS.read_text(encoding='utf-8')
tests = TESTS.read_text(encoding='utf-8') if TESTS.exists() else None

if '<script src="/static/statdata-i18n.js"></script>' in html:
    print('Bilingual UI is already installed. Checking CPI inflation precision...')
else:
    old_tag = '<script src="/static/i18n.js"></script>'
    if old_tag not in html:
        raise SystemExit('Cannot locate original i18n.js tag; no changes were made.')
    html = html.replace(old_tag, '<script src="/static/statdata-i18n.js"></script>', 1)

# The visible label "Tout" must not break the All-range selector.
old_range = 'button.classList.toggle("active", button.textContent.toUpperCase() === period);'
new_range = 'button.classList.toggle("active", button.dataset.range === period);'
if old_range in html:
    html = html.replace(old_range, new_range, 1)
elif new_range not in html:
    raise SystemExit('Cannot locate range selection logic; no changes were made.')

# Insert a specific CPI inflation rule at the beginning of formatValue regardless
# of the user's whitespace, other return statements, or existing number formatting.
format_function = re.search(r'function\s+formatValue\s*\(\s*key\s*,\s*value\s*\)\s*\{', html)
if not format_function:
    raise SystemExit('Cannot locate formatValue(key, value); no changes were made.')
existing_rule = re.search(r'if\s*\(\s*key\s*===\s*[\'"]inflation_rate[\'"]\s*\)',
                          html[format_function.end(): format_function.end() + 250])
if not existing_rule:
    html = (html[:format_function.end()] +
            '\n  if (key === "inflation_rate") return value.toFixed(1) + "%";' +
            html[format_function.end():])

# Localize CSV headers and units while preserving ISO dates and raw numeric values.
old_header = '    writer.writerow(["date", "value", "unit", "source_table"])'
if old_header in backend:
    replacement = '''    lang = request.args.get("lang", "fr").lower()
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
    )'''
    backend = backend.replace(old_header, replacement, 1)
elif 'french_units = {' not in backend:
    raise SystemExit('Cannot locate the CSV header writer; no changes were made.')

if '"&lang="' not in export_js:
    match = re.search(r'"\?range="\s*\+\s*encodeURIComponent\(selectedRange\)', export_js)
    if not match:
        raise SystemExit('Cannot locate CSV export range parameter; no changes were made.')
    export_js = (export_js[:match.end()] +
                 ' + "&lang=" + encodeURIComponent(document.documentElement.lang || "fr")' +
                 export_js[match.end():])

old_columns = '["date", "region", "region_value", "canada_value", "unit"]'
if old_columns in regional_js:
    regional_js = regional_js.replace(old_columns, '''(document.documentElement.lang === "fr"
        ? ["date", "region", "valeur_region", "valeur_canada", "unite", "tableau_source"]
        : ["date", "region", "region_value", "canada_value", "unit", "source_table"])''', 1)
elif 'valeur_region' not in regional_js:
    raise SystemExit('Cannot locate regional CSV header; no changes were made.')

old_values = '''        data.dates[i],
        data.region,
        data.region_values[i],
        data.canada_values[i],
        data.unit'''
new_values = '''        data.dates[i],
        document.documentElement.lang === "fr"
          ? (window.statdataTranslateRegion?.(data.region) || data.region)
          : data.region,
        data.region_values[i],
        data.canada_values[i],
        document.documentElement.lang === "fr"
          ? (window.statdataTranslateUnit?.(data.unit) || data.unit)
          : data.unit,
        data.dataset === "employment" ? "14-10-0287-01" : "17-10-0009-01"'''
if old_values in regional_js:
    regional_js = regional_js.replace(old_values, new_values, 1)
elif 'window.statdataTranslateRegion' not in regional_js:
    raise SystemExit('Cannot locate regional CSV data rows; no changes were made.')

if tests is not None:
    original_export = 'f"/api/export/{dataset}?range=1Y"'
    if original_export in tests:
        tests = tests.replace(original_export, 'f"/api/export/{dataset}?range=1Y&lang=en"', 1)
    if 'def test_french_csv_export' not in tests:
        tests += '''\n\n@pytest.mark.parametrize("dataset", DATASETS)
def test_french_csv_export(client, dataset):
    response = client.get(f"/api/export/{dataset}?range=1Y&lang=fr")
    assert response.status_code == 200
    assert b"tableau_source" in response.data
    assert b"valeur" in response.data


def test_invalid_export_language(client):
    response = client.get("/api/export/gdp?lang=invalid")
    assert response.status_code == 400
'''

# All source checks have succeeded before making any changes. Back up originals.
updated_files = [(HTML, html), (BACKEND, backend), (EXPORT_JS, export_js),
                 (REGIONAL_JS, regional_js)]
if tests is not None:
    updated_files.append((TESTS, tests))
for path, _ in updated_files:
    backup = path.with_name(path.name + '.before-step43')
    if not backup.exists():
        shutil.copy2(path, backup)

# Use the official one-decimal CPI rate convention; PostgreSQL's numeric ROUND
# handles positive and negative values consistently with the validator.
import psycopg2
with psycopg2.connect(dbname='statdata') as connection:
    with connection.cursor() as cursor:
        cursor.execute("""
        CREATE OR REPLACE VIEW inflation_yoy AS
        SELECT
            current_cpi.date,
            'Percent' AS unit,
            ROUND((current_cpi.value / NULLIF(previous_cpi.value, 0) - 1) * 100, 1) AS value
        FROM cpi AS current_cpi
        JOIN cpi AS previous_cpi
          ON previous_cpi.date = (current_cpi.date - INTERVAL '1 year')::date
         AND previous_cpi.region = current_cpi.region
         AND previous_cpi.unit = current_cpi.unit
        WHERE current_cpi.region = 'Canada'
        """)

for path, content in updated_files:
    path.write_text(content, encoding='utf-8')

print('SUCCESS: Bilingual charts, dates, CSV exports and CPI rounding installed.')
print('Backups saved as *.before-step43 in the original directories.')
