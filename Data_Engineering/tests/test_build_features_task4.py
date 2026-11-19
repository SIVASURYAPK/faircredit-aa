"""
tests/test_build_features_task4.py
===================================
Manual test for Task 4: bill behaviour features.
Run from project root:
    python tests/test_build_features_task4.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from datetime import date
from features.build_features import build_features, _compute_bill_features

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
    print(f"  bills_due_count_6m       {r['bills_due_count_6m']}")
    print(f"  missed_payment_count_6m  {r['missed_payment_count_6m']}")
    print(f"  avg_days_late            {r['avg_days_late']}")
    print(f"  on_time_bill_rate        {r['on_time_bill_rate']}")

# ==========================================================================
# Test B: Null guard — no bill history → 3 features must be np.nan
# ==========================================================================
print("\n" + "=" * 60)
print("Test B: Empty bills → missed/avg_days_late/on_time_rate = NaN")
print("=" * 60)
empty_bills = pd.DataFrame(
    columns=["due_date", "paid_date", "amount_inr"]
)
result = _compute_bill_features(empty_bills)
all_nan = (
    result["bills_due_count_6m"] == 0
    and pd.isna(result["missed_payment_count_6m"])
    and pd.isna(result["avg_days_late"])
    and pd.isna(result["on_time_bill_rate"])
)
print(f"  bills_due_count_6m       = {result['bills_due_count_6m']}")
print(f"  missed_payment_count_6m  = {result['missed_payment_count_6m']}")
print(f"  avg_days_late            = {result['avg_days_late']}")
print(f"  on_time_bill_rate        = {result['on_time_bill_rate']}")
print(f"  → {'PASS ✓' if all_nan else 'FAIL ✗'}")

# ==========================================================================
# Test C: All bills paid on time → avg_days_late must be 0 (not NaN)
# ==========================================================================
print("\n" + "=" * 60)
print("Test C: All on-time → avg_days_late = 0, on_time_rate = 1.0")
print("=" * 60)
on_time_bills = pd.DataFrame([
    # paid_date <= due_date on all rows
    {"due_date": pd.Timestamp("2024-05-05"), "paid_date": pd.Timestamp("2024-05-04"), "amount_inr": 5000},
    {"due_date": pd.Timestamp("2024-06-05"), "paid_date": pd.Timestamp("2024-06-05"), "amount_inr": 5000},
    {"due_date": pd.Timestamp("2024-07-05"), "paid_date": pd.Timestamp("2024-07-03"), "amount_inr": 5000},
])
result = _compute_bill_features(on_time_bills)
ok = (result["avg_days_late"] == 0.0 and result["on_time_bill_rate"] == 1.0)
print(f"  avg_days_late      = {result['avg_days_late']}   (expected 0.0)")
print(f"  on_time_bill_rate  = {result['on_time_bill_rate']}   (expected 1.0)")
print(f"  → {'PASS ✓' if ok else 'FAIL ✗'}")

# ==========================================================================
# Test D: Mixed — some late, some on-time, some missed
# ==========================================================================
print("\n" + "=" * 60)
print("Test D: Mixed bills — late, on-time, and missed")
print("=" * 60)
mixed_bills = pd.DataFrame([
    # on-time (days_late = -1)
    {"due_date": pd.Timestamp("2024-05-05"), "paid_date": pd.Timestamp("2024-05-04"), "amount_inr": 5000},
    # on-time exactly (days_late = 0)
    {"due_date": pd.Timestamp("2024-06-05"), "paid_date": pd.Timestamp("2024-06-05"), "amount_inr": 5000},
    # late by 6 days (days_late = 6)
    {"due_date": pd.Timestamp("2024-07-05"), "paid_date": pd.Timestamp("2024-07-11"), "amount_inr": 5000},
    # late by 10 days (days_late = 10)
    {"due_date": pd.Timestamp("2024-08-05"), "paid_date": pd.Timestamp("2024-08-15"), "amount_inr": 5000},
    # missed (paid_date is NaT)
    {"due_date": pd.Timestamp("2024-09-05"), "paid_date": pd.NaT,                    "amount_inr": 5000},
])
result = _compute_bill_features(mixed_bills)
# Expected:
#   bills_due_count      = 5
#   missed_count         = 1
#   avg_days_late        = (0 + 0 + 6 + 10) / 4 = 4.0  (average delay across paid bills, on-time counts as 0 delay)
#   on_time_bill_rate    = 2 on-time / 5 total = 0.4
expected_avg  = 4.0
expected_rate = 0.4
ok = (
    result["bills_due_count_6m"]      == 5
    and result["missed_payment_count_6m"] == 1
    and result["avg_days_late"]           == expected_avg
    and result["on_time_bill_rate"]       == expected_rate
)
print(f"  bills_due_count_6m       = {result['bills_due_count_6m']}    (expected 5)")
print(f"  missed_payment_count_6m  = {result['missed_payment_count_6m']}    (expected 1)")
print(f"  avg_days_late            = {result['avg_days_late']}   (expected {expected_avg}  — paid bills averaged with on-time as 0)")
print(f"  on_time_bill_rate        = {result['on_time_bill_rate']}   (expected {expected_rate} — 2 on-time / 5 total)")
print(f"  → {'PASS ✓' if ok else 'FAIL ✗'}")
