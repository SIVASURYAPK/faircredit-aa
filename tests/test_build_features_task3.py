"""
tests/test_build_features_task3.py
===================================
Manual test for Task 3: obligation ratio features.
Run from project root:
    python tests/test_build_features_task3.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from datetime import date
from features.build_features import build_features, _compute_ratio_features

DB    = "data/credit.db"
AS_OF = date(2024, 11, 1)

# --- Test A: real applicants from DB ---
print("=" * 55)
print("Test A: Real applicants")
print("=" * 55)
for app_id in ["APP_00000", "APP_00001", "APP_00004"]:
    result = build_features(app_id, AS_OF, DB)
    print(f"\n{app_id}")
    print(f"  avg_monthly_inflow          ₹{result['avg_monthly_inflow']:>10,.2f}")
    print(f"  obligation_to_inflow_ratio     {result['obligation_to_inflow_ratio']}")
    print(f"  emi_to_inflow_ratio            {result['emi_to_inflow_ratio']}")

# --- Test B: null guard — zero inflow must produce np.nan ratios ---
print("\n" + "=" * 55)
print("Test B: Null guard (avg_monthly_inflow = 0)")
print("=" * 55)
import pandas as pd

# Build a fake obligations DataFrame (2 months, 2 types)
fake_obligations = pd.DataFrame([
    {"month": "2024-05", "type": "rent", "amount_inr": 5000.0},
    {"month": "2024-05", "type": "emi",  "amount_inr": 2000.0},
    {"month": "2024-06", "type": "rent", "amount_inr": 5000.0},
    {"month": "2024-06", "type": "emi",  "amount_inr": 2000.0},
])

for inflow_val in [0, 0.0, None, float("nan")]:
    ratios = _compute_ratio_features(fake_obligations, inflow_val)
    ob_nan = pd.isna(ratios["obligation_to_inflow_ratio"])
    em_nan = pd.isna(ratios["emi_to_inflow_ratio"])
    status = "PASS ✓" if ob_nan and em_nan else "FAIL ✗"
    print(f"  avg_monthly_inflow={str(inflow_val):<6}  "
          f"obligation_ratio={str(ratios['obligation_to_inflow_ratio']):<6}  "
          f"emi_ratio={str(ratios['emi_to_inflow_ratio']):<6}  → {status}")

# --- Test C: applicant with no EMI rows → emi_ratio should be NaN ---
print("\n" + "=" * 55)
print("Test C: No EMI rows → emi_to_inflow_ratio must be NaN (not 0)")
print("=" * 55)
no_emi_obligations = pd.DataFrame([
    {"month": "2024-05", "type": "rent",      "amount_inr": 5000.0},
    {"month": "2024-05", "type": "utilities", "amount_inr": 800.0},
])
ratios = _compute_ratio_features(no_emi_obligations, avg_monthly_inflow=20000.0)
emi_is_null = pd.isna(ratios["emi_to_inflow_ratio"])
ob_ok       = ratios["obligation_to_inflow_ratio"] > 0
status = "PASS ✓" if emi_is_null and ob_ok else "FAIL ✗"
print(f"  obligation_to_inflow_ratio = {ratios['obligation_to_inflow_ratio']}")
print(f"  emi_to_inflow_ratio        = {ratios['emi_to_inflow_ratio']}  (should be NaN)")
print(f"  → {status}")
