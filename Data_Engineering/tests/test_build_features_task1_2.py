"""
Quick manual test: run build_features on 3 real applicants from the DB.
Run from project root:
    python tests/test_build_features_task1_2.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # add project root

from datetime import date
from features.build_features import build_features

DB = "data/credit.db"
AS_OF = date(2024, 11, 1)

# Test on 3 applicants so we see variety
for app_id in ["APP_00000", "APP_00001", "APP_00004"]:
    result = build_features(app_id, AS_OF, DB)
    print(f"\n--- {app_id} ---")
    for key, val in result.items():
        print(f"  {key:<25} {val}")
