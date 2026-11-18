"""
tests/test_build_features_task7.py
===================================
Manual test for Task 7: shock events & seasonality adjusted income.
Verifies all 19 features are produced and match null rules.
Run from project root:
    python tests/test_build_features_task7.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from datetime import date
from features.build_features import build_features, _compute_shock_and_seasonality_features

DB    = "data/credit.db"
AS_OF = date(2024, 11, 1)

# ==========================================================================
# Test A: Real applicants from the database (including shock and no-shock)
# ==========================================================================
print("=" * 70)
print("Test A: Real applicants from database (checking all 19 features)")
print("=" * 70)

for app_id in ["APP_00000", "APP_00001", "APP_00004"]:
    r = build_features(app_id, AS_OF, DB)
    print(f"\n{app_id}:")
    feature_keys = [k for k in r.keys() if k not in ("applicant_id", "as_of_date")]
    print(f"  Total features count: {len(feature_keys)} (expected 19)")
    for k, v in r.items():
        print(f"    {k:<30} : {v}")

# ==========================================================================
# Test B: Null Rule 1 — No shock rows -> severity = 0.0, recovery = NaN
# ==========================================================================
print("\n" + "=" * 70)
print("Test B: No shock events -> shock_severity = 0.0, recovery_time_days = NaN")
print("=" * 70)

empty_shocks = pd.DataFrame(columns=["shock_date", "end_date", "severity"])
fake_inflows = pd.DataFrame([
    {"date": pd.Timestamp("2024-05-01"), "amount_inr": 10000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-06-01"), "amount_inr": 12000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-07-01"), "amount_inr": 15000.0, "source_id": "src_1"},
])

res_b = _compute_shock_and_seasonality_features(
    empty_shocks, fake_inflows, avg_monthly_inflow=12333.33, as_of_date=AS_OF
)
ok_b = (res_b["shock_severity"] == 0.0) and pd.isna(res_b["recovery_time_days"])
print(f"  shock_severity:     {res_b['shock_severity']} (expected 0.0)")
print(f"  recovery_time_days: {res_b['recovery_time_days']} (expected NaN)")
print(f"  → {'PASS ✓' if ok_b else 'FAIL ✗'}")

# ==========================================================================
# Test C: Null Rule 2 — Shock occurred but income has NOT recovered
# ==========================================================================
print("\n" + "=" * 70)
print("Test C: Shock occurred, but never recovers -> recovery_time_days = NaN")
print("=" * 70)

# Pre-shock income: 10,000 / day in May. Shock on June 1st. Post-shock income: 1,000 / day in June, July, Aug.
shock_c = pd.DataFrame([
    {"shock_date": pd.Timestamp("2024-06-01"), "end_date": pd.Timestamp("2024-06-20"), "severity": 0.8}
])
inflows_c_rows = []
# Pre-shock days
for d in pd.date_range("2024-05-01", "2024-05-31"):
    inflows_c_rows.append({"date": d, "amount_inr": 1000.0, "source_id": "src_1"})
# Post-shock days (remains severely depressed)
for d in pd.date_range("2024-06-01", "2024-08-31"):
    inflows_c_rows.append({"date": d, "amount_inr": 100.0, "source_id": "src_1"})

inflows_c = pd.DataFrame(inflows_c_rows)
res_c = _compute_shock_and_seasonality_features(shock_c, inflows_c, avg_monthly_inflow=500.0, as_of_date=date(2024, 9, 1))

ok_c = (res_c["shock_severity"] == 0.8) and pd.isna(res_c["recovery_time_days"])
print(f"  shock_severity:     {res_c['shock_severity']} (expected 0.8)")
print(f"  recovery_time_days: {res_c['recovery_time_days']} (expected NaN)")
print(f"  → {'PASS ✓' if ok_c else 'FAIL ✗'}")

# ==========================================================================
# Test D: Null Rule 3 — Fewer than 3 months -> seasonality_adjusted = avg_monthly
# ==========================================================================
print("\n" + "=" * 70)
print("Test D: Fewer than 3 months -> seasonality_adjusted_income = avg_monthly_inflow")
print("=" * 70)

two_months_inflows = pd.DataFrame([
    {"date": pd.Timestamp("2024-08-01"), "amount_inr": 15000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-09-01"), "amount_inr": 25000.0, "source_id": "src_1"},
])
res_d = _compute_shock_and_seasonality_features(
    empty_shocks, two_months_inflows, avg_monthly_inflow=20000.0, as_of_date=AS_OF
)
ok_d = (res_d["seasonality_adjusted_income"] == 20000.0)
print(f"  seasonality_adjusted_income: {res_d['seasonality_adjusted_income']} (expected 20000.0)")
print(f"  → {'PASS ✓' if ok_d else 'FAIL ✗'}")

# ==========================================================================
# Test E: Trimming min and max months for seasonality_adjusted_income
# ==========================================================================
print("\n" + "=" * 70)
print("Test E: Trimming single min and max months")
print("=" * 70)
# 4 months:
#   May: 5,000 (MIN)
#   Jun: 12,000
#   Jul: 16,000
#   Aug: 45,000 (MAX)
# Dropping May (5000) and Aug (45000) leaves Jun (12000) and Jul (16000).
# Expected mean = (12000 + 16000) / 2 = 14,000.0

four_months_inflows = pd.DataFrame([
    {"date": pd.Timestamp("2024-05-15"), "amount_inr": 5000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-06-15"), "amount_inr": 12000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-07-15"), "amount_inr": 16000.0, "source_id": "src_1"},
    {"date": pd.Timestamp("2024-08-15"), "amount_inr": 45000.0, "source_id": "src_1"},
])
res_e = _compute_shock_and_seasonality_features(
    empty_shocks, four_months_inflows, avg_monthly_inflow=19500.0, as_of_date=AS_OF
)
expected_trim = 14000.0
ok_e = (res_e["seasonality_adjusted_income"] == expected_trim)
print(f"  seasonality_adjusted_income: {res_e['seasonality_adjusted_income']} (expected {expected_trim})")
print(f"  → {'PASS ✓' if ok_e else 'FAIL ✗'}")
