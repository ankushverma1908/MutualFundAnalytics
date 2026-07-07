"""
Bluestock Fintech - Mutual Fund Analytics Capstone
B4: Markowitz Efficient Frontier - Portfolio Optimisation for 5 Selected Funds

Fund selection strategy: picks the highest-AUM fund from each of 5 different
categories (for diversification), falling back to top-5-by-AUM overall if
fewer than 5 distinct categories exist.

Outputs:
  - reports/efficient_frontier.png  (chart)
  - Printed table of optimal (max Sharpe) and minimum-volatility portfolios

Run with:
    python markowitz_efficient_frontier.py

Can also be pasted into notebooks/05_advanced_analytics.ipynb as a cell -
just skip the __main__ guard and run the functions directly.
"""

import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import os

DB_PATH = "data/db/bluestock_mf.db"
REPORTS_DIR = "reports"
RISK_FREE_RATE = 0.06  # annual, adjust if you have a specific benchmark rate
TRADING_DAYS = 252

os.makedirs(REPORTS_DIR, exist_ok=True)


def select_five_funds():
    """Pick highest-AUM fund from each of up to 5 distinct categories."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT amfi_code, scheme_name, category, aum_crore
        FROM fact_performance
        ORDER BY aum_crore DESC
        """,
        conn,
    )
    conn.close()

    selected = df.groupby("category").first().reset_index()
    selected = selected.sort_values("aum_crore", ascending=False)

    if len(selected) >= 5:
        selected = selected.head(5)
    else:
        # fallback: top 5 overall by AUM if fewer than 5 categories exist
        selected = df.head(5)

    return selected[["amfi_code", "scheme_name", "category", "aum_crore"]].reset_index(drop=True)


def load_returns_matrix(amfi_codes):
    """Build a wide DataFrame of daily returns, one column per fund, aligned by date."""
    conn = sqlite3.connect(DB_PATH)
    frames = []
    for code in amfi_codes:
        df = pd.read_sql(
            "SELECT nav_date as date, nav FROM fact_nav WHERE amfi_code = ? ORDER BY nav_date",
            conn, params=(code,),
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")["nav"].rename(code)
        frames.append(df)
    conn.close()

    prices = pd.concat(frames, axis=1).dropna()
    returns = prices.pct_change().dropna()
    return returns


def portfolio_perf(weights, mean_returns, cov_matrix):
    ret = np.sum(weights * mean_returns) * TRADING_DAYS
    vol = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(TRADING_DAYS)
    sharpe = (ret - RISK_FREE_RATE) / vol if vol != 0 else np.nan
    return ret, vol, sharpe


def negative_sharpe(weights, mean_returns, cov_matrix):
    ret, vol, sharpe = portfolio_perf(weights, mean_returns, cov_matrix)
    return -sharpe


def portfolio_volatility(weights, mean_returns, cov_matrix):
    return portfolio_perf(weights, mean_returns, cov_matrix)[1]


def optimize_portfolio(mean_returns, cov_matrix, objective_fn):
    n = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
    bounds = tuple((0, 1) for _ in range(n))  # long-only, no leverage
    init_guess = np.array([1 / n] * n)
    result = minimize(objective_fn, init_guess, args=args, method="SLSQP",
                       bounds=bounds, constraints=constraints)
    return result.x


def random_portfolios(mean_returns, cov_matrix, n_portfolios=8000):
    n = len(mean_returns)
    results = np.zeros((3, n_portfolios))
    weights_record = []
    for i in range(n_portfolios):
        w = np.random.random(n)
        w /= np.sum(w)
        weights_record.append(w)
        ret, vol, sharpe = portfolio_perf(w, mean_returns, cov_matrix)
        results[0, i] = vol
        results[1, i] = ret
        results[2, i] = sharpe
    return results, weights_record


def plot_efficient_frontier(results, max_sharpe_perf, min_vol_perf, fund_names, save_path):
    fig, ax = plt.subplots(figsize=(9, 6))
    scatter = ax.scatter(results[0], results[1], c=results[2], cmap="viridis", s=8, alpha=0.6)
    fig.colorbar(scatter, label="Sharpe Ratio")

    ax.scatter(max_sharpe_perf[1], max_sharpe_perf[0], marker="*", color="red", s=400,
               label=f"Max Sharpe (Sharpe={max_sharpe_perf[2]:.2f})", edgecolors="black", linewidths=1)
    ax.scatter(min_vol_perf[1], min_vol_perf[0], marker="*", color="blue", s=400,
               label=f"Min Volatility (Sharpe={min_vol_perf[2]:.2f})", edgecolors="black", linewidths=1)

    ax.set_xlabel("Annualized Volatility (Risk)")
    ax.set_ylabel("Annualized Return")
    ax.set_title(f"Markowitz Efficient Frontier\nFunds: {', '.join(fund_names)}")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def main():
    print("=" * 60)
    print("B4: Markowitz Efficient Frontier - Portfolio Optimisation")
    print("=" * 60)

    funds = select_five_funds()
    print("\nSelected funds (diversified by category, top AUM each):")
    print(funds.to_string(index=False))

    amfi_codes = funds["amfi_code"].tolist()
    fund_names = funds["scheme_name"].tolist()

    print("\nLoading aligned daily returns...")
    returns = load_returns_matrix(amfi_codes)
    print(f"Aligned date range: {returns.index.min().date()} to {returns.index.max().date()} "
          f"({len(returns)} trading days)")

    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values

    print("\nRunning random portfolio simulation (8000 portfolios)...")
    results, weights_record = random_portfolios(mean_returns, cov_matrix)

    print("Optimising for Max Sharpe portfolio...")
    max_sharpe_weights = optimize_portfolio(mean_returns, cov_matrix, negative_sharpe)
    max_sharpe_perf = portfolio_perf(max_sharpe_weights, mean_returns, cov_matrix)

    print("Optimising for Minimum Volatility portfolio...")
    min_vol_weights = optimize_portfolio(mean_returns, cov_matrix, portfolio_volatility)
    min_vol_perf = portfolio_perf(min_vol_weights, mean_returns, cov_matrix)

    save_path = os.path.join(REPORTS_DIR, "efficient_frontier.png")
    plot_efficient_frontier(results, max_sharpe_perf, min_vol_perf, fund_names, save_path)
    print(f"\nChart saved to: {save_path}")

    print("\n" + "=" * 60)
    print("MAX SHARPE PORTFOLIO")
    print("=" * 60)
    print(f"Expected Annual Return: {max_sharpe_perf[0]*100:.2f}%")
    print(f"Annual Volatility:      {max_sharpe_perf[1]*100:.2f}%")
    print(f"Sharpe Ratio:           {max_sharpe_perf[2]:.2f}")
    for name, w in zip(fund_names, max_sharpe_weights):
        print(f"  {name}: {w*100:.1f}%")

    print("\n" + "=" * 60)
    print("MINIMUM VOLATILITY PORTFOLIO")
    print("=" * 60)
    print(f"Expected Annual Return: {min_vol_perf[0]*100:.2f}%")
    print(f"Annual Volatility:      {min_vol_perf[1]*100:.2f}%")
    print(f"Sharpe Ratio:           {min_vol_perf[2]:.2f}")
    for name, w in zip(fund_names, min_vol_weights):
        print(f"  {name}: {w*100:.1f}%")


if __name__ == "__main__":
    main()
