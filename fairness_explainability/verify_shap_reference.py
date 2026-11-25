import json
import numpy as np
import pandas as pd

from src.config import DATASET_PATH, FEATURE_COLUMNS
from src.schema import CreditRequest

from experiments.model_tuning.explain_frozen_models import explain
from fairness_explainability.shap_explainer import CreditExplainer


APPLICANT_ID = "APP_00675"
TOLERANCE = 1e-5

# Load the same synthetic applicant used by Member 3
dataset = pd.read_csv(DATASET_PATH)

row = dataset.loc[
    dataset["applicant_id"] == APPLICANT_ID
].iloc[0]

# Prepare the applicant's financial features
features = {}

for name in FEATURE_COLUMNS:
    value = row[name]

    features[name] = (
        None if pd.isna(value) else float(value)
    )

# Build the credit request
payload = {
    "applicant_id": APPLICANT_ID,
    "as_of_date": str(row["as_of_date"]),
    "schema_version": "1.0",
    "observation_window_months": 12,
    "currency": "INR",
    "features": features,
    "decision_context": {
        "requested_loan_amount": 10000,
        "requested_tenure_months": 6
    }
}

payload = CreditRequest.model_validate(
    payload
).model_dump(mode="json")

# Generate Member 3's reference explanations
reference = explain(APPLICANT_ID)

for expected in reference["models"]:

    model_name = expected["model_name"]

    print(f"\n===== {model_name.upper()} =====")

    # Generate Member 4's explanation
    explainer = CreditExplainer(model_name)

    actual = explainer.explain_applicant(
        payload,
        lang="en",
        top_k=30
    )

    expected_values = expected[
        "transformed_feature_contributions"
    ]

    actual_values = actual[
        "transformed_feature_contributions"
    ]

    # Test 1: Feature names
    assert set(expected_values) == set(actual_values)

    print("PASS: Transformed feature names")

    # Test 2: Base value
    np.testing.assert_allclose(
        actual["base_value"],
        expected["base_raw_margin"],
        atol=TOLERANCE,
        rtol=0
    )

    print("PASS: SHAP base value")

    # Test 3: Raw margin
    np.testing.assert_allclose(
        actual["raw_margin"],
        expected["raw_margin"],
        atol=TOLERANCE,
        rtol=0
    )

    print("PASS: Raw margin")

    # Test 4: Every feature contribution
    differences = []

    for feature in expected_values:

        expected_value = expected_values[feature]
        actual_value = actual_values[feature]

        difference = abs(
            expected_value - actual_value
        )

        differences.append(difference)

        np.testing.assert_allclose(
            actual_value,
            expected_value,
            atol=TOLERANCE,
            rtol=0,
            err_msg=f"Mismatch in {feature}"
        )

    print("PASS: All SHAP feature contributions")
    print("Features verified:", len(differences))
    print("Maximum difference:", max(differences))

    # Test 5: SHAP additivity
    reconstructed_margin = (
        actual["base_value"]
        + sum(actual_values.values())
    )

    np.testing.assert_allclose(
        reconstructed_margin,
        actual["raw_margin"],
        atol=TOLERANCE,
        rtol=0
    )

    print("PASS: SHAP additivity")

    # Test 6: Strict JSON compatibility
    json.dumps(actual, allow_nan=False)

    print("PASS: Strict JSON compatibility")

print("\nALL SHAP REFERENCE TESTS PASSED")