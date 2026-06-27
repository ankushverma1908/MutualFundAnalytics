-- ============================================================
-- schema.sql  —  Day 2: SQLite Database Schema
-- Bluestock Fintech Mutual Fund Analytics Capstone
-- Run: sqlite3 data/db/bluestock_mf.db < sql/schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────
-- DIMENSION: dim_fund
-- Master list of 40 mutual fund schemes
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT,           -- Equity / Debt
    sub_category        TEXT,           -- Large Cap / Small Cap / Liquid etc.
    plan                TEXT,           -- Regular / Direct
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,           -- Low / Moderate / High / Very High
    sebi_category_code  TEXT
);

-- ────────────────────────────────────────────
-- FACT: fact_nav
-- Daily NAV for all 40 schemes (2022–2026)
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code        TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    nav_date         DATE NOT NULL,
    nav              REAL NOT NULL,
    daily_return_pct REAL,
    UNIQUE(amfi_code, nav_date)
);
CREATE INDEX idx_nav_code_date ON fact_nav(amfi_code, nav_date);

-- ────────────────────────────────────────────
-- FACT: fact_transactions
-- 32,778 investor SIP/Lumpsum/Redemption rows
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT NOT NULL,
    transaction_date    DATE NOT NULL,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT NOT NULL,  -- Sip / Lumpsum / Redemption
    amount_inr          INTEGER NOT NULL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,           -- T30 / B30
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);
CREATE INDEX idx_tx_date       ON fact_transactions(transaction_date);
CREATE INDEX idx_tx_amfi       ON fact_transactions(amfi_code);
CREATE INDEX idx_tx_investor   ON fact_transactions(investor_id);
CREATE INDEX idx_tx_state      ON fact_transactions(state);

-- ────────────────────────────────────────────
-- FACT: fact_performance
-- Pre-computed metrics per scheme
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code           TEXT PRIMARY KEY REFERENCES dim_fund(amfi_code),
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT
);

-- ────────────────────────────────────────────
-- FACT: fact_aum
-- Quarterly AUM per fund house
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            DATE NOT NULL,
    fund_house      TEXT NOT NULL,
    aum_lakh_crore  REAL,
    aum_crore       INTEGER,
    num_schemes     INTEGER,
    UNIQUE(date, fund_house)
);
CREATE INDEX idx_aum_date ON fact_aum(date);

-- ────────────────────────────────────────────
-- FACT: fact_sip_industry
-- Monthly industry-level SIP data
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_sip_industry;
CREATE TABLE fact_sip_industry (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    month                       DATE NOT NULL UNIQUE,
    sip_inflow_crore            INTEGER,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

-- ────────────────────────────────────────────
-- FACT: fact_category_inflows
-- Monthly net inflow by fund category
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_category_inflows;
CREATE TABLE fact_category_inflows (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    month            DATE NOT NULL,
    category         TEXT NOT NULL,
    net_inflow_crore REAL,
    UNIQUE(month, category)
);

-- ────────────────────────────────────────────
-- FACT: fact_folio_count
-- Quarterly industry folio counts
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_folio_count;
CREATE TABLE fact_folio_count (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    month                DATE NOT NULL UNIQUE,
    total_folios_crore   REAL,
    equity_folios_crore  REAL,
    debt_folios_crore    REAL,
    hybrid_folios_crore  REAL,
    others_folios_crore  REAL
);

-- ────────────────────────────────────────────
-- FACT: fact_portfolio_holdings
-- Top stock holdings per equity fund
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_portfolio_holdings;
CREATE TABLE fact_portfolio_holdings (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code         TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol      TEXT NOT NULL,
    stock_name        TEXT,
    sector            TEXT,
    weight_pct        REAL,
    market_value_cr   REAL,
    current_price_inr REAL,
    portfolio_date    DATE
);

-- ────────────────────────────────────────────
-- FACT: fact_benchmark_indices
-- Daily closing values for 6 benchmark indices
-- ────────────────────────────────────────────
DROP TABLE IF EXISTS fact_benchmark_indices;
CREATE TABLE fact_benchmark_indices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             DATE NOT NULL,
    index_name       TEXT NOT NULL,
    close_value      REAL NOT NULL,
    daily_return_pct REAL,
    UNIQUE(date, index_name)
);
CREATE INDEX idx_bench_date ON fact_benchmark_indices(date);

SELECT 'Schema created successfully — ' || datetime('now') AS status;
