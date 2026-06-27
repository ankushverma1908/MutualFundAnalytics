"""
db_loader.py  —  Day 2: Load Cleaned Data into SQLite
Bluestock Fintech Mutual Fund Analytics Capstone

Reads all cleaned CSVs from data/processed/ and loads them
into the SQLite database at data/db/bluestock_mf.db

Run AFTER data_cleaning.py:
    python db_loader.py
"""

import logging
import sqlite3
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED    = PROJECT_ROOT / "data" / "processed"
DB_DIR       = PROJECT_ROOT / "data" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH      = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH  = PROJECT_ROOT / "sql" / "schema.sql"


def create_db_and_schema():
    """Run schema.sql to create all tables."""
    logger.info(f"Creating database at {DB_PATH}")
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    logger.info("Schema created successfully")


def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")


def load_table(engine, csv_name: str, table_name: str,
               date_cols: list = None, dtype_map: dict = None):
    """Generic loader — reads cleaned CSV and appends to SQLite table."""
    path = PROCESSED / csv_name
    if not path.exists():
        logger.error(f"File not found: {path}  — run data_cleaning.py first")
        return

    df = pd.read_csv(path)

    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    # Drop SQLite auto-increment id if accidentally present
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))  # clear before reload

    df.to_sql(table_name, engine, if_exists="append", index=False, dtype=dtype_map)
    logger.info(f"Loaded {len(df):>7,} rows  →  {table_name}")


def verify_counts(engine):
    """Print row counts for all tables as a quick sanity check."""
    tables = [
        "dim_fund", "fact_nav", "fact_transactions", "fact_performance",
        "fact_aum", "fact_sip_industry", "fact_category_inflows",
        "fact_folio_count", "fact_portfolio_holdings", "fact_benchmark_indices"
    ]
    print("\n" + "="*45)
    print(f"{'TABLE':<30} {'ROWS':>10}")
    print("="*45)
    with engine.connect() as conn:
        for t in tables:
            try:
                n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                print(f"{t:<30} {n:>10,}")
            except Exception as e:
                print(f"{t:<30} ERROR: {e}")
    print("="*45)


if __name__ == "__main__":
    logger.info("="*55)
    logger.info("DAY 2 — DATABASE LOADING STARTED")
    logger.info("="*55)

    create_db_and_schema()
    engine = get_engine()

    load_table(engine, "clean_fund_master.csv",         "dim_fund",
               date_cols=["launch_date"])

    load_table(engine, "clean_nav_history.csv",         "fact_nav",
           date_cols=["date"])

    load_table(engine, "clean_investor_transactions.csv","fact_transactions",
               date_cols=["transaction_date"])

    load_table(engine, "clean_scheme_performance.csv",  "fact_performance")

    load_table(engine, "clean_aum_by_fund_house.csv",   "fact_aum",
               date_cols=["date"])

    load_table(engine, "clean_monthly_sip_inflows.csv", "fact_sip_industry",
               date_cols=["month"])

    load_table(engine, "clean_category_inflows.csv",    "fact_category_inflows",
               date_cols=["month"])

    load_table(engine, "clean_industry_folio_count.csv","fact_folio_count",
               date_cols=["month"])

    load_table(engine, "clean_portfolio_holdings.csv",  "fact_portfolio_holdings",
               date_cols=["portfolio_date"])

    load_table(engine, "clean_benchmark_indices.csv",   "fact_benchmark_indices",
               date_cols=["date"])

    verify_counts(engine)

    logger.info(f"Database ready: {DB_PATH}")
    logger.info("="*55)
