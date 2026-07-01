# ============================================================
# Fund Performance Analytics — IMPROVEMENT
# Alpha, Beta + Benchmark Comparison Chart
# ============================================================

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import os

PROCESSED = "data/processed"
REPORTS   = "reports"
os.makedirs(REPORTS, exist_ok=True)

print("=" * 60)
print("Loading NAV data...")
print("=" * 60)

nav = pd.read_csv(f"{PROCESSED}/clean_nav_history.csv")
nav['nav_date'] = pd.to_datetime(nav['nav_date'])
nav.sort_values(['amfi_code', 'nav_date'], inplace=True)

print(f"Loaded {nav['amfi_code'].nunique()} funds")
print(f"Columns: {nav.columns.tolist()}")

# ── Benchmark: average daily return of all funds ─────────────
print("\nCreating benchmark...")
benchmark = nav.groupby('nav_date')['daily_return_pct'].mean().reset_index()
benchmark.columns = ['nav_date', 'benchmark_return']

# ── Alpha and Beta calculation ───────────────────────────────
print("\n" + "=" * 60)
print("Calculating Alpha and Beta...")
print("=" * 60)

results = []

for amfi_code, group in nav.groupby('amfi_code'):
    group = group.merge(benchmark, on='nav_date', how='inner')
    group = group.dropna(subset=['daily_return_pct', 'benchmark_return'])

    if len(group) < 30:
        continue

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        group['benchmark_return'],
        group['daily_return_pct']
    )

    alpha     = intercept * 252 * 100
    beta      = slope
    r_squared = r_value ** 2

    results.append({
        'amfi_code' : amfi_code,
        'alpha'     : round(alpha, 4),
        'beta'      : round(beta, 4),
        'r_squared' : round(r_squared, 4),
    })

alpha_beta_df = pd.DataFrame(results)
print(alpha_beta_df.head(10).to_string(index=False))

# Save
output = f"{REPORTS}/alpha_beta.csv"
alpha_beta_df.to_csv(output, index=False)
print(f"\nSaved: {output}")

# ── Benchmark Comparison Chart ───────────────────────────────
print("\n" + "=" * 60)
print("Creating benchmark comparison chart...")
print("=" * 60)

sharpe = pd.read_csv(f"{PROCESSED}/sharpe_values.csv")
top5_codes = sharpe.head(5)['amfi_code'].tolist()

fig, ax = plt.subplots(figsize=(14, 7))

for code in top5_codes:
    fund_data = nav[nav['amfi_code'] == code].sort_values('nav_date').copy()
    if len(fund_data) == 0:
        continue
    fund_data['cumulative'] = (1 + fund_data['daily_return_pct'].fillna(0)).cumprod() * 100
    ax.plot(fund_data['nav_date'], fund_data['cumulative'],
            label=f"Fund {code}", linewidth=2)

# Benchmark line
benchmark_sorted = benchmark.sort_values('nav_date').copy()
benchmark_sorted['cumulative'] = (1 + benchmark_sorted['benchmark_return'].fillna(0)).cumprod() * 100
ax.plot(benchmark_sorted['nav_date'], benchmark_sorted['cumulative'],
        label='Nifty 100 (Proxy)', linewidth=2.5,
        color='black', linestyle='--')

ax.set_title('Top 5 Funds vs Nifty 100 Benchmark', fontsize=16, fontweight='bold')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Cumulative Return (Base=100)', fontsize=12)
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()

chart_path = f"{REPORTS}/benchmark_comparison_chart.png"
plt.savefig(chart_path, dpi=150)
plt.close()
print(f"Saved: {chart_path}")

print("\n" + "=" * 60)
print("IMPROVEMENT COMPLETE!")
print(f"Funds analyzed: {len(alpha_beta_df)}")
print("Files created:")
print(f"  - {output}")
print(f"  - {chart_path}")
print("=" * 60)