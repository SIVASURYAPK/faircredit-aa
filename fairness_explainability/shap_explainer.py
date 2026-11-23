
import json
from pathlib import Path

import numpy as np
import pandas as pd
import shap

from src.predictor import load_model, prepare_input
from src.schema import CreditRequest


# ============================================================
# 1. ENGLISH AND TAMIL FEATURE LABELS
# ============================================================

FEATURE_LABELS = {
    "avg_monthly_inflow": {
        "en": "Average monthly verified income",
        "ta": "சராசரி மாதாந்திர வருமானம்"
    },
    "median_monthly_inflow": {
        "en": "Consistent baseline monthly income",
        "ta": "நிலையான மாதாந்திர வருமானம்"
    },
    "obligation_to_inflow_ratio": {
        "en": "Monthly recurring expense ratio",
        "ta": "மாதாந்திர செலவு விகிதம்"
    },
    "emi_to_inflow_ratio": {
        "en": "Existing EMI burden ratio",
        "ta": "தற்போதைய கடன் தவணை விகிதம்"
    },
    "income_cv": {
        "en": "Monthly income variability",
        "ta": "மாதாந்திர வருமான மாறுபாடு"
    },
    "active_day_ratio": {
        "en": "Active earning days ratio",
        "ta": "செயலில் உள்ள வேலை நாட்கள் விகிதம்"
    },
    "longest_zero_income_gap_days": {
        "en": "Longest gap without income",
        "ta": "வருமானம் இல்லாத நீண்ட இடைவெளி"
    },
    "income_trend_ratio": {
        "en": "Recent income growth trend",
        "ta": "சமீபத்திய வருமான வளர்ச்சி"
    },
    "on_time_bill_rate": {
        "en": "On-time bill payment rate",
        "ta": "சரியான நேரத்தில் கட்டணம் செலுத்தும் விகிதம்"
    },
    "avg_days_late": {
        "en": "Average bill payment delay",
        "ta": "கட்டணம் செலுத்துவதில் சராசரி தாமதம்"
    },
    "missed_payment_count_6m": {
        "en": "Missed payments in last 6 months",
        "ta": "கடந்த 6 மாதங்களில் தவறிய கட்டணங்கள்"
    },
    "bills_due_count_6m": {
        "en": "Number of bills due in last 6 months",
        "ta": "கடந்த 6 மாதங்களில் செலுத்த வேண்டிய கட்டணங்கள்"
    },
    "balance_buffer_months": {
        "en": "Savings reserve buffer in months",
        "ta": "சேமிப்பு இருப்பு காலம்"
    },
    "overdraft_event_count_6m": {
        "en": "Low-balance or overdraft events",
        "ta": "குறைந்த இருப்பு நிகழ்வுகள்"
    },
    "shock_severity": {
        "en": "Weather or seasonal shock severity",
        "ta": "வானிலை அல்லது பருவகால பாதிப்பு"
    },
    "recovery_time_days": {
        "en": "Income recovery time after shock",
        "ta": "பாதிப்பிற்குப் பின் வருமான மீட்பு காலம்"
    },
    "seasonality_adjusted_income": {
        "en": "Seasonality-adjusted income",
        "ta": "பருவகால சரிசெய்யப்பட்ட வருமானம்"
    },
    "months_observed": {
        "en": "Months of verified financial history",
        "ta": "சரிபார்க்கப்பட்ட நிதி வரலாறு (மாதங்கள்)"
    },
    "income_source_count": {
        "en": "Number of income sources",
        "ta": "வருமான ஆதாரங்களின் எண்ணிக்கை"
    },
    "has_existing_loan": {
        "en": "Existing loan indicator",
        "ta": "ஏற்கனவே கடன் உள்ளதா"
    },
    "missingindicator_on_time_bill_rate": {
        "en": "Missing on-time payment information",
        "ta": "சரியான நேர கட்டணத் தகவல் இல்லை"
    },
    "missingindicator_avg_days_late": {
        "en": "Missing payment delay information",
        "ta": "கட்டணத் தாமதத் தகவல் இல்லை"
    },
    "missingindicator_missed_payment_count_6m": {
        "en": "Missing missed-payment information",
        "ta": "தவறிய கட்டணத் தகவல் இல்லை"
    },
    "missingindicator_recovery_time_days": {
        "en": "Missing income recovery information",
        "ta": "வருமான மீட்புத் தகவல் இல்லை"
    }
}


# ============================================================
# 2. CREDIT EXPLAINER
# ============================================================

class CreditExplainer:

    def __init__(self, model_name="logistic_regression"):

        if model_name not in ("logistic_regression", "xgboost"):
            raise ValueError(
                "model_name must be 'logistic_regression' or 'xgboost'"
            )

        self.model_name = model_name

        # Load Member 3's saved model bundle.
        self.bundle = load_model(model_name)

        self.pipeline = self.bundle["model"]

        self.preprocessor = self.pipeline.named_steps[
            "preprocessing"
        ]

        self.classifier = self.pipeline.named_steps["model"]

        self.feature_names = list(
            self.pipeline[:-1].get_feature_names_out()
        )

        self.explainer = self._create_explainer()

    # --------------------------------------------------------
    # CREATE EXPLAINER
    # --------------------------------------------------------

    def _create_explainer(self):

        if self.model_name == "logistic_regression":
            # Exact linear contribution decomposition
            # relative to zero in transformed space.
            return None

        if self.model_name == "xgboost":
            return shap.TreeExplainer(
                self.classifier,
                model_output="raw"
            )

        raise ValueError("Unsupported model")

    # --------------------------------------------------------
    # PREPARE APPLICANT FEATURES
    # --------------------------------------------------------

    def _prepare_features(self, payload):

        request = CreditRequest.model_validate(payload)

        # Use Member 3's official input preparation.
        X = prepare_input(request)

        # Apply the saved fitted preprocessing pipeline.
        X_transformed = self.preprocessor.transform(X)

        if hasattr(X_transformed, "toarray"):
            X_transformed = X_transformed.toarray()

        X_transformed = np.asarray(
            X_transformed,
            dtype=float
        )

        if X_transformed.shape[0] != 1:
            raise ValueError(
                "Only one applicant can be explained at a time."
            )

        if X_transformed.shape[1] != len(self.feature_names):
            raise ValueError(
                "Transformed feature count does not match "
                "the saved model's feature names."
            )

        return request, X_transformed

    # --------------------------------------------------------
    # CALCULATE FEATURE CONTRIBUTIONS
    # --------------------------------------------------------

    def _calculate_shap(self, X_transformed):

        if self.model_name == "logistic_regression":

            coefficients = np.asarray(
                self.classifier.coef_[0],
                dtype=float
            )

            intercept = float(
                self.classifier.intercept_[0]
            )

            contributions = (
                X_transformed[0] * coefficients
            )

            base_value = intercept

            # FIX: Pass named columns to the classifier.
            # This avoids the sklearn feature-name warning.
            X_named = pd.DataFrame(
                X_transformed,
                columns=self.feature_names
            )

            raw_margin = float(
                self.classifier.decision_function(
                    X_named
                )[0]
            )

        else:

            explanation = self.explainer(
                X_transformed
            )

            values = np.asarray(
                explanation.values
            )

            if values.ndim != 2 or values.shape[0] != 1:
                raise ValueError(
                    "Unexpected XGBoost SHAP output shape: "
                    f"{values.shape}"
                )

            contributions = values[0]

            base_value = float(
                np.asarray(
                    explanation.base_values
                ).reshape(-1)[0]
            )

            raw_margin = float(
                self.classifier.predict(
                    X_transformed,
                    output_margin=True
                )[0]
            )

        if len(contributions) != len(self.feature_names):
            raise ValueError(
                "Feature contributions do not match "
                "the transformed feature names."
            )

        # Verify that contributions reconstruct
        # the underlying classifier's raw output.
        reconstructed_margin = (
            base_value + float(np.sum(contributions))
        )

        if not np.isclose(
            reconstructed_margin,
            raw_margin,
            rtol=1e-4,
            atol=1e-4
        ):
            raise ValueError(
                "Explanation does not reconstruct "
                "the model's raw output. "
                f"Expected {raw_margin}, "
                f"got {reconstructed_margin}."
            )

        return (
            contributions,
            base_value,
            raw_margin
        )

    # --------------------------------------------------------
    # EXPLAIN ONE APPLICANT
    # --------------------------------------------------------

    def explain_applicant(
        self,
        payload,
        lang="en",
        top_k=3
    ):

        if lang not in ("en", "ta"):
            raise ValueError(
                "Supported languages are 'en' and 'ta'."
            )

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(
                "top_k must be a positive integer."
            )

        request, X_transformed = self._prepare_features(
            payload
        )

        (
            contributions,
            base_value,
            raw_margin
        ) = self._calculate_shap(X_transformed)

        ranked_indices = np.argsort(
            -np.abs(contributions)
        )[:top_k]

        reasons = []

        for index in ranked_indices:

            feature = self.feature_names[index]

            contribution = float(
                contributions[index]
            )

            transformed_value = float(
                X_transformed[0, index]
            )

            label = FEATURE_LABELS.get(
                feature, {}
            ).get(lang, feature)

            if contribution > 0:
                direction = "increases_default_risk"

            elif contribution < 0:
                direction = "decreases_default_risk"

            else:
                direction = "neutral"

            reasons.append({
                "feature": feature,
                "label": label,
                "transformed_value": round(
                    transformed_value, 6
                ),
                "shap_value": round(
                    contribution, 6
                ),
                "direction": direction
            })

        return {
            "applicant_id": request.applicant_id,
            "model_name": self.model_name,
            "language": lang,
            "explained_output": "uncalibrated_raw_margin",
            "output_units": "log_odds",
            "baseline_type": (
                "zero_transformed_feature_reference"
                if self.model_name == "logistic_regression"
                else "tree_shap_reference"
            ),
            "base_value": round(base_value, 6),
            "raw_margin": round(raw_margin, 6),
            "shap_reason_codes": reasons,
            "simulation_only": True,
            "disclaimer": (
                "These contributions explain the underlying "
                "classifier's raw log-odds, not the calibrated "
                "default probability, credit score, or final "
                "policy decision. Logistic Regression uses a "
                "zero transformed-feature reference rather "
                "than a population-average SHAP baseline."
            )
        }

    # --------------------------------------------------------
    # WHAT-IF SIMULATION
    # --------------------------------------------------------

    def simulate_what_if(
        self,
        payload,
        updates,
        lang="en"
    ):

        if lang not in ("en", "ta"):
            raise ValueError(
                "Supported languages are 'en' and 'ta'."
            )

        from src.simulator import simulate

        result = simulate(
            payload,
            updates,
            model_name=self.model_name
        )

        result["language"] = lang

        return result


# ============================================================
# 3. LOCAL TEST
# ============================================================

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[1]

    request_path = (
        project_root
        / "examples"
        / "prediction_request.json"
    )

    with open(
        request_path,
        "r",
        encoding="utf-8"
    ) as file:
        payload = json.load(file)

    print("\n========== LOGISTIC REGRESSION ==========")

    logistic_explainer = CreditExplainer(
        model_name="logistic_regression"
    )

    print(
        json.dumps(
            logistic_explainer.explain_applicant(
                payload,
                lang="en",
                top_k=5
            ),
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n========== XGBOOST ==========")

    xgb_explainer = CreditExplainer(
        model_name="xgboost"
    )

    print(
        json.dumps(
            xgb_explainer.explain_applicant(
                payload,
                lang="en",
                top_k=5
            ),
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n========== TAMIL EXPLANATION ==========")

    print(
        json.dumps(
            logistic_explainer.explain_applicant(
                payload,
                lang="ta",
                top_k=3
            ),
            indent=2,
            ensure_ascii=False
        )
    )

    print("\nAll SHAP explanation tests completed.")
