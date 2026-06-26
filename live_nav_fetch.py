"""
live_nav_fetch.py
------------------
Fetches live/historical NAV data from the public mfapi.in API for a set of
mutual fund schemes (identified by their AMFI scheme codes) and saves each
as a raw CSV under data/raw/.

API docs: https://www.mfapi.in/
Endpoint pattern: https://api.mfapi.in/mf/<scheme_code>

Usage:
    python live_nav_fetch.py
"""

import json
import time
import logging
from pathlib import Path

import requests
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.mfapi.in/mf/{scheme_code}"
RAW_DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"
REQUEST_TIMEOUT = 15  # seconds
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2  # seconds, multiplied by attempt number

# Scheme code -> human readable name (per task spec)
SCHEMES = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip",
}


def fetch_scheme_nav(scheme_code: str) -> dict:
    """
    Fetch NAV history JSON for a single AMFI scheme code from mfapi.in.
    Retries on transient failures with simple linear backoff.
    """
    url = BASE_URL.format(scheme_code=scheme_code)
    last_exc = None

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            logger.info(f"Fetching scheme {scheme_code} (attempt {attempt}/{RETRY_ATTEMPTS})...")
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "SUCCESS" or "data" not in data:
                raise ValueError(f"Unexpected API response shape for scheme {scheme_code}")

            return data

        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            last_exc = exc
            logger.warning(f"Attempt {attempt} failed for scheme {scheme_code}: {exc}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF * attempt)

    raise RuntimeError(f"Failed to fetch scheme {scheme_code} after {RETRY_ATTEMPTS} attempts") from last_exc


def nav_json_to_dataframe(payload: dict, scheme_code: str, scheme_name: str) -> pd.DataFrame:
    """
    Convert the mfapi.in JSON payload into a tidy DataFrame with metadata
    columns attached (scheme_code, scheme_name, fund_house, scheme_type,
    scheme_category).
    """
    meta = payload.get("meta", {})
    nav_records = payload.get("data", [])

    df = pd.DataFrame(nav_records)
    if df.empty:
        logger.warning(f"No NAV records returned for scheme {scheme_code}")
        return df

    df = df.rename(columns={"date": "date", "nav": "nav"})
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    df["scheme_code"] = scheme_code
    df["scheme_name"] = scheme_name
    df["fund_house"] = meta.get("fund_house")
    df["scheme_type"] = meta.get("scheme_type")
    df["scheme_category"] = meta.get("scheme_category")

    df = df.sort_values("date").reset_index(drop=True)
    return df[["scheme_code", "scheme_name", "fund_house", "scheme_type",
               "scheme_category", "date", "nav"]]


def save_raw_csv(df: pd.DataFrame, scheme_code: str, scheme_name: str) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = scheme_name.lower().replace(" ", "_")
    out_path = RAW_DATA_DIR / f"nav_{scheme_code}_{safe_name}.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Saved {len(df):,} rows -> {out_path}")
    return out_path


def fetch_all_schemes(schemes: dict = SCHEMES) -> dict:
    """
    Fetch + save NAV history for every scheme in `schemes`.
    Returns dict of scheme_code -> DataFrame for any further in-memory use.
    Continues on individual scheme failure rather than aborting the whole run.
    """
    results = {}
    failures = []

    for scheme_code, scheme_name in schemes.items():
        try:
            payload = fetch_scheme_nav(scheme_code)
            df = nav_json_to_dataframe(payload, scheme_code, scheme_name)
            if df.empty:
                failures.append(scheme_code)
                continue
            save_raw_csv(df, scheme_code, scheme_name)
            results[scheme_code] = df
        except RuntimeError as exc:
            logger.error(str(exc))
            failures.append(scheme_code)

    logger.info(f"Done. Success: {len(results)}/{len(schemes)} schemes.")
    if failures:
        logger.warning(f"Failed schemes: {failures}")

    return results


def combine_and_save_master(results: dict) -> Path:
    """Optionally combine all fetched NAV frames into one master CSV."""
    if not results:
        logger.warning("No data to combine.")
        return None
    combined = pd.concat(results.values(), ignore_index=True)
    out_path = RAW_DATA_DIR / "nav_history_live_combined.csv"
    combined.to_csv(out_path, index=False)
    logger.info(f"Saved combined NAV file ({len(combined):,} rows) -> {out_path}")
    return out_path


if __name__ == "__main__":
    logger.info(f"Fetching live NAV data for {len(SCHEMES)} schemes from mfapi.in")
    results = fetch_all_schemes(SCHEMES)
    combine_and_save_master(results)
