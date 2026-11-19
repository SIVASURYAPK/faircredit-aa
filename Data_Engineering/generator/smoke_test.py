"""
generator/smoke_test.py
=======================
Quick sanity check: generate ONE person with FIXED traits and print
the first few rows of each table.

Run from the project root:
    python -m generator.smoke_test
"""

import numpy as np
from datetime import date
from generator.person import generate_person


def main():
    # Fixed traits — same person every time (for review / debugging)
    traits = {
        "segment":          "gig",
        "base_income":      18_000.0,   # INR / month
        "volatility":       0.35,
        "reliability":      0.72,
        "months":           9,
        "n_income_sources": 2,
        "has_bill_history": True,
        "has_shock":        True,
    }

    # Fixed seed → reproducible output
    rng = np.random.default_rng(seed=42)
    as_of_date = date(2024, 11, 1)

    tables = generate_person(
        applicant_id="APP_DEMO",
        traits=traits,
        rng=rng,
        as_of_date=as_of_date,
    )

    # Print shape and first 5 rows of every table
    for name, df in tables.items():
        print(f"\n{'='*60}")
        print(f"TABLE: {name}  — {len(df)} rows × {len(df.columns)} cols")
        print(f"{'='*60}")
        print(df.head(5).to_string(index=False))

    # Quick summary numbers
    inflow = tables["inflow_transactions"]
    print(f"\n--- Summary ---")
    print(f"Total inflow days : {len(inflow)}")
    if not inflow.empty:
        print(f"Total income INR  : {inflow['amount_inr'].sum():,.0f}")
        print(f"Avg daily income  : {inflow['amount_inr'].mean():,.0f}")
        print(f"Max daily income  : {inflow['amount_inr'].max():,.0f}")

    shocks = tables["shock_events"]
    print(f"Shock events      : {len(shocks)}")

    overdrafts = tables["overdraft_events"]
    print(f"Overdraft days    : {len(overdrafts)}")

    bills = tables["bills"]
    if not bills.empty:
        missed = bills["paid_date"].isna().sum()
        print(f"Bills missed      : {missed} / {len(bills)}")


if __name__ == "__main__":
    main()
