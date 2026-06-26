"""
data_ingestion.py
------------------
Day 1 data ingestion script for the Mutual Fund Analytics project.

What it does:
  1. Loads all CSV datasets found in data/raw/ using pandas.
  2. Prints .shape, .dtypes, and .head() for each, and flags common anomalies
     (nulls, duplicate rows, suspicious dtypes, etc.).
  3. Explores the fund master file: unique fund houses, categories,
     sub-categories, risk grades, and AMFI scheme code structure.
  4. Validates that every AMFI scheme code in fund_master exists in
     nav_history, and writes a short data quality summary to
     reports/data_quality_summary.md.

Expected input files (place in data/raw/, adjust DATASET_FILENAMES below to
match your actual filenames):
    fund_master.csv
    nav_history.csv
    ... + 8 more supporting datasets

Usage:
    python data_ingestion.py
"""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ---------------------------------------------------------------------------
# IMPORTANT: Update this list/mapping once your actual 10 CSV filenames are
# known. Keys are short logical names used elsewhere in the pipeline; values
# are the actual filenames expected in data/raw/.
# ---------------------------------------------------------------------------
DATASET_FILENAMES = {
    "fund_master": "fund_master.csv",
    "nav_history": "nav_history.csv",
    # "scheme_returns": "scheme_returns.csv",
    # "aum_data": "aum_data.csv",
    # "portfolio_holdings": "portfolio_holdings.csv",
    # "benchmark_index": "benchmark_index.csv",
    # "expense_ratio": "expense_ratio.csv",
    # "risk_metrics": "risk_metrics.csv",
    # "sip_returns": "sip_returns.csv",
    # "investor_transactions": "investor_transactions.csv",
}

# Columns we expect to identify AMFI scheme codes by, checked in order
SCHEME_CODE_CANDIDATES = ["scheme_code", "amfi_code", "scheme_code_amfi", "code"]


def discover_csv_files(raw_dir: Path) -> list[Path]:
    """Return all .csv files present in the raw data directory."""
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return []
    return sorted(raw_dir.glob("*.csv"))


def load_dataset(path: Path) -> pd.DataFrame:
    """Load a single CSV, trying a couple of encodings if needed."""
    for encoding in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            logger.error(f"Failed to load {path.name}: {exc}")
            raise
    raise RuntimeError(f"Could not decode {path.name} with utf-8 or latin-1")


def profile_dataset(name: str, df: pd.DataFrame) -> dict:
    """
    Print shape, dtypes, head for a dataset and return a dict of anomaly
    flags for the data quality summary.
    """
    print(f"\n{'=' * 70}")
    print(f"DATASET: {name}")
    print(f"{'=' * 70}")
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nHead:\n{df.head()}")

    n_dupes = df.duplicated().sum()
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    fully_null_cols = df.columns[df.isnull().all()].tolist()
    single_value_cols = [c for c in df.columns if df[c].nunique(dropna=True) == 1]

    anomalies = []
    if n_dupes:
        anomalies.append(f"{n_dupes:,} duplicate rows")
    if not cols_with_nulls.empty:
        anomalies.append(f"null values in columns: {dict(cols_with_nulls)}")
    if fully_null_cols:
        anomalies.append(f"fully null columns: {fully_null_cols}")
    if single_value_cols:
        anomalies.append(f"single-value (constant) columns: {single_value_cols}")
    if df.empty:
        anomalies.append("dataset is EMPTY")

    if anomalies:
        print("\nAnomalies detected:")
        for a in anomalies:
            print(f"  - {a}")
    else:
        print("\nNo obvious anomalies detected.")

    return {
        "name": name,
        "shape": df.shape,
        "n_duplicates": int(n_dupes),
        "null_columns": dict(cols_with_nulls),
        "fully_null_columns": fully_null_cols,
        "anomalies": anomalies,
    }


def load_all_datasets(raw_dir: Path = RAW_DIR) -> dict:
    """
    Load every CSV in data/raw/, profile each, and return a dict of
    {logical_or_file_name: DataFrame}.
    """
    csv_files = discover_csv_files(raw_dir)

    if not csv_files:
        logger.warning(
            f"No CSV files found in {raw_dir}. "
            "Place your 10 provided datasets there before running this script."
        )
        return {}

    if len(csv_files) < 10:
        logger.warning(
            f"Expected 10 datasets, found {len(csv_files)} CSV file(s) in {raw_dir}. "
            "Double check all files were copied in."
        )

    datasets = {}
    profiles = []

    for path in csv_files:
        logger.info(f"Loading {path.name} ...")
        df = load_dataset(path)
        key = path.stem
        datasets[key] = df
        profiles.append(profile_dataset(key, df))

    return datasets, profiles


def find_scheme_code_column(df: pd.DataFrame) -> str | None:
    """Identify which column in a dataframe holds the AMFI scheme code."""
    for candidate in SCHEME_CODE_CANDIDATES:
        if candidate in df.columns:
            return candidate
    # Fallback: any column with 'scheme' and 'code' in the name
    for col in df.columns:
        lc = col.lower()
        if "scheme" in lc and "code" in lc:
            return col
    return None


def explore_fund_master(df: pd.DataFrame) -> dict:
    """
    Print unique fund houses, categories, sub-categories, risk grades,
    and inspect the AMFI scheme code structure.
    """
    print(f"\n{'=' * 70}")
    print("FUND MASTER EXPLORATION")
    print(f"{'=' * 70}")

    summary = {}

    col_map = {
        "fund_house": ["fund_house", "amc", "amc_name", "fund_house_name"],
        "category": ["category", "scheme_category", "fund_category"],
        "sub_category": ["sub_category", "subcategory", "scheme_sub_category"],
        "risk_grade": ["risk_grade", "risk", "riskometer", "risk_level"],
    }

    for logical_name, candidates in col_map.items():
        actual_col = next((c for c in candidates if c in df.columns), None)
        if actual_col is None:
            print(f"\n{logical_name}: column not found (looked for {candidates})")
            continue
        uniques = sorted(df[actual_col].dropna().unique().tolist())
        print(f"\nUnique {logical_name} ({actual_col}) — {len(uniques)} values:")
        for v in uniques:
            print(f"  - {v}")
        summary[logical_name] = uniques

    scheme_code_col = find_scheme_code_column(df)
    if scheme_code_col:
        codes = df[scheme_code_col].dropna()
        print(f"\nAMFI scheme code column: '{scheme_code_col}'")
        print(f"  Count: {len(codes):,}")
        print(f"  Unique: {codes.nunique():,}")
        print(f"  Dtype: {codes.dtype}")
        print(f"  Sample: {codes.head(10).tolist()}")
        print(f"  Min/Max: {codes.min()} / {codes.max()}")
        summary["scheme_code_column"] = scheme_code_col
        summary["scheme_code_count"] = int(len(codes))
        summary["scheme_code_unique"] = int(codes.nunique())
    else:
        print("\nNo scheme code column identified in fund_master.")

    return summary


def validate_scheme_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame) -> dict:
    """
    Confirm every AMFI scheme code in fund_master exists in nav_history.
    Returns a dict summary of the validation result.
    """
    fm_col = find_scheme_code_column(fund_master)
    nh_col = find_scheme_code_column(nav_history)

    if fm_col is None or nh_col is None:
        msg = "Could not identify scheme code columns in one or both datasets."
        logger.error(msg)
        return {"error": msg}

    fm_codes = set(fund_master[fm_col].dropna().astype(str).str.strip())
    nh_codes = set(nav_history[nh_col].dropna().astype(str).str.strip())

    missing_in_nav = sorted(fm_codes - nh_codes)
    extra_in_nav = sorted(nh_codes - fm_codes)

    print(f"\n{'=' * 70}")
    print("AMFI SCHEME CODE VALIDATION")
    print(f"{'=' * 70}")
    print(f"fund_master unique codes: {len(fm_codes):,}")
    print(f"nav_history unique codes: {len(nh_codes):,}")
    print(f"Codes in fund_master missing from nav_history: {len(missing_in_nav):,}")
    if missing_in_nav:
        print(f"  Sample missing: {missing_in_nav[:20]}")
    print(f"Codes in nav_history not present in fund_master: {len(extra_in_nav):,}")

    return {
        "fund_master_unique_codes": len(fm_codes),
        "nav_history_unique_codes": len(nh_codes),
        "missing_in_nav_count": len(missing_in_nav),
        "missing_in_nav_sample": missing_in_nav[:50],
        "extra_in_nav_count": len(extra_in_nav),
        "all_fund_master_codes_present_in_nav": len(missing_in_nav) == 0,
    }


def write_data_quality_summary(profiles: list, fund_master_summary: dict,
                                validation_summary: dict, out_dir: Path = REPORTS_DIR) -> Path:
    """Write a short markdown data quality summary report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data_quality_summary.md"

    lines = ["# Day 1 Data Quality Summary\n"]
    lines.append("## Dataset Overview\n")
    for p in profiles:
        lines.append(f"### {p['name']}")
        lines.append(f"- Shape: {p['shape'][0]:,} rows x {p['shape'][1]} columns")
        if p["anomalies"]:
            lines.append("- Anomalies:")
            for a in p["anomalies"]:
                lines.append(f"  - {a}")
        else:
            lines.append("- No anomalies detected")
        lines.append("")

    if fund_master_summary:
        lines.append("## Fund Master Exploration\n")
        for key in ("fund_house", "category", "sub_category", "risk_grade"):
            if key in fund_master_summary:
                lines.append(f"- **{key}**: {len(fund_master_summary[key])} unique values")
        if "scheme_code_column" in fund_master_summary:
            lines.append(
                f"- **AMFI scheme codes**: column `{fund_master_summary['scheme_code_column']}`, "
                f"{fund_master_summary['scheme_code_unique']:,} unique codes "
                f"out of {fund_master_summary['scheme_code_count']:,} rows"
            )
        lines.append("")

    if validation_summary and "error" not in validation_summary:
        lines.append("## AMFI Scheme Code Validation\n")
        lines.append(f"- fund_master unique codes: {validation_summary['fund_master_unique_codes']:,}")
        lines.append(f"- nav_history unique codes: {validation_summary['nav_history_unique_codes']:,}")
        status = "✅ PASS" if validation_summary["all_fund_master_codes_present_in_nav"] else "❌ FAIL"
        lines.append(f"- All fund_master codes present in nav_history: {status}")
        if validation_summary["missing_in_nav_count"]:
            lines.append(f"- Missing codes count: {validation_summary['missing_in_nav_count']:,}")
            lines.append(f"  - Sample: {validation_summary['missing_in_nav_sample'][:10]}")
        lines.append("")
    elif validation_summary and "error" in validation_summary:
        lines.append("## AMFI Scheme Code Validation\n")
        lines.append(f"- Validation could not be performed: {validation_summary['error']}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Data quality summary written to {out_path}")
    return out_path


def main():
    result = load_all_datasets(RAW_DIR)
    if not result:
        logger.error("No datasets loaded. Aborting further steps.")
        return

    datasets, profiles = result

    fund_master_summary = {}
    validation_summary = {}

    if "fund_master" in datasets:
        fund_master_summary = explore_fund_master(datasets["fund_master"])
    else:
        logger.warning("fund_master.csv not found among loaded datasets — skipping fund master exploration.")

    if "fund_master" in datasets and "nav_history" in datasets:
        validation_summary = validate_scheme_codes(datasets["fund_master"], datasets["nav_history"])
    else:
        logger.warning("fund_master and/or nav_history not found — skipping scheme code validation.")

    write_data_quality_summary(profiles, fund_master_summary, validation_summary)


if __name__ == "__main__":
    main()
