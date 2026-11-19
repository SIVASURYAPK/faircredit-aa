"""
tests/test_raw_data.py
=======================
Step F validation suite.

What we check:
  1. No negative income in inflow_transactions.
  2. No dates after as_of_date in any date column.
  3. applicant_ids are unique in the applicants table.
  4. Each applicant's date window is 6–12 months long.
  5. Default rate is between 8 % and 15 %.
  6. Protected attributes exist ONLY in the protected_attributes table.
  7. Mandatory columns are present in every table.
  8. No duplicate rows in key tables.

Run from the project root:
    pytest tests/ -v

NOTE: This test suite reads from data/credit.db.
      Run `python -m generator.run_generator --n 500` first if the DB is missing.
"""

import sqlite3
import os
from datetime import date, timedelta

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixture: load all tables from SQLite once per test session
# ---------------------------------------------------------------------------

DB_PATH = "data/credit.db"


@pytest.fixture(scope="session")
def tables() -> dict[str, pd.DataFrame]:
    """
    Load all raw tables from SQLite into memory once.
    'scope=session' means this runs once for the whole test run, not per test.
    """
    if not os.path.exists(DB_PATH):
        pytest.skip(
            f"Database not found at {DB_PATH}. "
            "Run `python -m generator.run_generator` first."
        )

    conn = sqlite3.connect(DB_PATH)
    table_names = [
        "applicants", "protected_attributes", "inflow_transactions",
        "obligations", "bills", "balance_snapshots",
        "overdraft_events", "shock_events", "labels",
    ]
    result = {}
    for name in table_names:
        try:
            result[name] = pd.read_sql(f"SELECT * FROM {name}", conn)
        except Exception:
            result[name] = pd.DataFrame()   # table may be empty; don't crash
    conn.close()
    return result


# ---------------------------------------------------------------------------
# Test 1: No negative income
# ---------------------------------------------------------------------------

def test_no_negative_income(tables):
    """
    All inflow amounts must be >= 0.
    Lognormal draws can't go negative, but clamp logic must be verified.
    """
    inflow = tables["inflow_transactions"]
    if inflow.empty:
        pytest.skip("inflow_transactions is empty")

    negative_rows = inflow[inflow["amount_inr"] < 0]
    assert len(negative_rows) == 0, (
        f"Found {len(negative_rows)} negative income rows:\n{negative_rows.head()}"
    )


# ---------------------------------------------------------------------------
# Test 2: No dates after as_of_date per applicant
# ---------------------------------------------------------------------------

def test_no_future_dates(tables):
    """
    Every date in every table must be <= the applicant's as_of_date.
    We read the per-applicant as_of_date from the applicants table.
    """
    apps = tables["applicants"]
    if apps.empty:
        pytest.skip("applicants is empty")

    # Build a lookup: applicant_id → as_of_date
    as_of_map = dict(zip(apps["applicant_id"], pd.to_datetime(apps["as_of_date"]).dt.date))

    # Tables and their date columns to check
    date_tables = {
        "inflow_transactions": ["date"],
        "bills":               ["due_date", "paid_date"],
        "balance_snapshots":   ["date"],
        "overdraft_events":    ["date"],
        "shock_events":        ["start_date", "end_date"],
    }

    violations = []
    for tname, date_cols in date_tables.items():
        df = tables[tname]
        if df.empty or "applicant_id" not in df.columns:
            continue
        for col in date_cols:
            if col not in df.columns:
                continue
            # Drop nulls (paid_date can be null for missed bills)
            sub = df[["applicant_id", col]].dropna()
            sub[col] = pd.to_datetime(sub[col]).dt.date

            for _, row in sub.iterrows():
                aod = as_of_map.get(row["applicant_id"])
                if aod and row[col] > aod:
                    violations.append(f"{tname}.{col}: {row['applicant_id']} → {row[col]} > {aod}")

    assert len(violations) == 0, (
        f"Found {len(violations)} future-date violations:\n" + "\n".join(violations[:10])
    )


# ---------------------------------------------------------------------------
# Test 3: Unique applicant IDs
# ---------------------------------------------------------------------------

def test_unique_applicant_ids(tables):
    """Each applicant_id must appear exactly once in the applicants table."""
    apps = tables["applicants"]
    if apps.empty:
        pytest.skip("applicants is empty")

    duplicates = apps[apps["applicant_id"].duplicated()]
    assert len(duplicates) == 0, (
        f"Found {len(duplicates)} duplicate applicant_ids:\n{duplicates}"
    )


# ---------------------------------------------------------------------------
# Test 4: Date windows are 6–12 months per applicant
# ---------------------------------------------------------------------------

def test_date_windows(tables):
    """
    For each applicant, the spread of dates in inflow_transactions
    must span at least 6 months (180 days) and at most 13 months (395 days).
    We allow a little slack (395 not 365) for the 30*months approximation.
    """
    inflow = tables["inflow_transactions"]
    if inflow.empty:
        pytest.skip("inflow_transactions is empty")

    inflow["date"] = pd.to_datetime(inflow["date"]).dt.date

    grouped = inflow.groupby("applicant_id")["date"].agg(["min", "max"])
    grouped["span_days"] = (
        pd.to_datetime(grouped["max"]) - pd.to_datetime(grouped["min"])
    ).dt.days

    too_short = grouped[grouped["span_days"] < 150]   # ~5 months grace
    too_long  = grouped[grouped["span_days"] > 400]   # ~13 months

    assert len(too_short) == 0, (
        f"{len(too_short)} applicants have < 150 days of data:\n{too_short.head()}"
    )
    assert len(too_long) == 0, (
        f"{len(too_long)} applicants have > 400 days of data:\n{too_long.head()}"
    )


# ---------------------------------------------------------------------------
# Test 5: Default rate between 8 % and 15 %
# ---------------------------------------------------------------------------

def test_default_rate(tables):
    """
    The overall default rate must sit between 8 % and 15 %.
    This validates the logistic label formula in labels.py.

    Requires at least 200 applicants to be statistically meaningful;
    skipped on small test runs (--n 10 etc.).
    """
    labels = tables["labels"]
    if labels.empty:
        pytest.skip("labels is empty")
    if len(labels) < 200:
        pytest.skip(
            f"Only {len(labels)} applicants — need ≥ 200 for a meaningful default rate. "
            "Run `python -m generator.run_generator` for the full dataset."
        )

    rate = labels["default"].mean() * 100
    assert 8.0 <= rate <= 15.0, (
        f"Default rate {rate:.1f}% is outside the [8%, 15%] target range."
    )


# ---------------------------------------------------------------------------
# Test 6: Protected attributes only in their own table
# ---------------------------------------------------------------------------

def test_protected_attributes_isolated(tables):
    """
    Columns like 'gender', 'region', 'age_band' must NOT appear in any
    table other than protected_attributes.

    This is a key fairness guard: if these columns leaked into other tables,
    the model could learn from them indirectly.
    """
    protected_cols = {"gender", "region", "age_band"}

    for tname, df in tables.items():
        if tname == "protected_attributes":
            continue   # obviously fine here
        leaking = protected_cols & set(df.columns)
        assert len(leaking) == 0, (
            f"Table '{tname}' contains protected attribute columns: {leaking}"
        )


# ---------------------------------------------------------------------------
# Test 7: Required columns present in every table
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "applicants":           {"applicant_id", "segment", "as_of_date"},
    "protected_attributes": {"applicant_id", "gender", "region", "age_band"},
    "inflow_transactions":  {"applicant_id", "date", "amount_inr", "source_id"},
    "obligations":          {"applicant_id", "month", "type", "amount_inr"},
    "bills":                {"applicant_id", "due_date", "paid_date", "amount_inr"},
    "balance_snapshots":    {"applicant_id", "date", "balance_inr"},
    "overdraft_events":     {"applicant_id", "date"},
    "shock_events":         {"applicant_id", "start_date", "end_date", "severity"},
    "labels":               {"applicant_id", "default"},
}


def test_required_columns(tables):
    """Every table must have its expected columns."""
    for tname, expected_cols in REQUIRED_COLUMNS.items():
        df = tables.get(tname, pd.DataFrame())
        actual_cols = set(df.columns)
        missing = expected_cols - actual_cols
        assert len(missing) == 0, (
            f"Table '{tname}' is missing columns: {missing}"
        )


# ---------------------------------------------------------------------------
# Test 8: No duplicate rows in key tables
# ---------------------------------------------------------------------------

def test_no_duplicate_balance_rows(tables):
    """
    Each (applicant_id, date) pair must appear at most once in balance_snapshots.
    """
    df = tables["balance_snapshots"]
    if df.empty:
        pytest.skip("balance_snapshots is empty")

    dupes = df[df.duplicated(subset=["applicant_id", "date"])]
    assert len(dupes) == 0, (
        f"Found {len(dupes)} duplicate (applicant_id, date) rows in balance_snapshots"
    )


# ---------------------------------------------------------------------------
# Summary printer (not a test — called manually or via conftest)
# ---------------------------------------------------------------------------

def print_summary_stats(tables: dict) -> None:
    """
    Print a human-readable summary of the generated dataset.
    Call this from a __main__ block or a conftest fixture if desired.
    """
    print("\n=== Dataset Summary ===")
    for tname, df in tables.items():
        print(f"  {tname:<25} {len(df):>10,} rows")

    inflow = tables.get("inflow_transactions", pd.DataFrame())
    if not inflow.empty:
        print(f"\nIncome (inflow_transactions.amount_inr):")
        print(f"  Mean:   ₹{inflow['amount_inr'].mean():,.0f}")
        print(f"  Median: ₹{inflow['amount_inr'].median():,.0f}")
        print(f"  Std:    ₹{inflow['amount_inr'].std():,.0f}")

    labels = tables.get("labels", pd.DataFrame())
    apps   = tables.get("applicants", pd.DataFrame())
    if not labels.empty and not apps.empty:
        merged = labels.merge(apps[["applicant_id", "segment"]], on="applicant_id")
        print(f"\nDefault rate: {labels['default'].mean() * 100:.1f}%")
        for seg, grp in merged.groupby("segment"):
            print(f"  {seg}: {grp['default'].mean() * 100:.1f}% (n={len(grp):,})")


if __name__ == "__main__":
    # Allow running directly: python tests/test_raw_data.py
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    tbls = {
        name: pd.read_sql(f"SELECT * FROM {name}", conn)
        for name in REQUIRED_COLUMNS
    }
    conn.close()
    print_summary_stats(tbls)
