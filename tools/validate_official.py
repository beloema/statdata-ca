"""Compare every stored STATDATA.CA observation against official Statistics Canada CSV.

Run `python tools/validate_official.py` to download fresh official ZIPs via the
Statistics Canada Web Data Service, or `--local` to reuse the raw CSV files.
This is deliberately independent from the ETL scripts.
"""
import argparse
import csv
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import io
from pathlib import Path
import sys
import zipfile

import psycopg2
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SNAPSHOTS = ROOT / 'data' / 'validation_sources'

TABLES = {
    'cpi': ('18100004', ('date', 'region', 'unit')),
    'interest_rates': ('10100139', ('date', 'indicator')),
    'exchange_rates': ('33100036', ('date', 'currency')),
    'employment': ('14100287', ('date', 'region', 'indicator')),
    'gdp': ('36100434', ('date', 'industry')),
    'population': ('17100009', ('date', 'region')),
}

INTEREST = {
    'Bank rate', 'Target rate',
    'Government of Canada benchmark bond yields, 2 year',
    'Government of Canada benchmark bond yields, 5 year',
    'Government of Canada benchmark bond yields, 10 year',
    'Treasury Bills, 3-month'
}
CURRENCIES = {
    'U.S. dollar, daily average': 'USD',
    'European euro, daily average': 'EUR',
    'U.K. pound sterling, daily average': 'GBP',
    'Japanese yen, daily average': 'JPY',
    'Swiss franc, daily average': 'CHF',
    'Australian dollar, daily average': 'AUD',
}
EMPLOYMENT = {
    'Employment', 'Unemployment', 'Unemployment rate',
    'Employment rate', 'Participation rate'
}
INDUSTRIES = {
    'All industries [T001]': 'All industries',
    'Goods-producing industries [T002]': 'Goods-producing industries',
    'Services-producing industries [T003]': 'Services-producing industries',
}
REGIONS = {
    'Canada', 'Newfoundland and Labrador', 'Prince Edward Island',
    'Nova Scotia', 'New Brunswick', 'Quebec', 'Ontario', 'Manitoba',
    'Saskatchewan', 'Alberta', 'British Columbia', 'Yukon',
    'Northwest Territories', 'Nunavut'
}


def official_key(table, row):
    """Return the primary-key tuple for an included official row, or None."""
    if row.get('TERMINATED', '').strip() or not row.get('VALUE', '').strip():
        return None
    date_text = row['REF_DATE']
    geo = row['GEO']
    if table == 'cpi':
        if geo != 'Canada' or row['Products and product groups'] != 'All-items':
            return None
        return (date_text + '-01', geo, row['UOM'])
    if table == 'interest_rates':
        item = row['Financial market statistics']
        if geo != 'Canada' or item not in INTEREST:
            return None
        return (date_text, item)
    if table == 'exchange_rates':
        item = row['Type of currency']
        if geo != 'Canada' or item not in CURRENCIES:
            return None
        return (date_text, CURRENCIES[item])
    if table == 'employment':
        item = row['Labour force characteristics']
        if (item not in EMPLOYMENT
            or row['Gender'] != 'Total - Gender'
            or row['Age group'] != '15 years and over'
            or row['Statistics'] != 'Estimate'
            or row['Data type'] != 'Seasonally adjusted'):
            return None
        return (date_text + '-01', geo, item)
    if table == 'gdp':
        item = row['North American Industry Classification System (NAICS)']
        if (geo != 'Canada' or item not in INDUSTRIES
            or row['Seasonal adjustment'] != 'Seasonally adjusted at annual rates'
            or row['Prices'] != 'Chained (2017) dollars'):
            return None
        return (date_text + '-01', INDUSTRIES[item])
    if table == 'population':
        if geo not in REGIONS or row['UOM'] != 'Persons':
            return None
        return (date_text, geo)
    raise ValueError(table)


def fetch_official(pid):
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    destination = SNAPSHOTS / (pid + '.zip')
    staging = SNAPSHOTS / (pid + '.zip.partial')
    url = f'https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{pid}/en'
    reply = requests.get(url, timeout=60)
    reply.raise_for_status()
    payload = reply.json()
    if payload.get('status') != 'SUCCESS':
        raise ValueError(f'Statistics Canada API failed: {payload}')
    obj = payload['object']
    download_url = obj if isinstance(obj, str) else obj['downloadLink']
    try:
        with requests.get(download_url, stream=True, timeout=300) as response:
            response.raise_for_status()
            with staging.open('wb') as stream:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        with zipfile.ZipFile(staging) as archive:
            if pid + '.csv' not in archive.namelist():
                raise ValueError(f'{pid}.csv missing from downloaded ZIP')
            if archive.testzip():
                raise ValueError(f'{pid}: corrupt ZIP')
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    return destination


def iter_source(table, pid, fresh):
    if fresh:
        path = fetch_official(pid)
        with zipfile.ZipFile(path) as archive:
            with archive.open(pid + '.csv') as data:
                with io.TextIOWrapper(data, encoding='utf-8-sig', newline='') as text:
                    yield from csv.DictReader(text)
    else:
        path = RAW / (pid + '.csv')
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding='utf-8-sig', newline='') as stream:
            yield from csv.DictReader(stream)


def official_rows(table, pid, fresh):
    result = {}
    duplicates = []
    for row in iter_source(table, pid, fresh):
        key = official_key(table, row)
        if key is None:
            continue
        try:
            value = Decimal(row['VALUE'])
        except Exception as error:
            raise ValueError(f'Non-numeric {table} value at {key}: {row["VALUE"]}') from error
        if key in result and result[key] != value:
            duplicates.append((key, result[key], value))
        result.setdefault(key, value)
    if duplicates:
        raise ValueError(f'{table}: conflicting observations: {duplicates[:3]}')
    return result


def stored_rows(conn, table, keys):
    statement = 'SELECT ' + ', '.join(keys) + ', value FROM ' + table
    result = {}
    with conn.cursor() as cursor:
        cursor.execute(statement)
        for row in cursor:
            key = tuple(v.isoformat() if isinstance(v, date) else v for v in row[:-1])
            result[key] = Decimal(row[-1])
    return result


def compare(name, official, stored):
    missing = official.keys() - stored.keys()
    extra = stored.keys() - official.keys()
    mismatches = [(key, official[key], stored[key]) for key in official.keys() & stored.keys()
                  if abs(official[key] - stored[key]) > Decimal('0.000001')]
    good = not missing and not extra and not mismatches
    print(f'{"PASS" if good else "FAIL"} {name}: {len(official):,} official / '
          f'{len(stored):,} database; missing={len(missing)}, extra={len(extra)}, '
          f'wrong_values={len(mismatches)}')
    if missing:
        print('  Official records missing from DB:', list(sorted(missing))[:3])
    if extra:
        print('  Extra database records:', list(sorted(extra))[:3])
    if mismatches:
        print('  Value mismatches:', mismatches[:3])
    return good


def calculate_inflation(cpi):
    values = {key[0]: val for key, val in cpi.items()
              if key[1] == 'Canada' and key[2] == '2002=100'}
    expected = {}
    for day, current in values.items():
        prev_date = f'{int(day[:4]) - 1}{day[4:]}'
        old = values.get(prev_date)
        if old is not None and old != 0:
            percentage = (current / old - 1) * 100
            expected[(day,)] = percentage.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return expected



def verify_calculated_api(source_data, expected_inflation):
    """Independently recompute every displayed descriptive statistic from source CSVs."""
    from dateutil.relativedelta import relativedelta
    from statistics import mean

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from app import app

    def select(table, predicate):
        return {key[0]: float(value) for key, value in source_data[table].items()
                if predicate(key)}

    series = {
        'inflation': select('cpi', lambda k: k[1:] == ('Canada', '2002=100')),
        'inflation_rate': {key[0]: float(value) for key, value in expected_inflation.items()},
        'interest_rates': select('interest_rates', lambda k: k[1] == 'Target rate'),
        'exchange_rates': select('exchange_rates', lambda k: k[1] == 'USD'),
        'employment': select('employment', lambda k: k[1:] == ('Canada', 'Unemployment rate')),
        'gdp': select('gdp', lambda k: k[1] == 'All industries'),
        'population': select('population', lambda k: k[1] == 'Canada'),
    }
    success = True
    with app.test_client() as client:
        overview_response = client.get('/api/overview')
        if overview_response.status_code != 200:
            print('FAIL overview endpoint:', overview_response.status_code)
            return False
        overview = overview_response.get_json()
        for name, records in series.items():
            if not records:
                print('FAIL analytics: no official observations:', name)
                success = False
                continue
            rows = sorted((date.fromisoformat(d), v) for d, v in records.items())
            latest_date, latest_value = rows[-1]
            cutoff = latest_date - relativedelta(years=1)
            annual = [v for d, v in rows if d > cutoff]
            previous = next((v for d, v in reversed(rows) if d <= cutoff), None)
            rate_series = name in ('inflation_rate', 'interest_rates', 'employment')
            if previous is None:
                annual_change = None
            elif rate_series:
                annual_change = round(latest_value - previous, 2)
            elif previous != 0:
                annual_change = round((latest_value / previous - 1) * 100, 2)
            else:
                annual_change = None

            response = client.get('/api/analytics/' + name)
            obj = response.get_json() if response.status_code == 200 else None
            header = overview.get(name) or {}
            issues = []
            if not obj:
                issues.append('missing analytics response')
            else:
                for key, expected, tolerance in (
                    ('latest', latest_value, 0.000001),
                    ('average_12m', round(mean(annual), 3), 0.002),
                    ('minimum_12m', min(annual), 0.000001),
                    ('maximum_12m', max(annual), 0.000001),
                ):
                    actual = obj.get(key)
                    if actual is None or abs(actual - expected) > tolerance:
                        issues.append(f'{key}: API={actual}, official={expected}')
                if obj.get('annual_change') != annual_change:
                    issues.append(f'annual_change: API={obj.get("annual_change")}, '
                                  f'official={annual_change}')
                if obj.get('observations_12m') != len(annual):
                    issues.append('observations_12m differs')
                if obj.get('date') != latest_date.isoformat():
                    issues.append('analytics latest date differs')
            if (header.get('date') != latest_date.isoformat() or
                    abs(header.get('value', float('nan')) - latest_value) > 0.000001):
                issues.append('overview latest date/value differs')
            if issues:
                print(f'FAIL API analytics {name}: ' + '; '.join(issues[:4]))
                success = False
            else:
                print(f'PASS API analytics {name}: latest, min, max, average, annual change')

        # Validate a regional derived calculation against quarterly published counts.
        response = client.get('/api/region-history/population?region=Quebec&range=5Y')
        if response.status_code != 200:
            print('FAIL Quebec population history API')
            success = False
        else:
            result = response.get_json()
            pop = source_data['population']
            for region, field in [('Quebec', 'region_values'), ('Canada', 'canada_values')]:
                values = [float(pop[(d, region)]) for d in result['dates']]
                derived = [round(v / values[0] * 100, 3) for v in values]
                if any(abs(a - b) > 0.001 for a, b in zip(derived, result[field])):
                    print(f'FAIL regional population index: {region}')
                    success = False
            if success:
                print('PASS regional population indexes: Quebec vs Canada, 5Y')
    return success

def run(local=False):
    valid = True
    source_data = {}
    with psycopg2.connect(dbname='statdata') as conn:
        for table, (pid, columns) in TABLES.items():
            print(f'Checking {table} against StatCan table {pid}...', flush=True)
            expected = official_rows(table, pid, fresh=not local)
            source_data[table] = expected
            actual = stored_rows(conn, table, columns)
            valid = compare(table, expected, actual) and valid

        expected_inflation = calculate_inflation(source_data['cpi'])
        with conn.cursor() as cursor:
            cursor.execute('SELECT date, value FROM inflation_yoy')
            actual_inflation = {(d.isoformat(),): Decimal(v) for d, v in cursor}
        valid = compare('inflation_yoy (derived from official CPI)',
                        expected_inflation, actual_inflation) and valid

    valid = verify_calculated_api(source_data, expected_inflation) and valid

    if valid:
        print('\nPASS: Official source data, CPI inflation, descriptive statistics, regional index and API values agree.')
        return 0
    print('\nFAIL: Differences found. Run python update_all.py and validate again.')
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true',
                        help='Compare the previously downloaded raw CSVs (no network)')
    args = parser.parse_args()
    try:
        sys.exit(run(local=args.local))
    except (OSError, ValueError, KeyError, psycopg2.Error, requests.RequestException) as exc:
        print(f'VALIDATION ERROR: {exc}', file=sys.stderr)
        sys.exit(2)
