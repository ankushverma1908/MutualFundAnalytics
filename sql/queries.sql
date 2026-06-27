-- ============================================================
-- queries.sql  —  Day 2: 10 Analytical SQL Queries
-- Bluestock Fintech Mutual Fund Analytics Capstone
-- Run inside SQLite: sqlite3 data/db/bluestock_mf.db
-- Then paste each query below
-- ============================================================

-- ────────────────────────────────────────────
-- Q1: Top 5 funds by AUM (largest schemes)
-- ────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    category,
    aum_crore,
    expense_ratio_pct,
    morningstar_rating
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- ────────────────────────────────────────────
-- Q2: Average NAV per month for each fund
--     (last 6 months only)
-- ────────────────────────────────────────────
SELECT
    f.amfi_code,
    d.scheme_name,
    strftime('%Y-%m', f.nav_date) AS month,
    ROUND(AVG(f.nav), 4)          AS avg_nav
FROM fact_nav f
JOIN dim_fund d ON f.amfi_code = d.amfi_code
WHERE f.nav_date >= date('now', '-6 months')
GROUP BY f.amfi_code, month
ORDER BY f.amfi_code, month;

-- ────────────────────────────────────────────
-- Q3: SIP inflow YoY growth by year
-- ────────────────────────────────────────────
SELECT
    strftime('%Y', month)           AS year,
    SUM(sip_inflow_crore)           AS total_sip_inflow_crore,
    ROUND(AVG(yoy_growth_pct), 2)   AS avg_yoy_growth_pct
FROM fact_sip_industry
GROUP BY year
ORDER BY year;

-- ────────────────────────────────────────────
-- Q4: Total transaction amount by state
--     (Top 10 states)
-- ────────────────────────────────────────────
SELECT
    state,
    COUNT(*)                            AS num_transactions,
    SUM(amount_inr)                     AS total_amount_inr,
    ROUND(AVG(amount_inr), 0)           AS avg_amount_inr,
    city_tier
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC
LIMIT 10;

-- ────────────────────────────────────────────
-- Q5: Funds with expense ratio below 1%
--     (cheapest Direct plan funds)
-- ────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    sub_category,
    plan,
    expense_ratio_pct,
    risk_category
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- ────────────────────────────────────────────
-- Q6: Top 5 best performing funds (3yr CAGR)
-- ────────────────────────────────────────────
SELECT
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    benchmark_3yr_pct,
    ROUND(return_3yr_pct - benchmark_3yr_pct, 2) AS alpha_over_benchmark,
    sharpe_ratio
FROM fact_performance
ORDER BY return_3yr_pct DESC
LIMIT 5;

-- ────────────────────────────────────────────
-- Q7: SIP vs Lumpsum vs Redemption split
--     (count and total amount)
-- ────────────────────────────────────────────
SELECT
    transaction_type,
    COUNT(*)                              AS num_transactions,
    SUM(amount_inr)                       AS total_amount_inr,
    ROUND(AVG(amount_inr), 0)             AS avg_amount_inr,
    ROUND(100.0 * COUNT(*) /
          SUM(COUNT(*)) OVER (), 2)       AS pct_of_total
FROM fact_transactions
GROUP BY transaction_type
ORDER BY num_transactions DESC;

-- ────────────────────────────────────────────
-- Q8: AUM growth per fund house (2022 vs 2025)
-- ────────────────────────────────────────────
SELECT
    fund_house,
    MAX(CASE WHEN strftime('%Y', date) = '2022' THEN aum_lakh_crore END) AS aum_2022,
    MAX(CASE WHEN strftime('%Y', date) = '2025' THEN aum_lakh_crore END) AS aum_2025,
    ROUND(
        (MAX(CASE WHEN strftime('%Y', date) = '2025' THEN aum_lakh_crore END) -
         MAX(CASE WHEN strftime('%Y', date) = '2022' THEN aum_lakh_crore END)) /
         MAX(CASE WHEN strftime('%Y', date) = '2022' THEN aum_lakh_crore END) * 100
    , 1) AS growth_pct
FROM fact_aum
GROUP BY fund_house
ORDER BY aum_2025 DESC;

-- ────────────────────────────────────────────
-- Q9: Investor age group vs average SIP amount
-- ────────────────────────────────────────────
SELECT
    age_group,
    COUNT(*)                        AS num_sip_transactions,
    ROUND(AVG(amount_inr), 0)       AS avg_sip_amount_inr,
    SUM(amount_inr)                 AS total_invested_inr
FROM fact_transactions
WHERE transaction_type = 'Sip'
GROUP BY age_group
ORDER BY age_group;

-- ────────────────────────────────────────────
-- Q10: Top sectors by portfolio weight
--      across all equity funds
-- ────────────────────────────────────────────
SELECT
    sector,
    COUNT(DISTINCT amfi_code)            AS num_funds_holding,
    ROUND(AVG(weight_pct), 2)            AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 0)       AS total_market_value_cr
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;
