# Day 1 — Data Quality Summary

## ✅ fund_master
- Shape: 40 rows × 15 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ nav_history
- Shape: 46,000 rows × 3 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ aum_by_fund_house
- Shape: 90 rows × 5 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ⚠️ monthly_sip_inflows
- Shape: 48 rows × 6 cols
- Duplicates: 0
- Nulls: {'yoy_growth_pct': 12}
- Anomaly note: yoy_growth_pct: first 12 months have no prior year (expected)

## ✅ category_inflows
- Shape: 144 rows × 3 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ industry_folio_count
- Shape: 21 rows × 6 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ scheme_performance
- Shape: 40 rows × 19 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ investor_transactions
- Shape: 32,778 rows × 13 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ portfolio_holdings
- Shape: 322 rows × 8 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## ✅ benchmark_indices
- Shape: 8,050 rows × 3 cols
- Duplicates: 0
- Nulls: None
- Anomaly note: None

## AMFI Code Validation
- fund_master codes: 40
- nav_history codes: 40
- Missing: None ✅
- Extra: None ✅
