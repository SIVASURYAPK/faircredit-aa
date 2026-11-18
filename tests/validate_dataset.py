import sys
import pandas as pd
import numpy as np

# Exact 19 features from agreed schema
EXPECTED_FEATURES = {
    # A. Income and capacity
    "avg_monthly_inflow": "float",
    "median_monthly_inflow": "float",
    "obligation_to_inflow_ratio": "float",
    "emi_to_inflow_ratio": "float",
    # B. Income stability
    "income_cv": "float",
    "active_day_ratio": "float",
    "longest_zero_income_gap_days": "int",
    "income_trend_ratio": "float",
    # C. Payment behaviour
    "on_time_bill_rate": "float",
    "avg_days_late": "float",
    "missed_payment_count_6m": "int",
    "bills_due_count_6m": "int",
    # D. Savings and liquidity
    "balance_buffer_months": "float",
    "overdraft_event_count_6m": "int",
    # E. Weather and resilience
    "shock_severity": "float",
    "recovery_time_days": "float",
    "seasonality_adjusted_income": "float",
    # F. Data sufficiency
    "months_observed": "int",
    "income_source_count": "int",
}

# FIX 1: added age_band and region (our protected column names)
FORBIDDEN_PROTECTED_COLS = {"gender", "caste", "religion", "age", "age_group", "age_band",
                            "region", "pin_code", "latitude", "longitude"}

def validate_dataset(df: pd.DataFrame, is_training: bool = True) -> bool:
    errors = []
    warnings = []

    # 1. Check ID and Target columns
    if "applicant_id" not in df.columns:
        errors.append("Missing required primary key column: 'applicant_id'")
    elif df["applicant_id"].duplicated().any():
        errors.append(f"Duplicate 'applicant_id' values found: {df['applicant_id'].duplicated().sum()} duplicates")

    if is_training:
        if "TARGET" not in df.columns:
            errors.append("Missing 'TARGET' column for training dataset")
        elif not set(df["TARGET"].dropna().unique()).issubset({0, 1}):
            errors.append("Column 'TARGET' must contain only binary values {0, 1}")

    # 2. Check Protected Attributes Leakage
    leaked = FORBIDDEN_PROTECTED_COLS.intersection(set(df.columns))
    if leaked:
        errors.append(f"CRITICAL LEAKAGE: Protected attributes found in model input: {leaked}")

    # 3. Check all 19 feature columns & types
    missing_cols = [col for col in EXPECTED_FEATURES if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required feature columns: {missing_cols}")
        return _report(errors, warnings)

    for col, expected_dtype in EXPECTED_FEATURES.items():
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' must be numeric ({expected_dtype}), got {df[col].dtype}")
        elif expected_dtype == "int":
            non_null = df[col].dropna()
            if not np.all(np.equal(np.mod(non_null, 1), 0)):
                errors.append(f"Column '{col}' is specified as Integer but contains fractional decimals")

    # 4. Mandatory Data Rules
    # Non-negative income values
    for inc_col in ["avg_monthly_inflow", "median_monthly_inflow", "seasonality_adjusted_income"]:
        if (df[inc_col].dropna() < 0).any():
            errors.append(f"Rule Violation: '{inc_col}' contains negative values")

    # Ratios must be decimals (0 to 1), not percentages (0 to 100)
    for bounded_ratio in ["active_day_ratio", "on_time_bill_rate", "shock_severity"]:
        vals = df[bounded_ratio].dropna()
        if (vals < 0).any() or (vals > 1.0).any():
            errors.append(f"Rule Violation: '{bounded_ratio}' must be a decimal in [0.0, 1.0], found range [{vals.min()}, {vals.max()}]")

    for ratio_col in ["obligation_to_inflow_ratio", "emi_to_inflow_ratio"]:
        vals = df[ratio_col].dropna()
        if (vals < 0).any():
            errors.append(f"Rule Violation: '{ratio_col}' cannot be negative")
        if (vals > 5.0).any():
            warnings.append(f"Check units for '{ratio_col}': max value is {vals.max():.2f} (ensure decimal, not %)")

    # FIX 3: observation window must be 6-12 months (spec)
    obs = df["months_observed"].dropna()
    if (obs < 6).any() or (obs > 12).any():
        errors.append(f"Rule Violation: 'months_observed' must be 6-12, found range [{obs.min()}, {obs.max()}]")

    # 5. Special Cases (Null vs Zero enforcement)
    # Rule A: income_cv must be null if avg_monthly_inflow == 0
    bad_cv = df[(df["avg_monthly_inflow"] == 0) & (df["income_cv"].notna())]
    if len(bad_cv) > 0:
        errors.append(f"Special Case Violation: {len(bad_cv)} rows have avg_monthly_inflow == 0 but non-null 'income_cv'")

    # Rule B: on_time_bill_rate must be null if bills_due_count_6m == 0
    bad_bills = df[(df["bills_due_count_6m"] == 0) & (df["on_time_bill_rate"].notna())]
    if len(bad_bills) > 0:
        errors.append(f"Special Case Violation: {len(bad_bills)} rows have bills_due_count_6m == 0 but non-null 'on_time_bill_rate'")

    # Rule C: recovery_time_days must be null if shock_severity is 0 or null
    bad_rec = df[((df["shock_severity"].isna()) | (df["shock_severity"] == 0)) & (df["recovery_time_days"].notna())]
    if len(bad_rec) > 0:
        errors.append(f"Special Case Violation: {len(bad_rec)} rows have no shock (shock_severity 0/null) but non-null 'recovery_time_days'")

    # Rule D: Check if zeros were accidentally used instead of nulls across all columns
    if df[list(EXPECTED_FEATURES.keys())].isna().sum().sum() == 0:
        warnings.append("Zero NaN values detected across the entire dataset - verify missing values were not auto-filled with 0!")

    return _report(errors, warnings)


def _report(errors: list, warnings: list) -> bool:
    print("=" * 60)
    print("FAIRCREDIT AA - DATASET SCHEMA VALIDATION REPORT")
    print("=" * 60)
    if warnings:
        print("\n[WARNINGS]:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("\n[FAILED - ERRORS FOUND]:")
        for e in errors:
            print(f"  x {e}")
        print("\nStatus: INVALID DATASET. Fix errors above before model training.")
        return False
    print("\nStatus: PASSED! All 19 features and special null rules verified.")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_dataset.py <path_to_dataset.csv>")
        sys.exit(1)
    data = pd.read_csv(sys.argv[1])
    is_valid = validate_dataset(data, is_training=("TARGET" in data.columns))
    sys.exit(0 if is_valid else 1)