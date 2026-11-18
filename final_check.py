"""
final_check.py - run from the PROJECT ROOT (the folder that contains data/ and tests/):
    python final_check.py
Checks data/features_final.csv (+ protected_attrs.csv and raw files if present) before sending to teammates.
"""
import os, sys, hashlib
import numpy as np
import pandas as pd

FEATURES = [
    "avg_monthly_inflow", "median_monthly_inflow", "obligation_to_inflow_ratio", "emi_to_inflow_ratio",
    "income_cv", "active_day_ratio", "longest_zero_income_gap_days", "income_trend_ratio",
    "on_time_bill_rate", "avg_days_late", "missed_payment_count_6m", "bills_due_count_6m",
    "balance_buffer_months", "overdraft_event_count_6m",
    "shock_severity", "recovery_time_days", "seasonality_adjusted_income",
    "months_observed", "income_source_count",
]
INT_COLS = ["longest_zero_income_gap_days", "missed_payment_count_6m", "bills_due_count_6m",
            "overdraft_event_count_6m", "months_observed", "income_source_count"]
INCOME_COLS = ["avg_monthly_inflow", "median_monthly_inflow", "seasonality_adjusted_income"]
UNIT_COLS = ["active_day_ratio", "on_time_bill_rate", "shock_severity"]
PROTECTED = {"gender", "caste", "religion", "age", "age_group", "age_band", "region",
             "pin_code", "latitude", "longitude"}

FEAT_PATH = "data/features_final.csv"
PROT_PATH = "data/protected_attrs.csv"
RAW = "data/raw"
EXPECTED_ROWS = 5000

fails, warns = [], []
def ok(m): print("  PASS ", m)
def fail(m): print("  FAIL ", m); fails.append(m)
def warn(m): print("  WARN ", m); warns.append(m)
def skip(m): print("  SKIP ", m)
def chk(cond, good, bad):
    (ok if cond else fail)(good if cond else bad)
def head(t): print("\n== " + t)

if not os.path.exists(FEAT_PATH):
    print("Cannot find", FEAT_PATH, "- run this from the project root folder.")
    sys.exit(1)

f = pd.read_csv(FEAT_PATH)

head("1. Shape and columns")
if len(f) == EXPECTED_ROWS: ok(f"{len(f)} rows")
else: fail(f"expected {EXPECTED_ROWS} rows, found {len(f)}")
expected_cols = {"applicant_id", "as_of_date", "TARGET"} | set(FEATURES)
missing = expected_cols - set(f.columns); extra = set(f.columns) - expected_cols
if not missing: ok("all 19 features + applicant_id + as_of_date + TARGET present")
else: fail(f"missing columns: {sorted(missing)}")
if extra: fail(f"unexpected extra columns: {sorted(extra)}")
leaked = PROTECTED & set(f.columns)
if leaked: fail(f"PROTECTED columns inside features file: {sorted(leaked)}")
else: ok("no protected columns in features file")

head("2. IDs and TARGET")
if f["applicant_id"].isna().any(): fail("null applicant_id")
if f["applicant_id"].duplicated().any(): fail(f"{f['applicant_id'].duplicated().sum()} duplicate applicant_id")
else: ok("applicant_id unique")
if "TARGET" in f.columns:
    if f["TARGET"].isna().any(): fail(f"TARGET has {f['TARGET'].isna().sum()} nulls")
    elif not set(f["TARGET"].unique()).issubset({0, 1}): fail("TARGET not binary 0/1")
    else:
        rate = f["TARGET"].mean()
        ok(f"TARGET binary, default rate = {rate:.4f} ({int(f['TARGET'].sum())} defaulters)")
        if not 0.08 <= rate <= 0.15: warn("default rate outside 8-15% (our assumed range; confirm with Member 3)")

head("3. Types, ranges, infinities")
for c in FEATURES:
    if c not in f.columns: continue
    if not pd.api.types.is_numeric_dtype(f[c]): fail(f"{c} is not numeric ({f[c].dtype})"); continue
    v = f[c].dropna()
    if np.isinf(v).any(): fail(f"{c} contains inf")
    if c in INT_COLS and not np.all(np.mod(v, 1) == 0): fail(f"{c} must be integer but has fractions")
    if c in INCOME_COLS and (v < 0).any(): fail(f"{c} has negative values")
    elif c not in INCOME_COLS and c not in UNIT_COLS and (v < 0).any(): warn(f"{c} has negative values (min {v.min()})")
    if c in UNIT_COLS and ((v < 0).any() or (v > 1).any()): fail(f"{c} outside [0,1]: min {v.min()}, max {v.max()}")
if "months_observed" in f.columns:
    m = f["months_observed"]
    if m.isna().any() or (m < 6).any() or (m > 12).any(): fail("months_observed must be 6-12")
    else: ok(f"months_observed integer-valued, range {int(m.min())}-{int(m.max())}")
if "income_source_count" in f.columns:
    s = f["income_source_count"]
    if s.min() < 1 or s.max() > 4: fail(f"income_source_count range {s.min()}-{s.max()} (expected 1-4)")
    else: ok(f"income_source_count values: {sorted(s.unique().tolist())}")
if "active_day_ratio" in f.columns and (f["active_day_ratio"] > 1).any():
    fail("active_day_ratio above 1")

head("4. Constant / suspicious columns (catches bugs like 'always 1' or 'always 0')")
for c in FEATURES:
    if c in f.columns:
        n = f[c].nunique(dropna=True)
        if n <= 1: fail(f"{c} has only {n} distinct value(s) - useless to the model")
if not any("distinct value" in x for x in fails): ok("no constant feature columns")
if "overdraft_event_count_6m" in f.columns:
    p = (f["overdraft_event_count_6m"] > 0).mean()
    (ok if 0.05 <= p <= 0.40 else warn)(f"applicants with overdraft > 0: {p:.1%} (expected ~10-25%)")
if "on_time_bill_rate" in f.columns:
    mu = f["on_time_bill_rate"].mean()
    (ok if 0.55 <= mu <= 0.80 else warn)(f"on_time_bill_rate mean {mu:.3f} (expected ~0.6-0.75)")
if "bills_due_count_6m" in f.columns:
    mu = f["bills_due_count_6m"].mean()
    (ok if 10 <= mu <= 26 else warn)(f"bills_due_count_6m mean {mu:.1f} (expected ~12-24)")
dups = f.drop(columns=["applicant_id"], errors="ignore").duplicated().sum()
(ok if dups == 0 else warn)(f"{dups} fully duplicated feature rows")
if {"active_day_ratio", "longest_zero_income_gap_days"} <= set(f.columns):
    full = f[f.active_day_ratio >= 1.0]
    bad = (full.longest_zero_income_gap_days > 0).sum()
    chk(bad == 0, f"consistent: all {len(full)} applicants with active_day_ratio = 1 have zero-income gap = 0",
        f"{bad} of {len(full)} applicants earned on EVERY day (active_day_ratio = 1) yet have longest_zero_income_gap_days > 0 (likely off-by-one)")
    if f.longest_zero_income_gap_days.min() >= 1:
        warn("longest_zero_income_gap_days is never 0 for anyone (check for off-by-one in the gap calculation)")

head("5. Null rules")
if {"avg_monthly_inflow", "income_cv"} <= set(f.columns):
    n1 = ((f.avg_monthly_inflow == 0) & f.income_cv.notna()).sum()
    n2 = (f.income_cv.isna() & (f.avg_monthly_inflow > 0)).sum()
    chk(n1 == 0 and n2 == 0, "income_cv null exactly when avg income is 0", f"income_cv null-rule broken ({n1} non-null at zero income, {n2} null with income)")
if {"bills_due_count_6m", "on_time_bill_rate"} <= set(f.columns):
    n1 = ((f.bills_due_count_6m == 0) & f.on_time_bill_rate.notna()).sum()
    n2 = (f.on_time_bill_rate.isna() & (f.bills_due_count_6m > 0)).sum()
    chk(n1 == 0 and n2 == 0, "on_time_bill_rate null exactly when no bills due", f"on_time_bill_rate null-rule broken ({n1}, {n2})")
    for c in ["avg_days_late", "missed_payment_count_6m"]:
        if c in f.columns and (f[c].isna() != f.on_time_bill_rate.isna()).any():
            warn(f"{c} nulls do not match on_time_bill_rate nulls")
if {"shock_severity", "recovery_time_days"} <= set(f.columns):
    n = ((f.shock_severity.isna() | (f.shock_severity == 0)) & f.recovery_time_days.notna()).sum()
    chk(n == 0, "recovery_time_days null whenever there is no shock", f"{n} rows have recovery time but no shock")
if "income_trend_ratio" in f.columns:
    print(f"  INFO  income_trend_ratio nulls: {f.income_trend_ratio.isna().sum()} (spec: null only when previous 3-month avg is 0)")
if "emi_to_inflow_ratio" in f.columns:
    print(f"  INFO  emi_to_inflow_ratio nulls: {f.emi_to_inflow_ratio.isna().sum()}, zeros: {(f.emi_to_inflow_ratio == 0).sum()} (null = no EMI unless changed)")

head("6. Cross-check with other files (skipped if a file is missing)")
lab_p = f"{RAW}/labels.csv"
if os.path.exists(lab_p) and "TARGET" in f.columns:
    lab = pd.read_csv(lab_p)
    col = "default" if "default" in lab.columns else ("TARGET" if "TARGET" in lab.columns else None)
    if col:
        mg = f[["applicant_id", "TARGET"]].merge(lab[["applicant_id", col]], on="applicant_id", how="outer")
        bad = (mg["TARGET"] != mg[col]).sum()
        chk(bad == 0, "TARGET matches labels.csv for every applicant", f"{bad} applicants where TARGET differs from labels.csv")
else: skip("labels.csv not found")
lb = f"{RAW}/labels_before.csv"
if os.path.exists(lab_p) and os.path.exists(lb):
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    chk(h(lab_p) == h(lb), "labels.csv identical to labels_before.csv", "labels.csv CHANGED since labels_before.csv")
else: skip("labels_before.csv not found")
app_p = f"{RAW}/applicants.csv"
if os.path.exists(app_p):
    a = pd.read_csv(app_p)
    chk(set(a.applicant_id) == set(f.applicant_id), "applicant IDs match applicants.csv", "applicant IDs differ from applicants.csv")
    if "as_of_date" in a.columns:
        mg = f[["applicant_id", "as_of_date"]].merge(a[["applicant_id", "as_of_date"]], on="applicant_id", suffixes=("", "_raw"))
        chk((mg.as_of_date == mg.as_of_date_raw).all(), "as_of_date matches applicants.csv", "as_of_date differs from applicants.csv")
else: skip("applicants.csv not found")
inf_p = f"{RAW}/inflow_transactions.csv"
if os.path.exists(inf_p):
    inf = pd.read_csv(inf_p, usecols=["applicant_id", "source_id"])
    ns = inf.groupby("applicant_id")["source_id"].nunique()
    mg = f.set_index("applicant_id")["income_source_count"].to_frame().join(ns.rename("raw"))
    bad = (mg["income_source_count"] != mg["raw"]).sum()
    chk(bad == 0, "income_source_count equals distinct sources in raw inflows", f"{bad} applicants where income_source_count != raw distinct sources")
else: skip("inflow_transactions.csv not found")

head("7. Protected attributes file")
if os.path.exists(PROT_PATH):
    p = pd.read_csv(PROT_PATH)
    chk(len(p) == EXPECTED_ROWS, f"{len(p)} rows", f"{len(p)} rows (expected {EXPECTED_ROWS})")
    chk(set(p.applicant_id) == set(f.applicant_id), "applicant IDs match features file", "applicant IDs do not match features file")
    print("  INFO  columns:", list(p.columns))
    if {"TARGET", "default"} & set(p.columns): fail("label column inside protected file")
    if set(FEATURES) & set(p.columns): fail("feature columns inside protected file")
else: skip(f"{PROT_PATH} not created yet")

head("8. Leakage sanity")
if "TARGET" in f.columns:
    num = f[FEATURES].apply(pd.to_numeric, errors="coerce")
    cor = num.corrwith(f["TARGET"]).dropna()
    top = cor.reindex(cor.abs().sort_values(ascending=False).index).head(5)
    print("  INFO  top correlations with TARGET:\n" + top.round(3).to_string().replace("\n", "\n          "))
    if (cor.abs() > 0.5).any(): fail("a feature has |correlation| > 0.5 with TARGET (possible leakage)")
    else: ok("no feature has |correlation| > 0.5 with TARGET")
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import roc_auc_score
        Xtr, Xte, ytr, yte = train_test_split(num, f["TARGET"], test_size=0.3, stratify=f["TARGET"], random_state=42)
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000))
        model.fit(Xtr, ytr)
        auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
        print(f"  INFO  quick logistic regression AUC = {auc:.3f} (healthy ~0.70-0.85)")
        if auc > 0.92: fail("AUC > 0.92: likely leakage")
        elif auc < 0.60: warn("AUC < 0.60: very weak signal, model may learn little")
        else: ok("AUC in a plausible range")
    except ImportError:
        skip("scikit-learn not installed (pip install scikit-learn) - AUC check skipped")

head("9. Summary table (look through this yourself)")
summ = f[FEATURES].describe().T[["min", "mean", "max"]].round(3)
summ["nulls"] = f[FEATURES].isna().sum()
summ["distinct"] = f[FEATURES].nunique()
print(summ.to_string())

print("\n" + "=" * 60)
print(f"RESULT: {len(fails)} FAIL, {len(warns)} WARN")
print("READY TO SEND" if not fails else "NOT READY - fix the FAIL lines first")
sys.exit(0 if not fails else 1)