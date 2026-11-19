import pandas as pd

f = pd.read_csv("data/features.csv")
l = pd.read_csv("data/raw/labels.csv").rename(columns={"default": "TARGET"})

f = f.merge(l[["applicant_id", "TARGET"]], on="applicant_id", how="left")

print("rows:", len(f))
print("TARGET missing:", f["TARGET"].isna().sum())
print("default rate:", f["TARGET"].mean())

f.to_csv("data/features_final.csv", index=False)
print("saved data/features_final.csv")