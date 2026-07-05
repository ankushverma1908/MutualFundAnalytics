"""
Quick DB schema inspector for bluestock_mf.db
Run this first: python check_schema.py
It will print every table and its columns so we can confirm
the Streamlit app queries match your actual schema.
"""
import sqlite3
import os

DB_PATH = "data/db/bluestock_mf.db"  # relative to project root; adjust if needed

def inspect_db(db_path):
    if not os.path.exists(db_path):
        print(f"❌ DB not found at {db_path}. Update DB_PATH in this script.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]

    if not tables:
        print("No tables found in DB.")
        return

    print(f"Found {len(tables)} table(s) in {db_path}\n")

    for table in tables:
        print(f"TABLE: {table}")
        cur.execute(f"PRAGMA table_info({table});")
        cols = cur.fetchall()
        for col in cols:
            # col = (cid, name, type, notnull, dflt_value, pk)
            print(f"   - {col[1]} ({col[2]})")
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"   Row count: {count}\n")

    conn.close()

if __name__ == "__main__":
    inspect_db(DB_PATH)
