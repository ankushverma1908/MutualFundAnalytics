# Mutual Fund Analytics

End-to-end mutual fund data analytics project: ingestion, NAV tracking, fund
master exploration, and (in later phases) SQL modelling and dashboarding.

## Project Structure

```
data/raw/          Raw, unmodified source CSVs and live API pulls
data/processed/    Cleaned / transformed datasets
notebooks/         Jupyter notebooks for exploration
sql/                SQL scripts (schema, queries, views)
dashboard/         Dashboard app / assets
reports/           Generated reports (data quality summaries, etc.)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Day 1: Data Ingestion

1. Place the 10 provided source CSVs into `data/raw/`.
2. Update `DATASET_FILENAMES` in `data_ingestion.py` to match your actual
   filenames (fund_master, nav_history, etc.).
3. Run:

```bash
python data_ingestion.py
```

This prints shape/dtypes/head for every dataset, explores the fund master
(fund houses, categories, sub-categories, risk grades, AMFI scheme code
structure), validates that every fund_master scheme code exists in
nav_history, and writes `reports/data_quality_summary.md`.

4. Fetch live NAV data for HDFC Top 100 Direct + 5 key bluechip schemes from
   [mfapi.in](https://www.mfapi.in/):

```bash
python live_nav_fetch.py
```

This saves one raw CSV per scheme into `data/raw/`, plus a combined file
`nav_history_live_combined.csv`.

> **Note:** `api.mfapi.in` must be reachable from wherever you run this
> script (no special auth needed — it's a free public API).

## Scripts

| File | Purpose |
|---|---|
| `data_ingestion.py` | Loads & profiles the 10 provided datasets, validates AMFI codes |
| `live_nav_fetch.py` | Pulls live NAV history from mfapi.in for 6 schemes |
| `requirements.txt` | Pinned Python dependencies |
