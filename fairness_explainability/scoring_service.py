
import json
from pathlib import Path

from src.predictor import predict_credit
from src.simulator import simulate

from fairness_explainability.shap_explainer import CreditExplainer


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIT_REPORT_PATH = (
    PROJECT_ROOT
    / "fairness_explainability"
    / "fairness_audit_report.json"
)


# ============================================================
# FAIR CREDIT SERVICE
# ============================================================

class FairCreditService:

    def __init__(self):

        # Member 3's primary model is Logistic Regression.
        # SHAP explanations must correspond to that model.
        self.explainer = CreditExplainer(
            model_name="logistic_regression"
        )

    # --------------------------------------------------------
    # 1. OFFICIAL CREDIT SCORING + EXPLANATION
    # --------------------------------------------------------

    def score_applicant(
        self,
        payload: dict,
        lang: str = "en"
    ) -> dict:

        if lang not in ("en", "ta"):
            raise ValueError(
                "Supported languages are 'en' and 'ta'."
            )

        # Official calibrated credit prediction.
        result = predict_credit(payload)

        # Explain the underlying classifier.
        explanation = self.explainer.explain_applicant(
            payload,
            lang=lang,
            top_k=5
        )

        # Attach SHAP explanations without modifying
        # the official prediction.
        result["shap_explanation"] = explanation

        result["language"] = lang

        return result

    # --------------------------------------------------------
    # 2. WHAT-IF SIMULATION
    # --------------------------------------------------------

    def simulate_applicant(
        self,
        payload: dict,
        changes: dict,
        lang: str = "en"
    ) -> dict:

        if lang not in ("en", "ta"):
            raise ValueError(
                "Supported languages are 'en' and 'ta'."
            )

        # Member 3's official simulator handles:
        # - Input validation
        # - Allowed feature changes
        # - Calibrated predictions
        # - Credit score recalculation
        # - Policy decisions

        result = simulate(
            payload,
            changes,
            model_name="logistic_regression"
        )

        result["language"] = lang

        return result

    # --------------------------------------------------------
    # 3. FAIRNESS AUDIT REPORT
    # --------------------------------------------------------

    def get_fairness_audit(self) -> dict:

        if not AUDIT_REPORT_PATH.exists():
            raise FileNotFoundError(
                "Fairness audit report not generated yet. "
                "Run fairness_audit.py first."
            )

        with open(
            AUDIT_REPORT_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            report = json.load(file)

        return report


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    request_path = (
        PROJECT_ROOT
        / "examples"
        / "prediction_request.json"
    )

    with open(
        request_path,
        "r",
        encoding="utf-8"
    ) as file:
        payload = json.load(file)

    service = FairCreditService()

    # --------------------------------------------------------
    # TEST 1: CREDIT SCORING + SHAP
    # --------------------------------------------------------

    print("\n========== CREDIT SCORING + SHAP ==========")

    prediction = service.score_applicant(
        payload,
        lang="en"
    )

    print(
        json.dumps(
            prediction,
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # TEST 2: TAMIL EXPLANATIONS
    # --------------------------------------------------------

    print("\n========== TAMIL EXPLANATIONS ==========")

    tamil_prediction = service.score_applicant(
        payload,
        lang="ta"
    )

    print(
        json.dumps(
            tamil_prediction["shap_explanation"],
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------------
    # TEST 3: WHAT-IF SIMULATION
    # --------------------------------------------------------

    print("\n========== WHAT-IF SIMULATION ==========")

    simulation = service.simulate_applicant(
        payload,
        changes={
            "income_cv": 0.20
        },
        lang="en"
    )

    print(
        json.dumps(
            simulation,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\nAll scoring service tests completed.")
