"""
live_nav_fetch.py  —  ETL: Fetch live NAV from mfapi.in and load into fact_nav

B1 Bonus: Scheduled ETL auto-fetching NAV from mfapi.in every weekday at 8 PM.

Extract: pulls latest NAV history from mfapi.in for each tracked scheme
Transform: computes daily_return_pct, aligns column names to fact_nav schema
Load: upserts into data/db/bluestock_mf.db -> fact_nav (skips rows already present)

Run: python live_nav_fetch.py
"""
import sqlite3
import requests
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    "125497": "hdfc_top_100_direct",
    "119551": "sbi_bluechip",
    "120503": "icici_bluechip",
    "118632": "nippon_large_cap",
    "119092": "axis_bluechip",
    "120841": "kotak_bluechip",
}


def extract():
    """Fetch raw NAV history from mfapi.in for each tracked scheme."""
    all_frames = []
    for code, name in SCHEMES.items():
        print(f"Fetching {name} ({code})...")
        try:
            r = requests.get(f"https://api.mfapi.in/mf/{code}", timeout=15)
            r.raise_for_status()
            data = r.json()
            df = pd.DataFrame(data["data"])
            df["scheme_code"] = code
            df["scheme_name"] = name
            df["fund_house"] = data["meta"].get("fund_house", "")
            out = RAW_DIR / f"nav_{code}_{name}.csv"
            df.to_csv(out, index=False)
            print(f"  Saved {len(df)} rows -> {out.name}")
            all_frames.append(df)
        except Exception as e:
            print(f"  FAILED: {e}")

    if not all_frames:
        return None

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(RAW_DIR / "nav_live_combined.csv", index=False)
    print(f"\nExtract done. Combined: {len(combined)} rows total.")
    return combined


def transform(df):
    """Clean types, rename to match fact_nav schema, compute daily_return_pct."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["date", "nav"])
    df = df.rename(columns={"scheme_code": "amfi_code", "date": "nav_date"})

    df = df.sort_values(["amfi_code", "nav_date"])
    df["daily_return_pct"] = (
        df.groupby("amfi_code")["nav"].pct_change() * 100
    )

    df["nav_date"] = df["nav_date"].dt.strftime("%Y-%m-%d")
    return df[["amfi_code", "nav_date", "nav", "daily_return_pct"]]


def load(df):
    """Upsert into fact_nav, skipping rows that already exist (same amfi_code+nav_date)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    inserted, skipped = 0, 0
    for _, row in df.iterrows():
        cur.execute(
            "SELECT 1 FROM fact_nav WHERE amfi_code = ? AND nav_date = ?",
            (row["amfi_code"], row["nav_date"]),
        )
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute(
            "INSERT INTO fact_nav (amfi_code, nav_date, nav, daily_return_pct) VALUES (?, ?, ?, ?)",
            (row["amfi_code"], row["nav_date"], row["nav"], row["daily_return_pct"]),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\nLoad done. Inserted: {inserted} new rows, Skipped (already existed): {skipped}")


def main():
    print("=" * 60)
    print("B1 ETL: Fetch live NAV from mfapi.in -> fact_nav")
    print("=" * 60)

    raw = extract()
    if raw is None:
        print("No data fetched, aborting.")
        return

    clean = transform(raw)
    load(clean)

    print("\nETL run complete.")


if __name__ == "__main__":
    main()
