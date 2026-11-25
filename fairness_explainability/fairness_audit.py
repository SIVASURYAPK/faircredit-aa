
import json
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from fairlearn.metrics import (
    MetricFrame,
    selection_rate,
    demographic_parity_ratio,
    equal_opportunity_difference,
    equalized_odds_difference,
)

from src.config import FEATURE_COLUMNS, DECLINE_PD_THRESHOLD
from src.preprocessing import split_dataset
from src.predictor import predict_credit


# ============================================================
# 1. CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = ROOT / "data" / "raw" / "features_final_v1.csv"
PROTECTED_PATH = ROOT / "data" / "raw" / "protected_attrs.csv"

OUTPUT_JSON = (
    ROOT / "fairness_explainability" / "fairness_audit_report.json"
)

MODELS = [
    "logistic_regression",
    "xgboost",
]

PRIMARY_MODEL = "logistic_regression"

PROTECTED_ATTRIBUTES = [
    "gender",
    "region",
    "age_band",
    "urban_rural",
]

REQUESTED_LOAN_AMOUNT = 10000
REQUESTED_TENURE_MONTHS = 6
OBSERVATION_WINDOW_MONTHS = 12

DIAGNOSTIC_PD_THRESHOLD = float(DECLINE_PD_THRESHOLD)

MIN_GROUP_SIZE = 30
MIN_CLASS_COUNT = 10

MIN_DIR = 0.80
MAX_EOPP_DIFF = 0.05
MAX_EODDS_DIFF = 0.05

INTEGER_FEATURES = {
    "longest_zero_income_gap_days",
    "missed_payment_count_6m",
    "bills_due_count_6m",
    "overdraft_event_count_6m",
    "recovery_time_days",
    "months_observed",
    "income_source_count",
}


# ============================================================
# 2. HELPERS
# ============================================================

def safe_float(value, digits=4):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(result):
        return None

    return round(result, digits)


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return safe_float(numerator / denominator)


def safe_metric(func, *args, **kwargs):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            value = func(*args, **kwargs)
        return safe_float(value)
    except (ValueError, ZeroDivisionError):
        return None


def counts_dict(series):
    return {
        str(k): int(v)
        for k, v in series.value_counts().items()
    }


# ============================================================
# 3. LOAD AND VALIDATE DATA
# ============================================================

def load_audit_data(
    features_path=FEATURES_PATH,
    protected_path=PROTECTED_PATH,
):
    features_df = pd.read_csv(features_path)

    protected_df = pd.read_csv(
        protected_path,
        dtype={"pin_code": str},
    )

    required_features = (
        ["applicant_id", "as_of_date", "TARGET"]
        + list(FEATURE_COLUMNS)
    )

    required_protected = (
        ["applicant_id"] + PROTECTED_ATTRIBUTES
    )

    for name, df, required in [
        ("Financial", features_df, required_features),
        ("Protected", protected_df, required_protected),
    ]:
        missing = [
            col for col in required if col not in df.columns
        ]

        if missing:
            raise ValueError(
                f"{name} dataset missing columns: {missing}"
            )

        if df["applicant_id"].isna().any():
            raise ValueError(
                f"{name} dataset has missing applicant IDs."
            )

        if df["applicant_id"].duplicated().any():
            raise ValueError(
                f"{name} dataset has duplicate applicant IDs."
            )

    if (
        features_df["TARGET"].isna().any()
        or not features_df["TARGET"].isin([0, 1]).all()
    ):
        raise ValueError("TARGET must contain only 0 and 1.")

    return features_df, protected_df


# ============================================================
# 4. REPRODUCE HELD-OUT TEST SET
# ============================================================

def prepare_test_data(features_df, protected_df):

    splits = split_dataset(features_df)

    X_test, y_test = splits["test"]

    test_df = features_df.loc[
        X_test.index,
        ["applicant_id", "as_of_date"],
    ].copy()

    test_df = test_df.join(X_test)

    test_df["TARGET"] = y_test

    test_df = test_df.merge(
        protected_df[
            ["applicant_id"] + PROTECTED_ATTRIBUTES
        ],
        on="applicant_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if (test_df["_merge"] != "both").any():
        raise ValueError(
            "Some test applicants lack protected attributes."
        )

    return test_df.drop(columns=["_merge"])


# ============================================================
# 5. BUILD MEMBER 3'S PREDICTION REQUEST
# ============================================================

def build_credit_request(row):

    features = {}

    for name in FEATURE_COLUMNS:
        value = row[name]

        if pd.isna(value):
            features[name] = None

        elif isinstance(value, (np.integer, int)):
            features[name] = int(value)

        elif isinstance(value, (np.floating, float)):
            value = float(value)

            if not np.isfinite(value):
                features[name] = None

            elif name in INTEGER_FEATURES:
                if not value.is_integer():
                    raise ValueError(
                        f"{name} must be an integer: {value}"
                    )
                features[name] = int(value)

            else:
                features[name] = value

        else:
            features[name] = value

    return {
        "schema_version": "1.0",
        "applicant_id": str(row["applicant_id"]),
        "as_of_date": str(row["as_of_date"])[:10],
        "observation_window_months": (
            OBSERVATION_WINDOW_MONTHS
        ),
        "currency": "INR",
        "features": features,
        "decision_context": {
            "requested_loan_amount": REQUESTED_LOAN_AMOUNT,
            "requested_tenure_months": REQUESTED_TENURE_MONTHS,
        },
    }


# ============================================================
# 6. GENERATE PREDICTIONS FOR ONE MODEL
# ============================================================

def generate_predictions(test_df, model_name, policy_version):

    records = []

    total = len(test_df)

    print(f"\nRunning model: {model_name}, policy: {policy_version}")

    for position, (_, row) in enumerate(
        test_df.iterrows(),
        start=1,
    ):
        request = build_credit_request(row)

        try:
            result = predict_credit(
                request,
                model_name=model_name,
                policy_version=policy_version,
            )
        except Exception as exc:
            raise RuntimeError(
                f"{model_name} failed for applicant "
                f"{row['applicant_id']}: {exc}"
            ) from exc

        pd_value = float(result["pred_prob"])

        if not np.isfinite(pd_value) or not 0 <= pd_value <= 1:
            raise ValueError(
                f"Invalid PD from {model_name}: {pd_value}"
            )

        decision = str(result["decision"]).upper()

        if decision not in {
            "APPROVE", "REVIEW", "DECLINE"
        }:
            raise ValueError(
                f"Unexpected decision: {decision}"
            )

        reasons = result.get("policy_reasons") or []

        if not isinstance(reasons, list):
            raise ValueError(
                "policy_reasons must be a list."
            )

        records.append({
            "applicant_id": str(row["applicant_id"]),
            "TARGET": int(row["TARGET"]),
            "pred_prob": pd_value,
            "score": int(result["score"]),
            "decision": decision,
            "approved": int(decision == "APPROVE"),
            "reviewed": int(decision == "REVIEW"),
            "declined": int(decision == "DECLINE"),
            "suggested_limit": int(
                result["suggested_limit"]
            ),
            "policy_reasons": [
                str(reason) for reason in reasons
            ],
            "model_version": result.get(
                "model_version"
            ),
        })

        if position % 100 == 0 or position == total:
            print(f"  Processed {position}/{total}")

    return pd.DataFrame(records)


# ============================================================
# 7. FAIRLEARN METRICS
# ============================================================

def calculate_binary_fairness(
    audit_df,
    attribute,
    prediction_column,
):

    groups = (
        audit_df[attribute]
        .astype("string")
        .fillna("MISSING")
        .astype(str)
    )

    # TARGET=0 means the applicant did not default.
    y_true = (
        audit_df["TARGET"] == 0
    ).astype(int)

    y_pred = audit_df[
        prediction_column
    ].astype(int)

    metric_frame = MetricFrame(
        metrics={
            "selection_rate": selection_rate,
        },
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=groups,
    )

    group_metrics = {}

    small_groups = []
    low_class_groups = []

    for group_name in sorted(groups.unique()):

        mask = groups == group_name

        group_true = y_true.loc[mask]
        group_pred = y_pred.loc[mask]

        sample_count = int(mask.sum())

        good_mask = group_true == 1
        default_mask = group_true == 0

        good_count = int(good_mask.sum())
        default_count = int(default_mask.sum())

        true_positive_count = int(
            group_pred.loc[good_mask].sum()
        )

        false_positive_count = int(
            group_pred.loc[default_mask].sum()
        )

        if sample_count < MIN_GROUP_SIZE:
            small_groups.append(str(group_name))

        if (
            good_count < MIN_CLASS_COUNT
            or default_count < MIN_CLASS_COUNT
        ):
            low_class_groups.append(str(group_name))

        group_metrics[str(group_name)] = {
            "sample_count": sample_count,
            "non_default_count": good_count,
            "default_count": default_count,
            "positive_prediction_rate": safe_float(
                metric_frame.by_group.loc[
                    group_name, "selection_rate"
                ]
            ),
            "true_positive_rate": safe_rate(
                true_positive_count,
                good_count,
            ),
            "false_positive_rate": safe_rate(
                false_positive_count,
                default_count,
            ),
        }

    positive_count = int(y_pred.sum())

    all_zero = positive_count == 0
    all_positive = positive_count == len(y_pred)

    has_two_groups = len(group_metrics) >= 2

    has_both_classes = all(
        item["non_default_count"] > 0
        and item["default_count"] > 0
        for item in group_metrics.values()
    )

    if has_two_groups and not all_zero:
        dir_value = safe_metric(
            demographic_parity_ratio,
            y_true,
            y_pred,
            sensitive_features=groups,
        )
    else:
        dir_value = None

    if has_two_groups and has_both_classes:

        eopp_value = safe_metric(
            equal_opportunity_difference,
            y_true,
            y_pred,
            sensitive_features=groups,
        )

        eodds_value = safe_metric(
            equalized_odds_difference,
            y_true,
            y_pred,
            sensitive_features=groups,
        )

    else:
        eopp_value = None
        eodds_value = None

    warnings_list = []

    if all_zero:
        warnings_list.append(
            "No positive predictions. Approval "
            "fairness cannot be established."
        )

    if all_positive:
        warnings_list.append(
            "All predictions are positive; "
            "fairness metrics have limited value."
        )

    if small_groups:
        warnings_list.append(
            "Small groups: " + ", ".join(small_groups)
        )

    if low_class_groups:
        warnings_list.append(
            "Insufficient class counts: "
            + ", ".join(low_class_groups)
        )

    if not has_both_classes:
        warnings_list.append(
            "Some groups lack examples from "
            "both target classes."
        )

    sufficient = (
        has_two_groups
        and not all_zero
        and not all_positive
        and not small_groups
        and not low_class_groups
        and dir_value is not None
        and eopp_value is not None
        and eodds_value is not None
    )

    if not sufficient:
        status = "INSUFFICIENT_EVIDENCE"

    elif (
        dir_value >= MIN_DIR
        and eopp_value <= MAX_EOPP_DIFF
        and eodds_value <= MAX_EODDS_DIFF
    ):
        status = "WITHIN_EXPLORATORY_THRESHOLDS"

    else:
        status = "REVIEW_NEEDED"

    return {
        "sample_count": int(len(audit_df)),
        "positive_prediction_count": positive_count,
        "positive_prediction_rate": safe_rate(
            positive_count,
            len(audit_df),
        ),
        "group_metrics": group_metrics,
        "disparate_impact_ratio": dir_value,
        "equal_opportunity_difference": eopp_value,
        "equalized_odds_difference": eodds_value,
        "review_status": status,
        "warnings": warnings_list,
    }


# ============================================================
# 8. POLICY OUTCOMES BY DEMOGRAPHIC GROUP
# ============================================================

def calculate_policy_group_metrics(
    audit_df,
    attribute,
):

    groups = (
        audit_df[attribute]
        .astype("string")
        .fillna("MISSING")
        .astype(str)
    )

    results = {}

    for group_name in sorted(groups.unique()):

        subset = audit_df.loc[
            groups == group_name
        ]

        count = len(subset)

        approvals = int(subset["approved"].sum())
        reviews = int(subset["reviewed"].sum())
        declines = int(subset["declined"].sum())

        good_mask = subset["TARGET"] == 0
        default_mask = subset["TARGET"] == 1

        good_count = int(good_mask.sum())
        default_count = int(default_mask.sum())

        reason_counter = Counter()

        for reasons in subset["policy_reasons"]:
            reason_counter.update(set(reasons))

        results[str(group_name)] = {
            "sample_count": int(count),
            "non_default_count": good_count,
            "default_count": default_count,
            "approval_count": approvals,
            "review_count": reviews,
            "decline_count": declines,
            "approval_rate": safe_rate(
                approvals, count
            ),
            "review_rate": safe_rate(
                reviews, count
            ),
            "decline_rate": safe_rate(
                declines, count
            ),
            "good_repayer_approval_rate": safe_rate(
                int(subset.loc[
                    good_mask, "approved"
                ].sum()),
                good_count,
            ),
            "default_repayer_approval_rate": safe_rate(
                int(subset.loc[
                    default_mask, "approved"
                ].sum()),
                default_count,
            ),
            "mean_predicted_default_probability": (
                safe_float(subset["pred_prob"].mean())
            ),
            "mean_credit_score": safe_float(
                subset["score"].mean()
            ),
            "policy_reason_counts": dict(
                sorted(reason_counter.items())
            ),
        }

    return results


# ============================================================
# 9. POLICY REASON SUMMARY
# ============================================================

def calculate_policy_reasons(audit_df):

    overall = Counter()

    by_decision = {
        "APPROVE": Counter(),
        "REVIEW": Counter(),
        "DECLINE": Counter(),
    }

    for _, row in audit_df.iterrows():

        reasons = set(row["policy_reasons"])

        overall.update(reasons)

        by_decision[row["decision"]].update(reasons)

    return {
        "overall_reason_counts": dict(
            sorted(overall.items())
        ),
        "reasons_by_decision": {
            decision: dict(sorted(counter.items()))
            for decision, counter in by_decision.items()
        },
        "counting_method": (
            "Applicants per reason; an applicant "
            "may have multiple reasons."
        ),
    }


# ============================================================
# 10. AUDIT ONE MODEL
# ============================================================

def audit_one_model(
    test_df,
    predictions_df,
    model_name,
):

    audit_df = test_df[
        ["applicant_id"] + PROTECTED_ATTRIBUTES
    ].merge(
        predictions_df,
        on="applicant_id",
        how="inner",
        validate="one_to_one",
    )

    if len(audit_df) != len(test_df):
        raise ValueError(
            f"{model_name}: prediction merge mismatch."
        )

    # Research-only model-risk screening.
    # This is NOT an official loan approval.
    audit_df["risk_screen_positive"] = (
        audit_df["pred_prob"]
        <= DIAGNOSTIC_PD_THRESHOLD
    ).astype(int)

    policy_fairness = {}
    model_risk_fairness = {}

    for attribute in PROTECTED_ATTRIBUTES:

        policy_metrics = calculate_binary_fairness(
            audit_df,
            attribute,
            "approved",
        )

        policy_metrics["group_policy_outcomes"] = (
            calculate_policy_group_metrics(
                audit_df,
                attribute,
            )
        )

        policy_fairness[attribute] = policy_metrics

        model_risk_fairness[attribute] = (
            calculate_binary_fairness(
                audit_df,
                attribute,
                "risk_screen_positive",
            )
        )

    overall_results = {
        "sample_count": int(len(audit_df)),
        "approval_count": int(
            audit_df["approved"].sum()
        ),
        "review_count": int(
            audit_df["reviewed"].sum()
        ),
        "decline_count": int(
            audit_df["declined"].sum()
        ),
        "approval_rate": safe_float(
            audit_df["approved"].mean()
        ),
        "review_rate": safe_float(
            audit_df["reviewed"].mean()
        ),
        "decline_rate": safe_float(
            audit_df["declined"].mean()
        ),
        "decision_counts": counts_dict(
            audit_df["decision"]
        ),
        "actual_non_default_count": int(
            (audit_df["TARGET"] == 0).sum()
        ),
        "actual_default_count": int(
            (audit_df["TARGET"] == 1).sum()
        ),
        "mean_predicted_default_probability": (
            safe_float(audit_df["pred_prob"].mean())
        ),
        "mean_credit_score": safe_float(
            audit_df["score"].mean()
        ),
    }

    return {
        "model_name": model_name,
        "model_versions": (
            audit_df["model_version"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
        "overall_results": overall_results,
        "policy_fairness": policy_fairness,
        "model_risk_fairness": {
            "diagnostic_definition": (
                "Positive if predicted default "
                "probability <= decline threshold."
            ),
            "diagnostic_pd_threshold": (
                DIAGNOSTIC_PD_THRESHOLD
            ),
            "is_official_approval": False,
            "attributes": model_risk_fairness,
        },
        "policy_reason_analysis": (
            calculate_policy_reasons(audit_df)
        ),
    }


# ============================================================
# 11. BUILD MODEL COMPARISON
# ============================================================

def build_model_comparison(model_reports):

    comparison = {}

    for attribute in PROTECTED_ATTRIBUTES:

        comparison[attribute] = {}

        for model_name, result in model_reports.items():

            diagnostic = result[
                "model_risk_fairness"
            ]["attributes"][attribute]

            official = result[
                "policy_fairness"
            ][attribute]

            comparison[attribute][model_name] = {
                "diagnostic_dir": diagnostic[
                    "disparate_impact_ratio"
                ],
                "diagnostic_equal_opportunity_difference": (
                    diagnostic[
                        "equal_opportunity_difference"
                    ]
                ),
                "diagnostic_equalized_odds_difference": (
                    diagnostic[
                        "equalized_odds_difference"
                    ]
                ),
                "diagnostic_review_status": diagnostic[
                    "review_status"
                ],
                "official_approval_rate": official[
                    "positive_prediction_rate"
                ],
                "official_policy_review_status": official[
                    "review_status"
                ],
            }

    return comparison


# ============================================================
# 12. MAIN TWO-MODEL AUDIT
# ============================================================

def run_fairness_audit(features_path=FEATURES_PATH, protected_path=PROTECTED_PATH, output_json=None):
    from src.config import get_policy_thresholds
    features, protected = load_audit_data(features_path, protected_path)
    manifest = pd.read_csv(ROOT / "reports" / "data_splits.csv", dtype={"applicant_id": str})
    assert not manifest["applicant_id"].duplicated().any()
    assert not set(FEATURE_COLUMNS).intersection(protected.columns), "Protected feature leakage"
    report = {"report_type": "two_model_two_policy_audit", "simulation_only": True,
              "policy_status": "experimental", "fairness_and_risk_approval_required": True,
              "primary_model": PRIMARY_MODEL, "cohorts": {},
              "decision_context": {"requested_loan_amount": REQUESTED_LOAN_AMOUNT,
                                   "requested_tenure_months": REQUESTED_TENURE_MONTHS,
                                   "observation_window_months": OBSERVATION_WINDOW_MONTHS},
              "limitations": ["Synthetic data only; validation is policy selection data.",
                              "Test cohort is a separate evaluation, not for threshold tuning.",
                              "Exploratory fairness thresholds are not legal compliance guarantees.",
                              "No uncertainty intervals; small groups require caution."]}
    for cohort in ("validation", "test"):
        ids = set(manifest.loc[manifest["split"] == cohort, "applicant_id"])
        df = features.loc[features["applicant_id"].astype(str).isin(ids)].merge(
            protected[["applicant_id"] + PROTECTED_ATTRIBUTES], on="applicant_id", how="left", validate="one_to_one", indicator=True)
        assert len(df) == len(ids) == 750 and (df["_merge"] == "both").all()
        df = df.drop(columns="_merge")
        cohort_report = {"sample_count": len(df), "policies": {}}
        previous = {}
        for version in ("1.0.0", "1.1.0"):
            thresholds = get_policy_thresholds(version)
            models = {}
            for name in MODELS:
                pred = generate_predictions(df, name, version)
                indexed = pred.set_index("applicant_id").sort_index()
                if version == "1.0.0":
                    previous[name] = indexed
                else:
                    old = previous[name]
                    assert indexed.index.equals(old.index)
                    assert np.allclose(indexed["pred_prob"], old["pred_prob"], atol=1e-7, rtol=0)
                    assert indexed["declined"].equals(old["declined"])
                models[name] = audit_one_model(df, pred, name)
                approved = pred.loc[pred["approved"] == 1, "TARGET"]
                models[name]["overall_results"]["synthetic_default_rate_among_approvals"] = safe_rate(int(approved.sum()), len(approved))
                print(cohort, version, name, models[name]["overall_results"]["decision_counts"])
            cohort_report["policies"][version] = {"approve_below": thresholds.approve_below,
                "decline_above": thresholds.decline_above, "models": models,
                "model_comparison": build_model_comparison(models)}
        report["cohorts"][cohort] = cohort_report
    output = Path(output_json or ROOT / "fairness_explainability" / "fairness_policy_comparison.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(f"Report saved: {output}")
    return report

if __name__ == "__main__":
    run_fairness_audit()
