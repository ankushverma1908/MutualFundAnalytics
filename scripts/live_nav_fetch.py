"""
live_nav_fetch.py  —  Fetch live NAV from mfapi.in
Run: python live_nav_fetch.py
"""
import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    "125497": "hdfc_top_100_direct",
    "119551": "sbi_bluechip",
    "120503": "icici_bluechip",
    "118632": "nippon_large_cap",
    "119092": "axis_bluechip",
    "120841": "kotak_bluechip",
}

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
        df["fund_house"]  = data["meta"].get("fund_house", "")
        out = RAW_DIR / f"nav_{code}_{name}.csv"
        df.to_csv(out, index=False)
        print(f"  Saved {len(df)} rows -> {out.name}")
        all_frames.append(df)
    except Exception as e:
        print(f"  FAILED: {e}")

if all_frames:
    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(RAW_DIR / "nav_live_combined.csv", index=False)
    print(f"\nDone. Combined file: {len(combined)} rows total.")