"""
tests/test_build_features_task6.py
===================================
Manual test for Task 6: volatility & trends features.
Run from project root:
    python tests/test_build_features_task6.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from datetime import date
from features.build_features import build_features, _compute_volatility_and_trends

DB    = "data/credit.db"
AS_OF = date(2024, 11, 1)

# ==========================================================================
# Test A: Real applicants from the database
# ==========================================================================
print("=" * 65)
print("Test A: Real applicants from database")
print("=" * 65)
for app_id in ["APP_00000", "APP_00001", "APP_00004"]:
    r = build_features(app_id, AS_OF, DB)
    print(f"\n{app_id}")
    print(f"  active_day_ratio             {r['active_day_ratio']}")
    print(f"  longest_zero_income_gap_days {r['longest_zero_income_gap_days']}")
    print(f"  income_cv                    {r['income_cv']}")
    print(f"  income_trend_ratio           {r['income_trend_ratio']}")

# ==========================================================================
# Test B: Null guard — fewer than 2 transactions for longest_zero_income_gap_days
# ==========================================================================
print("\n" + "=" * 65)
print("Test B: Fewer than 2 transactions → longest_zero_income_gap_days = NaN")
print("=" * 65)

# 0 transactions
empty_inflows = pd.DataFrame(columns=["date", "amount_inr", "source_id"])
res_empty = _compute_volatility_and_trends(empty_inflows, months_observed=6.0, as_of_date=AS_OF)
ok_empty = pd.isna(res_empty["longest_zero_income_gap_days"])

# 1 transaction
single_inflow = pd.DataFrame([
    {"date": pd.Timestamp("2024-06-01"), "amount_inr": 1500.0, "source_id": "src_1"}
])
res_single = _compute_volatility_and_trends(single_inflow, months_observed=6.0, as_of_date=AS_OF)
ok_single = pd.isna(res_single["longest_zero_income_gap_days"])

print(f"  0 transactions gap: {res_empty['longest_zero_income_gap_days']} (expected NaN)")
print(f"  1 transaction gap:  {res_single['longest_zero_income_gap_days']} (expected NaN)")
print(f"  → {'PASS ✓' if ok_empty and ok_single else 'FAIL ✗'}")

# ==========================================================================
# Test C: Null guard — mean monthly income is 0 → income_cv = NaN
# ==========================================================================
print("\n" + "=" * 65)
print("Test C: Mean monthly income is 0 → income_cv = NaN")
print("=" * 65)

zero_inflows = pd.DataFrame([
    {"date": pd.Timestamp("2024-06-01"), "amount_inr": 0.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-07-01"), "amount_inr": 0.0, "source_id": "src_1"},
])
res_zero = _compute_volatility_and_trends(zero_inflows, months_observed=2.0, as_of_date=AS_OF)
ok_zero = pd.isna(res_zero["income_cv"])
print(f"  income_cv with 0 income: {res_zero['income_cv']} (expected NaN)")
print(f"  → {'PASS ✓' if ok_zero else 'FAIL ✗'}")

# ==========================================================================
# Test D: Null guard — preceding months average is 0 or missing → income_trend_ratio = NaN
# ==========================================================================
print("\n" + "=" * 65)
print("Test D: Preceding months average is 0 or missing → income_trend_ratio = NaN")
print("=" * 65)

# Only recent transactions within 30 days of 2024-11-01 (e.g. 2024-10-15)
only_recent = pd.DataFrame([
    {"date": pd.Timestamp("2024-10-15"), "amount_inr": 5000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-10-20"), "amount_inr": 4000.0, "source_id": "src_1"},
])
res_no_preceding = _compute_volatility_and_trends(only_recent, months_observed=1.0, as_of_date=AS_OF)
ok_no_preceding = pd.isna(res_no_preceding["income_trend_ratio"])

# Preceding period exists but sum is 0
zero_preceding = pd.DataFrame([
    {"date": pd.Timestamp("2024-08-01"), "amount_inr": 0.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-10-15"), "amount_inr": 5000.0, "source_id": "src_1"},
])
res_zero_preceding = _compute_volatility_and_trends(zero_preceding, months_observed=3.0, as_of_date=AS_OF)
ok_zero_preceding = pd.isna(res_zero_preceding["income_trend_ratio"])

print(f"  No preceding history: trend_ratio={res_no_preceding['income_trend_ratio']} (expected NaN)")
print(f"  0 preceding income:   trend_ratio={res_zero_preceding['income_trend_ratio']} (expected NaN)")
print(f"  → {'PASS ✓' if ok_no_preceding and ok_zero_preceding else 'FAIL ✗'}")

# ==========================================================================
# Test E: Known manual calculations
# ==========================================================================
print("\n" + "=" * 65)
print("Test E: Known values verification")
print("=" * 65)
# Window: as_of = 2024-11-01, months_observed = 4.0 -> total_days = 120
# Transactions on:
#   2024-08-01: 1000
#   2024-08-05: 2000  (gap = 4 days from Aug 1)
#   2024-09-01: 3000  (gap = 27 days from Aug 5)
#   2024-10-15: 4000  (zero income between Sep 1 and Oct 15 is 43 days!)
# Total unique active days = 4 -> active_day_ratio = 4 / 120 = 0.0333
# Max gap = 43 zero-income days
# Monthly totals:
#   Aug: 3000
#   Sep: 3000
#   Oct: 4000
# Mean monthly = 3333.3333
# Std monthly (sample, ddof=1) of [3000, 3000, 4000] = 577.3503
# income_cv = 577.3503 / 3333.3333 = 0.1732
#
# Recent 30 days (after 2024-10-02): Oct 15 -> sum = 4000
# Preceding period (up to 2024-10-02): Aug, Sep -> monthly totals [3000, 3000] -> mean = 3000
# income_trend_ratio = 4000 / 3000 = 1.3333

known_df = pd.DataFrame([
    {"date": pd.Timestamp("2024-08-01"), "amount_inr": 1000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-08-05"), "amount_inr": 2000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-09-01"), "amount_inr": 3000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-10-15"), "amount_inr": 4000.0, "source_id": "src_1"},
])

res_known = _compute_volatility_and_trends(known_df, months_observed=4.0, as_of_date=AS_OF)
print(f"  active_day_ratio:             {res_known['active_day_ratio']} (expected ~0.0333)")
print(f"  longest_zero_income_gap_days: {res_known['longest_zero_income_gap_days']} (expected 43)")
print(f"  income_cv:                    {res_known['income_cv']} (expected ~0.1732)")
print(f"  income_trend_ratio:           {res_known['income_trend_ratio']} (expected ~1.3333)")

ok_known = (
    abs(res_known["active_day_ratio"] - 0.0333) < 0.001
    and res_known["longest_zero_income_gap_days"] == 43
    and abs(res_known["income_cv"] - 0.1732) < 0.001
    and abs(res_known["income_trend_ratio"] - 1.3333) < 0.001
)
print(f"  → {'PASS ✓' if ok_known else 'FAIL ✗'}")
