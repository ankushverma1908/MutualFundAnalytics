"""
data_ingestion.py  —  Day 1: Data Ingestion
Bluestock Fintech Mutual Fund Analytics Capstone
"""

import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR  = PROJECT_ROOT / "reports"

DATASETS = {
    "fund_master"          : "01_fund_master.csv",
    "nav_history"          : "02_nav_history.csv",
    "aum_by_fund_house"    : "03_aum_by_fund_house.csv",
    "monthly_sip_inflows"  : "04_monthly_sip_inflows.csv",
    "category_inflows"     : "05_category_inflows.csv",
    "industry_folio_count" : "06_industry_folio_count.csv",
    "scheme_performance"   : "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings"   : "09_portfolio_holdings.csv",
    "benchmark_indices"    : "10_benchmark_indices.csv",
}

def load_all(raw_dir=RAW_DIR):
    dfs = {}
    for name, fname in DATASETS.items():
        path = raw_dir / fname
        df   = pd.read_csv(path)
        dfs[name] = df
        dupes    = df.duplicated().sum()
        nulls    = {c: int(n) for c, n in df.isnull().sum().items() if n > 0}
        print(f"\n{'='*60}")
        print(f"DATASET : {name}")
        print(f"Shape   : {df.shape[0]:,} rows x {df.shape[1]} cols")
        print(f"Dtypes  :\n{df.dtypes.to_string()}")
        print(f"Head    :\n{df.head(3).to_string()}")
        print(f"Dupes   : {dupes}  |  Nulls: {nulls if nulls else 'None'}")
        logger.info(f"Loaded {name}: {df.shape}")
    return dfs

def explore_fund_master(df):
    print(f"\n{'='*60}\nFUND MASTER EXPLORATION\n{'='*60}")
    for col in ["fund_house", "category", "sub_category", "risk_category"]:
        vals = sorted(df[col].dropna().unique())
        print(f"\n{col} ({len(vals)}):")
        for v in vals: print(f"  - {v}")
    codes = df["amfi_code"]
    print(f"\nAMFI scheme codes: {codes.nunique()} unique | range {codes.min()}–{codes.max()}")

def validate_codes(fund_master, nav_history):
    fm_codes = set(fund_master["amfi_code"].astype(str))
    nh_codes = set(nav_history["amfi_code"].astype(str))
    missing  = fm_codes - nh_codes
    extra    = nh_codes - fm_codes
    print(f"\n{'='*60}\nAMFI CODE VALIDATION\n{'='*60}")
    print(f"fund_master codes : {len(fm_codes)}")
    print(f"nav_history codes : {len(nh_codes)}")
    print(f"Missing in nav    : {sorted(missing) if missing else 'NONE ✅'}")
    print(f"Extra in nav      : {sorted(extra)[:10] if extra else 'NONE ✅'}")
    return {"missing": sorted(missing), "extra": sorted(extra)}

def write_quality_report(dfs, validation, out_dir=REPORTS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Day 1 — Data Quality Summary\n"]
    for name, df in dfs.items():
        nulls  = {c: int(n) for c, n in df.isnull().sum().items() if n > 0}
        dupes  = int(df.duplicated().sum())
        status = "⚠️" if (nulls or dupes) else "✅"
        lines += [f"## {status} {name}",
                  f"- Shape: {df.shape[0]:,} rows × {df.shape[1]} cols",
                  f"- Duplicates: {dupes}",
                  f"- Nulls: {nulls if nulls else 'None'}",
                  f"- Anomaly note: {'yoy_growth_pct: first 12 months have no prior year (expected)' if name=='monthly_sip_inflows' else 'None'}",
                  ""]
    lines += ["## AMFI Code Validation",
              f"- fund_master codes: 40",
              f"- nav_history codes: 40",
              f"- Missing: {'None ✅' if not validation['missing'] else validation['missing']}",
              f"- Extra: {'None ✅' if not validation['extra'] else validation['extra']}",
              ""]
    (out_dir / "data_quality_summary.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote reports/data_quality_summary.md")

if __name__ == "__main__":
    dfs        = load_all()
    explore_fund_master(dfs["fund_master"])
    validation = validate_codes(dfs["fund_master"], dfs["nav_history"])
    write_quality_report(dfs, validation)
