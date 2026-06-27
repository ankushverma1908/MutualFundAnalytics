# Data Dictionary
## Bluestock Fintech — Mutual Fund Analytics Capstone

---

## 01_fund_master.csv / dim_fund

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| amfi_code | TEXT | Unique AMFI scheme code (Primary Key) | 119551 |
| fund_house | TEXT | Asset Management Company name | SBI Mutual Fund |
| scheme_name | TEXT | Full official AMFI scheme name | SBI Bluechip Fund - Regular Plan |
| category | TEXT | Broad asset class: Equity / Debt | Equity |
| sub_category | TEXT | SEBI sub-category | Large Cap |
| plan | TEXT | Regular or Direct plan | Regular |
| launch_date | DATE | Fund inception date | 2006-02-14 |
| benchmark | TEXT | Official benchmark index | NIFTY 100 TRI |
| expense_ratio_pct | REAL | Annual expense ratio % | 1.54 |
| exit_load_pct | REAL | Exit load charged on redemption % | 1.0 |
| min_sip_amount | INT | Minimum SIP instalment (Rs.) | 500 |
| min_lumpsum_amount | INT | Minimum lumpsum investment (Rs.) | 1000 |
| fund_manager | TEXT | Primary fund manager name | Sohini Andani |
| risk_category | TEXT | SEBI risk label | Moderate |
| sebi_category_code | TEXT | Internal SEBI code | EC01 |

---

## 02_nav_history.csv / fact_nav

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| amfi_code | TEXT | Foreign key to dim_fund | 119551 |
| date | DATE | Business day NAV date | 2022-01-03 |
| nav | REAL | Net Asset Value in Rs. | 54.3856 |
| daily_return_pct | REAL | Day-on-day return % (computed in cleaning) | 0.0042 |

**Notes:** 46,000 rows covering Jan 2022–May 2026. Forward-filled for weekends/holidays. NAV anchored to real mfapi.in values.

---

## 03_aum_by_fund_house.csv / fact_aum

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| date | DATE | Quarter-end date | 2022-03-31 |
| fund_house | TEXT | AMC name | SBI Mutual Fund |
| aum_lakh_crore | REAL | AUM in Rs. lakh crore | 6.05 |
| aum_crore | INT | AUM in Rs. crore | 605000 |
| num_schemes | INT | Number of schemes managed | 186 |

**Notes:** 90 rows, quarterly frequency, 10 fund houses × 9 quarters (2022–2025).

---

## 04_monthly_sip_inflows.csv / fact_sip_industry

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| month | DATE | Month (YYYY-MM) | 2022-01 |
| sip_inflow_crore | INT | Total SIP inflow (Rs. crore) | 11517 |
| active_sip_accounts_crore | REAL | Active SIP accounts in crore | 4.91 |
| new_sip_accounts_lakh | REAL | New SIP registrations (lakh) | 9.1 |
| sip_aum_lakh_crore | REAL | SIP AUM (Rs. lakh crore) | 4.80 |
| yoy_growth_pct | REAL | YoY growth % in SIP inflow | 15.3 |

**Notes:** 48 rows (Jan 2022–Dec 2025). First 12 months have yoy_growth_pct = 0 (no prior year baseline).

---

## 05_category_inflows.csv / fact_category_inflows

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| month | DATE | Month (YYYY-MM) | 2024-04 |
| category | TEXT | Fund category | Large Cap |
| net_inflow_crore | REAL | Net inflow Rs. crore (can be negative) | 2413.0 |

**Notes:** 144 rows = 12 categories × 12 months (FY2024-25).

---

## 06_industry_folio_count.csv / fact_folio_count

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| month | DATE | Snapshot month | 2022-01 |
| total_folios_crore | REAL | Total MF folios (crore) | 13.26 |
| equity_folios_crore | REAL | Equity fund folios (crore) | 9.28 |
| debt_folios_crore | REAL | Debt fund folios (crore) | 1.86 |
| hybrid_folios_crore | REAL | Hybrid fund folios (crore) | 0.80 |
| others_folios_crore | REAL | Other fund folios (crore) | 1.33 |

---

## 07_scheme_performance.csv / fact_performance

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| amfi_code | TEXT | Primary key | 119551 |
| return_1yr_pct | REAL | 1-year absolute return % | 12.42 |
| return_3yr_pct | REAL | 3-year CAGR % | 12.36 |
| return_5yr_pct | REAL | 5-year CAGR % | 14.45 |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR % | 11.49 |
| alpha | REAL | Return above benchmark | 0.87 |
| beta | REAL | Market sensitivity (1.0 = market) | 0.89 |
| sharpe_ratio | REAL | Risk-adjusted return (higher = better) | 0.88 |
| sortino_ratio | REAL | Downside-only risk-adjusted return | 1.29 |
| std_dev_ann_pct | REAL | Annualised standard deviation % | 14.0 |
| max_drawdown_pct | REAL | Worst peak-to-trough decline % | -21.70 |
| aum_crore | INT | Scheme AUM in Rs. crore | 14288 |
| expense_ratio_pct | REAL | Annual expense ratio % | 1.54 |
| morningstar_rating | INT | Star rating 1–5 | 4 |
| risk_grade | TEXT | Risk classification | Moderate |

---

## 08_investor_transactions.csv / fact_transactions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| investor_id | TEXT | Unique investor ID | INV003054 |
| transaction_date | DATE | Date of transaction | 2024-01-01 |
| amfi_code | TEXT | Fund invested in | 119092 |
| transaction_type | TEXT | Sip / Lumpsum / Redemption | Sip |
| amount_inr | INT | Transaction amount (Rs.) | 1834 |
| state | TEXT | Investor's state | Telangana |
| city | TEXT | Investor's city | Hyderabad |
| city_tier | TEXT | T30 (top 30 cities) or B30 | T30 |
| age_group | TEXT | Age bracket | 56+ |
| gender | TEXT | Male / Female | Female |
| annual_income_lakh | REAL | Annual income (Rs. lakh) | 77.1 |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque | UPI |
| kyc_status | TEXT | Verified / Pending | Verified |

**Notes:** 32,778 rows. 5,000 unique investors. 92% KYC Verified. Amount range ₹400–₹5,97,498.

---

## 09_portfolio_holdings.csv / fact_portfolio_holdings

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| amfi_code | TEXT | Fund holding these stocks | 119551 |
| stock_symbol | TEXT | NSE ticker symbol | POWERGRID |
| stock_name | TEXT | Company name | Power Grid Corporation |
| sector | TEXT | Sector classification | Utilities |
| weight_pct | REAL | % weight in portfolio | 13.85 |
| market_value_cr | REAL | Market value in Rs. crore | 737.09 |
| current_price_inr | REAL | Stock price in Rs. | 6011.08 |
| portfolio_date | DATE | Holdings as-of date | 2025-12-31 |

---

## 10_benchmark_indices.csv / fact_benchmark_indices

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| date | DATE | Trading day | 2022-01-03 |
| index_name | TEXT | Index name | NIFTY50 |
| close_value | REAL | Closing index value | 17492.79 |
| daily_return_pct | REAL | Day-on-day return % (computed) | 0.0011 |

**Notes:** 8,050 rows. Multiple indices in long format: NIFTY50, NIFTY100, NiftyMidcap150, BSESmallCap, CRISILLiquid, CRISILGilt.

---

## AMFI Code Reference (10 Key Schemes)

| AMFI Code | Scheme | Fund House |
|-----------|--------|------------|
| 119551 | SBI Bluechip Fund - Regular | SBI MF |
| 119552 | SBI Bluechip Fund - Direct | SBI MF |
| 125497 | HDFC Top 100 Fund - Direct | HDFC MF |
| 120503 | ICICI Pru Bluechip - Direct | ICICI Pru MF |
| 118632 | Nippon Large Cap - Direct | Nippon India MF |
| 119092 | Axis Bluechip - Direct | Axis MF |
| 120841 | Kotak Bluechip - Direct | Kotak MF |
