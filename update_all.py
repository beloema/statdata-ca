import sys
import subprocess
import requests
import zipfile
from pathlib import Path

DATASETS = {
    "14100287": "employment",
    "36100434": "gdp",
    "17100009": "population",
}

API = "https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV"

def download(table, name):
    print(f"\nDownloading {name}...", flush=True)

    response = requests.get(f"{API}/{table}/en", timeout=60)
    response.raise_for_status()

    result = response.json()
    if result["status"] != "SUCCESS":
        raise RuntimeError(result)

    obj = result["object"]
    url = obj if isinstance(obj, str) else obj["downloadLink"]

    path = Path(f"data/raw/{name}.zip")
    temp = path.with_suffix(".zip.part")

    try:
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(temp, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)

        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None:
                raise RuntimeError("Corrupted ZIP")
            z.extract(f"{table}.csv", "data/raw")

        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)

    print(f"{name}: downloaded successfully", flush=True)


def run(script):
    print(f"\nRunning {script}...", flush=True)
    subprocess.run([sys.executable, f"etl/{script}"], check=True)


def main():
    for table, name in DATASETS.items():
        download(table, name)

    for script in [
        "update_cpi.py",
        "update_interest_rates.py",
        "update_exchange_rates.py",
        "update_employment.py",
        "update_gdp.py",
        "update_population.py",
    ]:
        run(script)

    print("\nSUCCESS: All 6 datasets updated!")


if __name__ == "__main__":
    main()
