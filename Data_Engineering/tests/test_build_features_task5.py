"""
tests/test_build_features_task5.py
===================================
Manual test for Task 5: balances & overdraft features.
Run from project root:
    python tests/test_build_features_task5.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from datetime import date
from features.build_features import build_features, _compute_balance_features

DB    = "data/credit.db"
AS_OF = date(2024, 11, 1)

# ==========================================================================
# Test A: Real applicants from the database
# ==========================================================================
print("=" * 60)
print("Test A: Real applicants")
print("=" * 60)
for app_id in ["APP_00000", "APP_00001", "APP_00004"]:
    r = build_features(app_id, AS_OF, DB)
    print(f"\n{app_id}")
    print(f"  overdraft_event_count_6m  {r['overdraft_event_count_6m']}")
    print(f"  balance_buffer_months     {r['balance_buffer_months']}")

# ==========================================================================
# Test B: Null guard — no balance data → balance_buffer_months = NaN
# ==========================================================================
print("\n" + "=" * 60)
print("Test B: Empty balance_snapshots → balance_buffer_months = NaN")
print("=" * 60)

empty_balance = pd.DataFrame(columns=["date", "balance_inr"])
some_overdrafts = pd.DataFrame([{"date": "2024-06-10"}, {"date": "2024-07-03"}])
some_obligations = pd.DataFrame([
    {"month": "2024-05", "type": "rent", "amount_inr": 5000.0},
])
result = _compute_balance_features(empty_balance, some_overdrafts, some_obligations)
ok = (
    result["overdraft_event_count_6m"] == 2    # still counted correctly
    and pd.isna(result["balance_buffer_months"])
)
print(f"  overdraft_event_count_6m  = {result['overdraft_event_count_6m']}  (expected 2)")
print(f"  balance_buffer_months     = {result['balance_buffer_months']}  (expected NaN)")
print(f"  → {'PASS ✓' if ok else 'FAIL ✗'}")

# ==========================================================================
# Test C: Null guard — zero monthly obligations → balance_buffer_months = NaN
# ==========================================================================
print("\n" + "=" * 60)
print("Test C: Zero obligations → balance_buffer_months = NaN")
print("=" * 60)

normal_balance = pd.DataFrame([
    {"date": pd.Timestamp("2024-05-01"), "balance_inr": 20000.0},
    {"date": pd.Timestamp("2024-06-01"), "balance_inr": 22000.0},
])
no_overdrafts   = pd.DataFrame(columns=["date"])
zero_obligation = pd.DataFrame(columns=["month", "type", "amount_inr"])  # empty

result = _compute_balance_features(normal_balance, no_overdrafts, zero_obligation)
ok = (
    result["overdraft_event_count_6m"] == 0
    and pd.isna(result["balance_buffer_months"])
)
print(f"  overdraft_event_count_6m  = {result['overdraft_event_count_6m']}  (expected 0)")
print(f"  balance_buffer_months     = {result['balance_buffer_months']}  (expected NaN)")
print(f"  → {'PASS ✓' if ok else 'FAIL ✗'}")

# ==========================================================================
# Test D: Normal case — verify arithmetic manually
# ==========================================================================
print("\n" + "=" * 60)
print("Test D: Known values → verify balance_buffer_months arithmetic")
print("=" * 60)
# avg daily balance: (10000 + 20000 + 30000) / 3 = 20000
# avg monthly obligations:
#   May: rent 8000 + emi 4000 = 12000
#   Jun: rent 8000 + emi 4000 = 12000
#   avg = 12000
# buffer = 20000 / 12000 = 1.6667 months

known_balance = pd.DataFrame([
    {"date": pd.Timestamp("2024-05-15"), "balance_inr": 10000.0},
    {"date": pd.Timestamp("2024-06-15"), "balance_inr": 20000.0},
    {"date": pd.Timestamp("2024-07-15"), "balance_inr": 30000.0},
])
known_overdrafts = pd.DataFrame([{"date": "2024-05-02"}])  # exactly 1
known_obligations = pd.DataFrame([
    {"month": "2024-05", "type": "rent", "amount_inr": 8000.0},
    {"month": "2024-05", "type": "emi",  "amount_inr": 4000.0},
    {"month": "2024-06", "type": "rent", "amount_inr": 8000.0},
    {"month": "2024-06", "type": "emi",  "amount_inr": 4000.0},
])

result = _compute_balance_features(known_balance, known_overdrafts, known_obligations)
expected_buffer = round(20000.0 / 12000.0, 4)   # 1.6667
ok = (
    result["overdraft_event_count_6m"] == 1
    and abs(result["balance_buffer_months"] - expected_buffer) < 0.001
)
print(f"  overdraft_event_count_6m  = {result['overdraft_event_count_6m']}    (expected 1)")
print(f"  balance_buffer_months     = {result['balance_buffer_months']}  (expected {expected_buffer})")
print(f"  Calculation: avg_balance=₹20000 / avg_monthly_obligations=₹12000 = {expected_buffer} months")
print(f"  → {'PASS ✓' if ok else 'FAIL ✗'}")
