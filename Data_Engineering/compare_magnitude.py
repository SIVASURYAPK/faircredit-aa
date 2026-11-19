import pandas as pd

old = pd.read_csv("data/features_before.csv").set_index("applicant_id")
new = pd.read_csv("data/features.csv").set_index("applicant_id")

cols = ["avg_monthly_inflow", "median_monthly_inflow", "seasonality_adjusted_income",
        "balance_buffer_months", "income_trend_ratio", "income_cv",
        "obligation_to_inflow_ratio", "emi_to_inflow_ratio", "active_day_ratio"]

for c in cols:
    d = (new[c] - old[c]).abs()
    print(f"{c:30s} max diff: {d.max():.6f}   rows with diff > 1: {(d > 1).sum()}")

a = new["active_day_ratio"]
print("\nactive_day_ratio above 1:", (a > 1).sum(), "| max:", a.max())
print("old vs new mean:", old["active_day_ratio"].mean(), new["active_day_ratio"].mean())