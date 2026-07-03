import pandas as pd
import sqlite3

conn = sqlite3.connect('data/db/bluestock_mf.db')
fund_master = pd.read_sql("SELECT * FROM dim_fund", conn)
perf = pd.read_sql("SELECT * FROM fact_performance", conn)

def recommend_funds(risk_appetite):
    filtered = fund_master[fund_master["risk_category"] == risk_appetite][["amfi_code", "scheme_name"]]
    merged = filtered.merge(perf[["amfi_code", "sharpe_ratio", "return_1yr_pct"]], on="amfi_code", how="left")
    merged = merged.dropna(subset=["sharpe_ratio"])
    return merged.nlargest(3, "sharpe_ratio")[["scheme_name", "sharpe_ratio", "return_1yr_pct"]]

risk = input("Enter risk appetite (Low/Moderate/High): ")
print(recommend_funds(risk))
