import pandas as pd
import numpy as np

old = pd.read_csv("data/features_before.csv").set_index("applicant_id")
new = pd.read_csv("data/features.csv").set_index("applicant_id")

print("same applicants:", old.index.equals(new.index))

for col in old.columns:
    if col not in new.columns:
        print(f"{col:35s} MISSING in new file")
        continue
    a, b = old[col], new[col]
    if pd.api.types.is_numeric_dtype(a):
        same = np.isclose(a, b, rtol=1e-9, atol=1e-9, equal_nan=True)
    else:
        same = (a == b) | (a.isna() & b.isna())
    print(f"{col:35s} rows changed: {(~same).sum()}")