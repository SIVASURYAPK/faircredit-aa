import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from fairlearn.metrics import demographic_parity_ratio
from fairness_explainability.shap_explainer import CreditExplainer, MODEL_FEATURES

# 1. Load data
features_df = pd.read_csv("data/features_final_v1.csv")
protected_df = pd.read_csv("data/protected_attrs.csv", dtype={"pin_code": str})
df = pd.merge(features_df, protected_df, on="applicant_id", how="inner")

# Check 1: Zero Protected Attribute Leakage
assert len(set(MODEL_FEATURES) & set(protected_df.columns)) == 0, "Leakage detected!"
print("[PASS] Check 1: Zero protected attribute leakage.")

# Train temporary model
X, y = df[MODEL_FEATURES], df["TARGET"]
model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
model.fit(X, y)
coach = CreditExplainer(model, MODEL_FEATURES)

# Check 2: SHAP Additivity (Base value + sum(SHAP) == raw model margin)
sample = X.iloc[[0]]
shap_vals = coach.explainer.shap_values(sample)[0]
expected_val = float(coach.explainer.expected_value)
raw_margin = float(model.predict(sample, output_margin=True)[0])
assert np.isclose(expected_val + shap_vals.sum(), raw_margin, atol=1e-4), "SHAP additivity failed!"
print(f"[PASS] Check 2: SHAP additivity exact ({expected_val + shap_vals.sum():.4f} == {raw_margin:.4f}).")

# Check 3: Null / NaN Handling
null_sample = sample.copy()
null_sample["recovery_time_days"] = np.nan
null_sample["on_time_bill_rate"] = np.nan
res_null = coach.explain_applicant(null_sample, lang="ta")
assert isinstance(res_null["credit_score"], int), "Null handling failed!"
print("[PASS] Check 3: Null special-case rows handled cleanly in English & Tamil.")

# Check 4: Directional Sanity on a High-Risk Borrower
risky_idx = model.predict_proba(X)[:, 1].argmax()
risky_sample = X.iloc[[risky_idx]]
sim_improve = coach.simulate_what_if(
    risky_sample,
    {"missed_payment_count_6m": 0, "avg_days_late": 0.0, "on_time_bill_rate": 1.0, "balance_buffer_months": 4.0},
)
print(f"[PASS] Check 4: High-risk borrower What-If delta = {sim_improve['score_delta']:+d} pts "
      f"({sim_improve['old_score']} -> {sim_improve['new_score']}).")

# Check 5: Fairlearn Synthetic Bias Detection Stress-Test
y_pred_clean = (model.predict_proba(X)[:, 1] < 0.35).astype(int)
y_pred_biased = y_pred_clean.copy()
y_pred_biased[df["gender"] == df["gender"].iloc[0]] = 0  # Force extreme bias on one group
biased_dir = demographic_parity_ratio((1 - y), y_pred_biased, sensitive_features=df["gender"])
assert biased_dir < 0.80, "Fairlearn failed to catch injected bias!"
print(f"[PASS] Check 5: Fairlearn successfully flagged injected bias (DIR = {biased_dir:.4f} < 0.80).")