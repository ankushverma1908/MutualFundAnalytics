"""
Bluestock Fintech - Mutual Fund Analytics Capstone
B2: Streamlit Dashboard

Schema (confirmed from check_schema.py):
  dim_fund             : amfi_code, scheme_name, category, sub_category, fund_house, ...
  fact_nav             : amfi_code, nav_date, nav, daily_return_pct
  fact_performance     : amfi_code, return_1yr/3yr/5yr_pct, alpha, beta, sharpe_ratio,
                          sortino_ratio, std_dev_ann_pct, max_drawdown_pct, aum_crore,
                          morningstar_rating, risk_grade
  fact_portfolio_holdings : amfi_code, stock_symbol, sector, weight_pct, ...
  fact_benchmark_indices  : date, index_name, close_value, daily_return_pct

Run with:
    streamlit run app.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

DB_PATH = "data/db/bluestock_mf.db"

st.set_page_config(page_title="Bluestock MF Analytics", layout="wide", page_icon="📈")


@st.cache_data(ttl=3600)
def load_funds():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT amfi_code, scheme_name, category, sub_category, fund_house, risk_category FROM dim_fund",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_nav_history(amfi_code):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT nav_date as date, nav, daily_return_pct
        FROM fact_nav
        WHERE amfi_code = ?
        ORDER BY nav_date
        """,
        conn, params=(amfi_code,),
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=3600)
def load_performance(amfi_code):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM fact_performance WHERE amfi_code = ?", conn, params=(amfi_code,)
    )
    conn.close()
    return df.iloc[0] if not df.empty else None


@st.cache_data(ttl=3600)
def load_holdings(amfi_code):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT stock_symbol, stock_name, sector, weight_pct, market_value_cr, portfolio_date
        FROM fact_portfolio_holdings
        WHERE amfi_code = ?
        ORDER BY weight_pct DESC
        """,
        conn, params=(amfi_code,),
    )
    conn.close()
    return df


def monte_carlo_simulation(nav_df, days=252, simulations=500, seed=42):
    """GBM-based Monte Carlo projection of future NAV (same approach as B3 notebook)."""
    np.random.seed(seed)
    returns = nav_df["nav"].pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    last_price = nav_df["nav"].iloc[-1]

    sim_results = np.zeros((days, simulations))
    shocks = np.random.normal(mu, sigma, size=(days, simulations))
    prices = np.full(simulations, last_price)
    for d in range(days):
        prices = prices * (1 + shocks[d])
        sim_results[d] = prices
    return sim_results


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("📊 Bluestock MF Analytics")
st.sidebar.caption("Ankush Kumar | Data Analyst Intern 2026")

try:
    funds_df = load_funds()
except Exception as e:
    st.error(f"Could not load dim_fund table. Error: {e}")
    st.stop()

categories = ["All"] + sorted(funds_df["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Filter by Category", categories)
if selected_category != "All":
    funds_df = funds_df[funds_df["category"] == selected_category]

fund_names = funds_df["scheme_name"].tolist()
selected_fund_name = st.sidebar.selectbox("Select Fund", fund_names)
selected_row = funds_df.loc[funds_df["scheme_name"] == selected_fund_name].iloc[0]
selected_amfi = selected_row["amfi_code"]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Fund House:** {selected_row['fund_house']}")
st.sidebar.markdown(f"**Sub-category:** {selected_row['sub_category']}")
st.sidebar.markdown(f"**Risk Category:** {selected_row['risk_category']}")

st.sidebar.markdown("---")
mc_days = st.sidebar.slider("Monte Carlo Horizon (days)", 30, 504, 252, step=30)
mc_sims = st.sidebar.slider("Monte Carlo Simulations", 100, 2000, 500, step=100)

# ============================================================
# MAIN
# ============================================================
st.title(f"📈 {selected_fund_name}")
st.caption(f"AMFI Code: {selected_amfi}  |  {selected_row['category']} - {selected_row['sub_category']}")

nav_df = load_nav_history(selected_amfi)
perf = load_performance(selected_amfi)

if nav_df.empty:
    st.warning("No NAV history found for this fund.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(
    ["📉 NAV Trend & Returns", "⚠️ Risk Metrics", "🎲 Monte Carlo Simulation", "🧺 Portfolio Holdings"]
)

# --- TAB 1: NAV TREND ---
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=nav_df["date"], y=nav_df["nav"], mode="lines", name="NAV"))
        fig.update_layout(title="NAV Over Time", xaxis_title="Date", yaxis_title="NAV (Rs)", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        latest_nav = nav_df["nav"].iloc[-1]
        first_nav = nav_df["nav"].iloc[0]
        total_return = (latest_nav / first_nav - 1) * 100
        st.metric("Latest NAV", f"Rs {latest_nav:.2f}")
        st.metric("Total Return (period)", f"{total_return:.2f}%")
        st.metric("Data Points", f"{len(nav_df)}")
        if perf is not None:
            st.metric("1Y Return", f"{perf['return_1yr_pct']:.2f}%")
            st.metric("3Y Return", f"{perf['return_3yr_pct']:.2f}%")

    st.subheader("Daily Returns Distribution")
    fig2 = px.histogram(nav_df.dropna(subset=["daily_return_pct"]), x="daily_return_pct", nbins=60)
    fig2.update_layout(height=350, xaxis_title="Daily Return (%)")
    st.plotly_chart(fig2, use_container_width=True)

# --- TAB 2: RISK METRICS (from fact_performance) ---
with tab2:
    if perf is None:
        st.warning("No performance record found for this fund in fact_performance.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sharpe Ratio", f"{perf['sharpe_ratio']:.2f}")
        c2.metric("Sortino Ratio", f"{perf['sortino_ratio']:.2f}")
        c3.metric("Alpha", f"{perf['alpha']:.2f}")
        c4.metric("Beta", f"{perf['beta']:.2f}")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Std Dev (Ann.)", f"{perf['std_dev_ann_pct']:.2f}%")
        c6.metric("Max Drawdown", f"{perf['max_drawdown_pct']:.2f}%")
        c7.metric("Morningstar Rating", f"{'*' * int(perf['morningstar_rating'])}")
        c8.metric("Risk Grade", f"{perf['risk_grade']}")

        st.markdown("---")
        c9, c10 = st.columns(2)
        c9.metric("AUM (Crore)", f"Rs {perf['aum_crore']:,}")
        c10.metric("Expense Ratio", f"{perf['expense_ratio_pct']:.2f}%")

        st.subheader("Return vs Benchmark")
        returns_data = pd.DataFrame({
            "Period": ["1Y", "3Y"],
            "Fund": [perf["return_1yr_pct"], perf["return_3yr_pct"]],
            "Benchmark (3Y)": [np.nan, perf["benchmark_3yr_pct"]],
        })
        fig3 = px.bar(returns_data.melt(id_vars="Period", var_name="Type", value_name="Return_pct"),
                      x="Period", y="Return_pct", color="Type", barmode="group")
        fig3.update_layout(height=350, yaxis_title="Return %")
        st.plotly_chart(fig3, use_container_width=True)

# --- TAB 3: MONTE CARLO ---
with tab3:
    st.caption("GBM-based projection using historical daily return mean/volatility - same method as your B3 notebook.")

    with st.spinner("Running simulation..."):
        sim_results = monte_carlo_simulation(nav_df, days=mc_days, simulations=mc_sims)

    fig4 = go.Figure()
    for s in range(min(mc_sims, 100)):
        fig4.add_trace(go.Scatter(y=sim_results[:, s], mode="lines", line=dict(width=0.5),
                                   opacity=0.3, showlegend=False))
    fig4.update_layout(title=f"Monte Carlo Simulation ({mc_sims} paths, {mc_days} days)",
                        xaxis_title="Trading Days Ahead", yaxis_title="Projected NAV (Rs)", height=450)
    st.plotly_chart(fig4, use_container_width=True)

    final_prices = sim_results[-1, :]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean Projected NAV", f"Rs {final_prices.mean():.2f}")
    c2.metric("5th Percentile", f"Rs {np.percentile(final_prices, 5):.2f}")
    c3.metric("95th Percentile", f"Rs {np.percentile(final_prices, 95):.2f}")
    c4.metric("Std Dev", f"Rs {final_prices.std():.2f}")

# --- TAB 4: PORTFOLIO HOLDINGS ---
with tab4:
    holdings_df = load_holdings(selected_amfi)
    if holdings_df.empty:
        st.info("No portfolio holdings data available for this fund.")
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            fig5 = px.pie(holdings_df.head(10), names="stock_name", values="weight_pct",
                          title="Top 10 Holdings by Weight")
            fig5.update_layout(height=400)
            st.plotly_chart(fig5, use_container_width=True)
        with col2:
            sector_df = holdings_df.groupby("sector")["weight_pct"].sum().reset_index()
            fig6 = px.pie(sector_df, names="sector", values="weight_pct", title="Sector Allocation")
            fig6.update_layout(height=400)
            st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Full Holdings")
        st.dataframe(holdings_df, use_container_width=True)

st.markdown("---")
st.caption(f"Bluestock Fintech MF Analytics Capstone | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
