"""
prepare_powerbi_data.py  —  Day 5: Prepare data for Power BI
Bluestock Fintech Mutual Fund Analytics Capstone

Creates flat, Power BI-ready CSV files in data/powerbi/
Run: python prepare_powerbi_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED    = PROJECT_ROOT / "data" / "processed"
PBI_DIR      = PROJECT_ROOT / "data" / "powerbi"
PBI_DIR.mkdir(parents=True, exist_ok=True)

print("="*55)
print("Preparing Power BI data files...")
print("="*55)

# 1. dim_fund — master table
fm = pd.read_csv(PROCESSED / "clean_fund_master.csv")
fm.to_csv(PBI_DIR / "dim_fund.csv", index=False)
print(f"✅ dim_fund.csv           {len(fm)} rows")

# 2. fact_nav — daily NAV (sample last 3 years to keep file small)
nav = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["nav_date"])
nav = nav[nav["nav_date"] >= "2022-01-01"]
nav["year"]  = nav["nav_date"].dt.year
nav["month"] = nav["nav_date"].dt.month
nav["quarter"] = nav["nav_date"].dt.quarter
nav.to_csv(PBI_DIR / "fact_nav.csv", index=False)
print(f"✅ fact_nav.csv           {len(nav):,} rows")

# 3. fact_performance — scorecard + metrics
perf = pd.read_csv(PROCESSED / "clean_scheme_performance.csv")
# merge scorecard if exists
sc_path = PROCESSED / "fund_scorecard.csv"
if sc_path.exists():
    sc = pd.read_csv(sc_path)[["amfi_code","composite_score","cagr_3yr_pct"]]
    perf = perf.merge(sc, on="amfi_code", how="left", suffixes=("","_sc"))
perf.to_csv(PBI_DIR / "fact_performance.csv", index=False)
print(f"✅ fact_performance.csv   {len(perf)} rows")

# 4. fact_transactions
tx = pd.read_csv(PROCESSED / "clean_investor_transactions.csv",
                 parse_dates=["transaction_date"])
tx["year"]  = tx["transaction_date"].dt.year
tx["month"] = tx["transaction_date"].dt.month
tx["quarter"] = tx["transaction_date"].dt.quarter
tx.to_csv(PBI_DIR / "fact_transactions.csv", index=False)
print(f"✅ fact_transactions.csv  {len(tx):,} rows")

# 5. fact_aum
aum = pd.read_csv(PROCESSED / "clean_aum_by_fund_house.csv", parse_dates=["date"])
aum["year"] = aum["date"].dt.year
aum.to_csv(PBI_DIR / "fact_aum.csv", index=False)
print(f"✅ fact_aum.csv           {len(aum)} rows")

# 6. fact_sip_industry
sip = pd.read_csv(PROCESSED / "clean_monthly_sip_inflows.csv", parse_dates=["month"])
sip["year"] = sip["month"].dt.year
sip.to_csv(PBI_DIR / "fact_sip_industry.csv", index=False)
print(f"✅ fact_sip_industry.csv  {len(sip)} rows")

# 7. fact_category_inflows
cat = pd.read_csv(PROCESSED / "clean_category_inflows.csv", parse_dates=["month"])
cat["year"] = cat["month"].dt.year
cat.to_csv(PBI_DIR / "fact_category_inflows.csv", index=False)
print(f"✅ fact_category_inflows.csv {len(cat)} rows")

# 8. fact_folio_count
fol = pd.read_csv(PROCESSED / "clean_industry_folio_count.csv", parse_dates=["month"])
fol["year"] = fol["month"].dt.year
fol.to_csv(PBI_DIR / "fact_folio_count.csv", index=False)
print(f"✅ fact_folio_count.csv   {len(fol)} rows")

# 9. fact_portfolio_holdings
ph = pd.read_csv(PROCESSED / "clean_portfolio_holdings.csv")
ph.to_csv(PBI_DIR / "fact_portfolio_holdings.csv", index=False)
print(f"✅ fact_portfolio_holdings.csv {len(ph)} rows")

# 10. fact_benchmark
bm = pd.read_csv(PROCESSED / "clean_benchmark_indices.csv", parse_dates=["date"])
bm["year"]  = bm["date"].dt.year
bm["month"] = bm["date"].dt.month
bm.to_csv(PBI_DIR / "fact_benchmark.csv", index=False)
print(f"✅ fact_benchmark.csv     {len(bm):,} rows")

# 11. KPI summary table for cards
kpi = pd.DataFrame([{
    "total_aum_lakh_crore": aum[aum["year"]==2025]["aum_lakh_crore"].sum().round(1),
    "sip_inflow_latest_crore": sip["sip_inflow_crore"].max(),
    "total_folios_crore": fol["total_folios_crore"].max(),
    "total_schemes": len(fm),
    "total_investors": tx["investor_id"].nunique(),
    "total_tx": len(tx),
}])
kpi.to_csv(PBI_DIR / "kpi_summary.csv", index=False)
print(f"✅ kpi_summary.csv        1 row (KPI cards)")

print("\n" + "="*55)
print(f"All files saved to: data/powerbi/")
print(f"Open Power BI → Get Data → Text/CSV → select each file")
print("="*55)
