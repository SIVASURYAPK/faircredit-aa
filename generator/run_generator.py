"""
generator/run_generator.py
===========================
Entry point: generate N applicants, save to SQLite + CSVs.

Run from the project root:
    python -m generator.run_generator
    python -m generator.run_generator --n 500   # quick test run

What this script does (in order):
  1. Parse CLI args (n, seed, as_of_date — all have sensible defaults from config).
  2. Create one master numpy Generator from the fixed seed.
  3. Loop over N applicants:
       a. Draw traits (traits.py)
       b. Generate raw tables (person.py)
       c. Collect shock severity for label computation
       d. Accumulate all table rows
  4. Concatenate each table across all applicants into one big DataFrame.
  5. Compute default labels (labels.py).
  6. Save everything to SQLite (data/credit.db) and CSVs (data/raw/*.csv).
  7. Print a summary.
"""

import argparse
import os
import sys
import sqlite3
from datetime import date

import numpy as np
import pandas as pd

from generator import config
from generator.person import generate_person
from generator.traits import draw_traits
from generator.labels import build_labels_table


# ---------------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic credit data.")
    parser.add_argument(
        "--n", type=int, default=config.N_APPLICANTS,
        help=f"Number of applicants to generate (default: {config.N_APPLICANTS})",
    )
    parser.add_argument(
        "--seed", type=int, default=config.RANDOM_SEED,
        help=f"Random seed (default: {config.RANDOM_SEED})",
    )
    parser.add_argument(
        "--as-of-date", type=str, default=config.AS_OF_DATE,
        help=f"Cutoff date YYYY-MM-DD (default: {config.AS_OF_DATE})",
    )
    parser.add_argument(
        "--db-path", type=str, default=config.DB_PATH,
        help=f"SQLite database path (default: {config.DB_PATH})",
    )
    parser.add_argument(
        "--csv-dir", type=str, default=config.CSV_DIR,
        help=f"CSV directory path (default: {config.CSV_DIR})",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def run(n: int, seed: int, as_of_date: date) -> dict[str, pd.DataFrame]:
    """
    Generate n applicants and return a dict of consolidated DataFrames.

    Parameters
    ----------
    n           : number of applicants
    seed        : master random seed
    as_of_date  : cutoff date (no data after this)
    """
    print(f"\nGenerating {n} applicants (seed={seed}, as_of={as_of_date}) ...")

    # One master rng; each applicant gets a child rng (spawned) so they're
    # independent but the whole run is reproducible from `seed`.
    master_rng = np.random.default_rng(seed)
    # Separate RNG generator for overdraft events so existing generation is undisturbed
    overdraft_master_rng = np.random.default_rng(seed + 3)
    # Separate RNG generator for bills so existing generation is undisturbed
    bills_master_rng = np.random.default_rng(seed + 4)

    # Accumulators: list of DataFrames, one per person, per table
    table_buckets: dict[str, list[pd.DataFrame]] = {
        "applicants":           [],
        "protected_attributes": [],
        "inflow_transactions":  [],
        "obligations":          [],
        "bills":                [],
        "balance_snapshots":    [],
        "overdraft_events":     [],
        "shock_events":         [],
    }

    # For label computation we need traits and shock severities
    all_traits:       list[dict]  = []
    all_ids:          list[str]   = []
    shock_severities: dict        = {}   # applicant_id → severity (0 if no shock)

    for i in range(n):
        applicant_id = f"APP_{i:05d}"   # e.g. "APP_00042"

        # Spawn a child generator — independent stream per person
        child_rng = np.random.default_rng(master_rng.integers(0, 2**32))
        child_od_rng = np.random.default_rng(overdraft_master_rng.integers(0, 2**32))
        child_bill_rng = np.random.default_rng(bills_master_rng.integers(0, 2**32))

        # Draw this person's traits
        traits = draw_traits(applicant_id, child_rng)

        # Generate all raw tables
        tables = generate_person(
            applicant_id=applicant_id,
            traits=traits,
            rng=child_rng,
            as_of_date=as_of_date,
            overdraft_rng=child_od_rng,
            bill_rng=child_bill_rng,
        )

        # Collect shock severity (0 if no shock event)
        shock_df = tables["shock_events"]
        if not shock_df.empty:
            shock_severities[applicant_id] = float(shock_df["severity"].iloc[0])
        else:
            shock_severities[applicant_id] = 0.0

        # Append each table to its bucket
        for tname, df in tables.items():
            table_buckets[tname].append(df)

        all_traits.append(traits)
        all_ids.append(applicant_id)

        # Progress indicator every 500 applicants
        if (i + 1) % 500 == 0:
            print(f"  ... {i + 1}/{n} applicants done")

    print("Concatenating tables ...")

    # Concatenate each table into one big DataFrame
    # ignore_index=True resets the row index (avoids duplicate index values)
    combined: dict[str, pd.DataFrame] = {
        tname: pd.concat(dfs, ignore_index=True)
        for tname, dfs in table_buckets.items()
    }

    # Compute default labels using the HIDDEN traits + noise
    print("Computing default labels ...")
    labels_df = build_labels_table(all_traits, shock_severities, all_ids, master_rng)
    combined["labels"] = labels_df

    return combined


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _assert_not_production_paths(db_path: str = None, csv_dir: str = None, n: int = None) -> None:
    """
    Safety guard: refuse to overwrite production paths (data/credit.db or data/raw)
    when running under tests or when running with a test/reduced subset (n < config.N_APPLICANTS).
    Tests and smoke runs must write to a temporary folder (e.g. pytest tmp_path or tests/tmp/).
    """
    is_pytest = "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules

    prod_db = os.path.abspath(config.DB_PATH)
    prod_csv = os.path.abspath(config.CSV_DIR)

    is_prod_db = db_path and os.path.abspath(db_path) == prod_db
    is_prod_csv = csv_dir and os.path.abspath(csv_dir) == prod_csv

    if is_pytest and (is_prod_db or is_prod_csv):
        raise RuntimeError(
            f"Tests must write ONLY to a temporary folder (e.g. pytest tmp_path or tests/tmp/), "
            f"never to production paths {config.DB_PATH} or {config.CSV_DIR}."
        )

    if n is not None and n < config.N_APPLICANTS and (is_prod_db or is_prod_csv):
        raise ValueError(
            f"Safety block: Refusing to overwrite production dataset with a reduced test run "
            f"(n={n} < {config.N_APPLICANTS}). Specify a temporary output directory via "
            f"--db-path and --csv-dir (e.g. tests/tmp/)."
        )


def save_to_sqlite(tables: dict[str, pd.DataFrame], db_path: str) -> None:
    """
    Write all DataFrames to SQLite.

    pandas .to_sql() does the heavy lifting: it creates the table if it
    doesn't exist and replaces it if it does (if_exists="replace").
    """
    # Safety guard: refuse to overwrite production paths when running under pytest.
    # Tests must pass a tmp_path-based db_path, never config.DB_PATH directly.
    _assert_not_production_paths(db_path=db_path)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"Writing to SQLite: {db_path}")

    # connect() creates the .db file if it doesn't exist
    conn = sqlite3.connect(db_path)
    for tname, df in tables.items():
        df.to_sql(tname, conn, if_exists="replace", index=False)
        print(f"  Saved table '{tname}': {len(df):,} rows")
    
    # Create indexes on applicant_id for fast downstream feature pipeline querying
    cursor = conn.cursor()
    for tname in ["inflow_transactions", "balance_snapshots", "bills", "obligations", "shock_events", "overdraft_events"]:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{tname}_applicant_id ON {tname}(applicant_id);")
    conn.commit()
    conn.close()
    print("SQLite done.")


def save_to_csv(tables: dict[str, pd.DataFrame], csv_dir: str) -> None:
    """
    Write each DataFrame to a CSV file in csv_dir/.
    """
    _assert_not_production_paths(csv_dir=csv_dir)

    os.makedirs(csv_dir, exist_ok=True)
    print(f"Writing CSVs to: {csv_dir}/")

    for tname, df in tables.items():
        path = os.path.join(csv_dir, f"{tname}.csv")
        df.to_csv(path, index=False)
        print(f"  {tname}.csv — {len(df):,} rows")
    print("CSVs done.")


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(tables: dict[str, pd.DataFrame]) -> None:
    """Print row counts, income stats, and default rate by segment."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for tname, df in tables.items():
        print(f"  {tname:<25} {len(df):>10,} rows")

    inflow = tables["inflow_transactions"]
    if not inflow.empty:
        print(f"\nIncome distribution (all inflow days):")
        print(f"  Mean  daily income: ₹{inflow['amount_inr'].mean():>10,.0f}")
        print(f"  Median daily income:₹{inflow['amount_inr'].median():>10,.0f}")
        print(f"  Max   daily income: ₹{inflow['amount_inr'].max():>10,.0f}")

    labels  = tables["labels"]
    apps    = tables["applicants"]
    merged  = labels.merge(apps[["applicant_id", "segment"]], on="applicant_id")
    overall = labels["default"].mean() * 100
    print(f"\nDefault rate (overall):  {overall:.1f}%")
    for seg, grp in merged.groupby("segment"):
        rate = grp["default"].mean() * 100
        print(f"  {seg:<10}  {rate:.1f}%  (n={len(grp):,})")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args       = parse_args()
    as_of_date = date.fromisoformat(args.as_of_date)

    _assert_not_production_paths(db_path=args.db_path, csv_dir=args.csv_dir, n=args.n)

    tables = run(n=args.n, seed=args.seed, as_of_date=as_of_date)
    save_to_sqlite(tables, args.db_path)
    save_to_csv(tables, args.csv_dir)
    print_summary(tables)
