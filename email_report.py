"""
Bluestock Fintech - Mutual Fund Analytics Capstone
B5: HTML Email Report

Sends a portfolio-wide HTML summary email:
  - Top 5 / Bottom 5 performing funds (1Y return)
  - Category-level average returns
  - Highlighted fund: NAV trend chart + Monte Carlo projection
  - Full fund performance table

This same script is what B1's cron job (Windows Task Scheduler) will trigger.

SETUP (one-time):
1. Enable 2-Step Verification on your Gmail account:
   https://myaccount.google.com/security
2. Create an App Password:
   https://myaccount.google.com/apppasswords
   -> Select app: "Mail", device: "Windows Computer" -> Generate
   -> Copy the 16-character password shown
3. Create a file named ".env" in this same folder (mf-analytics/mf-analytics/.env)
   with these two lines (replace with your real values):

       GMAIL_ADDRESS=youremail@gmail.com
       GMAIL_APP_PASSWORD=your16charapppassword
       REPORT_RECIPIENT=youremail@gmail.com

4. Install dependencies:
       pip install python-dotenv matplotlib pandas

5. Run:
       python email_report.py
"""

import os
import sqlite3
import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from io import BytesIO

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no GUI backend needed
import matplotlib.pyplot as plt

from dotenv import load_dotenv

load_dotenv()

DB_PATH = "data/db/bluestock_mf.db"
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT", GMAIL_ADDRESS)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# ============================================================
# DATA
# ============================================================
def get_performance_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT amfi_code, scheme_name, fund_house, category,
               return_1yr_pct, return_3yr_pct, sharpe_ratio,
               std_dev_ann_pct, max_drawdown_pct, aum_crore, morningstar_rating
        FROM fact_performance
        ORDER BY return_1yr_pct DESC
        """,
        conn,
    )
    conn.close()
    return df


def get_nav_history(amfi_code):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT nav_date as date, nav FROM fact_nav WHERE amfi_code = ? ORDER BY nav_date",
        conn, params=(amfi_code,),
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


def monte_carlo_simulation(nav_df, days=252, simulations=300, seed=42):
    np.random.seed(seed)
    returns = nav_df["nav"].pct_change().dropna()
    mu, sigma = returns.mean(), returns.std()
    last_price = nav_df["nav"].iloc[-1]
    shocks = np.random.normal(mu, sigma, size=(days, simulations))
    prices = np.full(simulations, last_price)
    sim_results = np.zeros((days, simulations))
    for d in range(days):
        prices = prices * (1 + shocks[d])
        sim_results[d] = prices
    return sim_results


# ============================================================
# CHARTS -> embedded inline images (cid)
# ============================================================
def fig_to_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def make_nav_chart(nav_df, fund_name):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(nav_df["date"], nav_df["nav"], color="#1f77b4", linewidth=1.5)
    ax.set_title(f"NAV Trend - {fund_name}", fontsize=11)
    ax.set_ylabel("NAV (Rs)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_bytes(fig)


def make_monte_carlo_chart(sim_results, fund_name):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for s in range(min(sim_results.shape[1], 60)):
        ax.plot(sim_results[:, s], linewidth=0.4, alpha=0.3, color="#2ca02c")
    ax.set_title(f"Monte Carlo Projection (1Y) - {fund_name}", fontsize=11)
    ax.set_xlabel("Trading Days Ahead")
    ax.set_ylabel("Projected NAV (Rs)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_bytes(fig)


# ============================================================
# HTML BUILD
# ============================================================
def df_to_html_table(df, cols_fmt=None):
    """Simple styled HTML table (no external CSS deps for email client safety)."""
    rows_html = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td style='padding:6px 10px;border-bottom:1px solid #eee;font-size:13px;'>{row[c]}</td>" for c in df.columns)
        rows_html += f"<tr>{cells}</tr>"
    header_html = "".join(f"<th style='padding:6px 10px;background:#0b1f3a;color:#fff;font-size:13px;text-align:left;'>{c}</th>" for c in df.columns)
    return f"<table style='border-collapse:collapse;width:100%;'><tr>{header_html}</tr>{rows_html}</table>"


def build_html_report(perf_df, highlight_fund, top5, bottom5, category_avg):
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    top5_html = df_to_html_table(top5[["scheme_name", "category", "return_1yr_pct", "sharpe_ratio"]])
    bottom5_html = df_to_html_table(bottom5[["scheme_name", "category", "return_1yr_pct", "sharpe_ratio"]])
    category_html = df_to_html_table(category_avg)

    html = f"""
    <html>
    <body style="font-family:Segoe UI,Arial,sans-serif;background:#f4f6f8;padding:20px;color:#1a1a1a;">
      <div style="max-width:720px;margin:auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <div style="background:#0b1f3a;padding:20px 24px;">
          <h1 style="color:#ffffff;margin:0;font-size:20px;">Bluestock Fintech - MF Analytics Report</h1>
          <p style="color:#9fb3d1;margin:4px 0 0;font-size:12px;">Generated {generated_at} | Ankush Kumar, Data Analyst Intern 2026</p>
        </div>

        <div style="padding:24px;">
          <h2 style="font-size:16px;color:#0b1f3a;">Top 5 Performing Funds (1Y Return)</h2>
          {top5_html}

          <h2 style="font-size:16px;color:#0b1f3a;margin-top:24px;">Bottom 5 Performing Funds (1Y Return)</h2>
          {bottom5_html}

          <h2 style="font-size:16px;color:#0b1f3a;margin-top:24px;">Average Return by Category</h2>
          {category_html}

          <h2 style="font-size:16px;color:#0b1f3a;margin-top:24px;">Spotlight Fund: {highlight_fund}</h2>
          <p style="font-size:13px;color:#444;">NAV trend and 1-year Monte Carlo projection below.</p>
          <img src="cid:nav_chart" style="width:100%;max-width:660px;border-radius:6px;margin-top:8px;" />
          <img src="cid:mc_chart" style="width:100%;max-width:660px;border-radius:6px;margin-top:12px;" />

          <p style="font-size:11px;color:#999;margin-top:28px;border-top:1px solid #eee;padding-top:12px;">
            Automated report - Bluestock Fintech Mutual Fund Analytics Capstone Project.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    return html


# ============================================================
# MAIN
# ============================================================
def main():
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("ERROR: GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set. Check your .env file.")
        return

    print("Loading performance data...")
    perf_df = get_performance_data()

    top5 = perf_df.head(5)
    bottom5 = perf_df.tail(5)
    category_avg = (
        perf_df.groupby("category")["return_1yr_pct"]
        .mean()
        .reset_index()
        .rename(columns={"return_1yr_pct": "avg_return_1yr_pct"})
        .round(2)
        .sort_values("avg_return_1yr_pct", ascending=False)
    )

    highlight_row = top5.iloc[0]
    highlight_amfi = highlight_row["amfi_code"]
    highlight_name = highlight_row["scheme_name"]

    print(f"Highlight fund: {highlight_name}")
    nav_df = get_nav_history(highlight_amfi)
    sim_results = monte_carlo_simulation(nav_df)

    nav_chart_bytes = make_nav_chart(nav_df, highlight_name)
    mc_chart_bytes = make_monte_carlo_chart(sim_results, highlight_name)

    html_body = build_html_report(perf_df, highlight_name, top5, bottom5, category_avg)

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Bluestock MF Analytics Report - {datetime.now().strftime('%d %b %Y')}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = REPORT_RECIPIENT

    msg.attach(MIMEText(html_body, "html"))

    img1 = MIMEImage(nav_chart_bytes)
    img1.add_header("Content-ID", "<nav_chart>")
    msg.attach(img1)

    img2 = MIMEImage(mc_chart_bytes)
    img2.add_header("Content-ID", "<mc_chart>")
    msg.attach(img2)

    print("Sending email...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, REPORT_RECIPIENT, msg.as_string())

    print(f"Report sent successfully to {REPORT_RECIPIENT}")


if __name__ == "__main__":
    main()
