"""
data_cleaning.py  —  Day 2: Data Cleaning
Bluestock Fintech Mutual Fund Analytics Capstone

Cleans all 10 raw datasets and saves to data/processed/
Run: python data_cleaning.py
"""

import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
OUT_DIR      = PROJECT_ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. FUND MASTER
# ─────────────────────────────────────────────
def clean_fund_master():
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv")

    df["amfi_code"]   = df["amfi_code"].astype(str).str.strip()
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df["fund_house"]  = df["fund_house"].str.strip()
    df["scheme_name"] = df["scheme_name"].str.strip()
    df["category"]    = df["category"].str.strip()
    df["sub_category"]= df["sub_category"].str.strip()
    df["plan"]        = df["plan"].str.strip()
    df["risk_category"]= df["risk_category"].str.strip()

    # Validate expense ratio range
    bad_expense = df[(df["expense_ratio_pct"] < 0) | (df["expense_ratio_pct"] > 3)]
    if not bad_expense.empty:
        logger.warning(f"Unusual expense ratios: {bad_expense[['scheme_name','expense_ratio_pct']]}")

    out = OUT_DIR / "clean_fund_master.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_fund_master.csv  →  {df.shape[0]} rows, {df.shape[1]} cols")
    return df

# ─────────────────────────────────────────────
# 2. NAV HISTORY
# ─────────────────────────────────────────────
def clean_nav_history():
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")

    df["amfi_code"] = df["amfi_code"].astype(str).str.strip()
    df["date"]      = pd.to_datetime(df["date"], errors="coerce")
    df["nav"]       = pd.to_numeric(df["nav"], errors="coerce")

    # Drop rows with invalid date or nav
    before = len(df)
    df.dropna(subset=["date", "nav"], inplace=True)
    dropped = before - len(df)
    if dropped:
        logger.warning(f"NAV history: dropped {dropped} rows with null date/nav")

    # Remove duplicates (same fund + same date)
    df.drop_duplicates(subset=["amfi_code", "date"], inplace=True)

    # Remove NAV <= 0
    df = df[df["nav"] > 0]

    # Sort
    df.sort_values(["amfi_code", "date"], inplace=True)

    # Forward-fill missing business days per fund
    all_dates = pd.date_range(df["date"].min(), df["date"].max(), freq="B")
    filled_frames = []
    for code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date").reindex(all_dates)
        grp["amfi_code"] = code
        grp["nav"]       = grp["nav"].ffill()
        grp = grp.dropna(subset=["nav"]).reset_index().rename(columns={"index": "date"})
        filled_frames.append(grp)

    df_filled = pd.concat(filled_frames, ignore_index=True)
    df_filled = df_filled.rename(columns={"date": "nav_date"})

    # Compute daily return
    df_filled["daily_return_pct"] = (
        df_filled.groupby("amfi_code")["nav"]
        .pct_change()
        .round(6)
    )

    out = OUT_DIR / "clean_nav_history.csv"
    df_filled.to_csv(out, index=False)
    logger.info(f"clean_nav_history.csv  →  {df_filled.shape[0]:,} rows, {df_filled.shape[1]} cols")
    return df_filled

# ─────────────────────────────────────────────
# 3. AUM BY FUND HOUSE
# ─────────────────────────────────────────────
def clean_aum():
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")

    df["date"]       = pd.to_datetime(df["date"], errors="coerce")
    df["fund_house"] = df["fund_house"].str.strip()
    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["aum_crore"]      = pd.to_numeric(df["aum_crore"], errors="coerce")
    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_aum_by_fund_house.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_aum_by_fund_house.csv  →  {df.shape[0]} rows")
    return df

# ─────────────────────────────────────────────
# 4. MONTHLY SIP INFLOWS
# ─────────────────────────────────────────────
def clean_sip_inflows():
    df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")

    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df.sort_values("month", inplace=True)

    # yoy_growth_pct: first 12 months are null by design — fill with 0 for DB storage
    df["yoy_growth_pct"] = df["yoy_growth_pct"].fillna(0.0)

    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_monthly_sip_inflows.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_monthly_sip_inflows.csv  →  {df.shape[0]} rows")
    return df

# ─────────────────────────────────────────────
# 5. CATEGORY INFLOWS
# ─────────────────────────────────────────────
def clean_category_inflows():
    df = pd.read_csv(RAW_DIR / "05_category_inflows.csv")

    df["month"]    = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df["category"] = df["category"].str.strip()
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_category_inflows.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_category_inflows.csv  →  {df.shape[0]} rows")
    return df

# ─────────────────────────────────────────────
# 6. INDUSTRY FOLIO COUNT
# ─────────────────────────────────────────────
def clean_folio_count():
    df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")

    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    for col in df.columns:
        if col != "month":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_industry_folio_count.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_industry_folio_count.csv  →  {df.shape[0]} rows")
    return df

# ─────────────────────────────────────────────
# 7. SCHEME PERFORMANCE
# ─────────────────────────────────────────────
def clean_scheme_performance():
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")

    df["amfi_code"]   = df["amfi_code"].astype(str).str.strip()
    df["scheme_name"] = df["scheme_name"].str.strip()
    df["fund_house"]  = df["fund_house"].str.strip()

    # Validate numeric ranges
    numeric_cols = [
        "return_1yr_pct","return_3yr_pct","return_5yr_pct",
        "alpha","beta","sharpe_ratio","sortino_ratio",
        "std_dev_ann_pct","max_drawdown_pct","expense_ratio_pct"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag suspicious values
    neg_sharpe = df[df["sharpe_ratio"] < 0]
    if not neg_sharpe.empty:
        logger.warning(f"Negative Sharpe ratios found: {neg_sharpe['scheme_name'].tolist()}")

    out_of_range_exp = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    if not out_of_range_exp.empty:
        logger.warning(f"Expense ratio out of range: {out_of_range_exp['scheme_name'].tolist()}")

    out = OUT_DIR / "clean_scheme_performance.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_scheme_performance.csv  →  {df.shape[0]} rows, {df.shape[1]} cols")
    return df

# ─────────────────────────────────────────────
# 8. INVESTOR TRANSACTIONS
# ─────────────────────────────────────────────
def clean_investor_transactions():
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amfi_code"]        = df["amfi_code"].astype(str).str.strip()
    df["amount_inr"]       = pd.to_numeric(df["amount_inr"], errors="coerce")

    # Standardise transaction_type casing
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    valid_types = {"Sip", "Lumpsum", "Redemption"}
    invalid = df[~df["transaction_type"].isin(valid_types)]
    if not invalid.empty:
        logger.warning(f"Unknown transaction types: {invalid['transaction_type'].unique()}")

    # Remove zero / negative amounts
    before = len(df)
    df = df[df["amount_inr"] > 0]
    logger.info(f"Removed {before - len(df)} zero/negative amount rows")

    # Validate KYC status
    df["kyc_status"] = df["kyc_status"].str.strip().str.title()

    # Standardise city tier
    df["city_tier"] = df["city_tier"].str.upper().str.strip()

    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_investor_transactions.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_investor_transactions.csv  →  {df.shape[0]:,} rows, {df.shape[1]} cols")
    return df

# ─────────────────────────────────────────────
# 9. PORTFOLIO HOLDINGS
# ─────────────────────────────────────────────
def clean_portfolio_holdings():
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")

    df["amfi_code"]      = df["amfi_code"].astype(str).str.strip()
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
    df["weight_pct"]     = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["market_value_cr"]= pd.to_numeric(df["market_value_cr"], errors="coerce")
    df["stock_symbol"]   = df["stock_symbol"].str.strip().str.upper()
    df["sector"]         = df["sector"].str.strip()
    df.drop_duplicates(inplace=True)

    out = OUT_DIR / "clean_portfolio_holdings.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_portfolio_holdings.csv  →  {df.shape[0]} rows")
    return df

# ─────────────────────────────────────────────
# 10. BENCHMARK INDICES
# ─────────────────────────────────────────────
def clean_benchmark_indices():
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")

    df["date"]        = pd.to_datetime(df["date"], errors="coerce")
    df["index_name"]  = df["index_name"].str.strip()
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

    df.drop_duplicates(subset=["date", "index_name"], inplace=True)
    df.sort_values(["index_name", "date"], inplace=True)

    # Compute daily return per index
    df["daily_return_pct"] = (
        df.groupby("index_name")["close_value"]
        .pct_change()
        .round(6)
    )

    out = OUT_DIR / "clean_benchmark_indices.csv"
    df.to_csv(out, index=False)
    logger.info(f"clean_benchmark_indices.csv  →  {df.shape[0]:,} rows")
    return df


if __name__ == "__main__":
    logger.info("=" * 55)
    logger.info("DAY 2 — DATA CLEANING STARTED")
    logger.info("=" * 55)

    clean_fund_master()
    clean_nav_history()
    clean_aum()
    clean_sip_inflows()
    clean_category_inflows()
    clean_folio_count()
    clean_scheme_performance()
    clean_investor_transactions()
    clean_portfolio_holdings()
    clean_benchmark_indices()

    logger.info("=" * 55)
    logger.info("ALL 10 DATASETS CLEANED → data/processed/")
    logger.info("=" * 55)
