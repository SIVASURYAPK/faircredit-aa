"""Simulation-only integration of frozen models, SHAP and policy audit."""
import json
from pathlib import Path
from src.config import ROLLBACK_POLICY_VERSION, POLICY_VERSION, PRIMARY_MODEL, get_policy_thresholds
from src.predictor import predict_credit
from src.simulator import simulate
from fairness_explainability.shap_explainer import CreditExplainer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_REPORT_PATH = PROJECT_ROOT / "fairness_explainability" / "fairness_policy_comparison.json"


class FairCreditService:
    def __init__(self):
        self._explainers = {}

    @staticmethod
    def _validate(lang, model_name, policy_version):
        if lang not in ("en", "ta"):
            raise ValueError("Supported languages are en and ta.")
        if model_name not in ("logistic_regression", "xgboost"):
            raise ValueError("Unsupported model.")
        get_policy_thresholds(policy_version)

    def _get_explainer(self, model_name):
        if model_name not in self._explainers:
            self._explainers[model_name] = CreditExplainer(model_name=model_name)
        return self._explainers[model_name]

    @staticmethod
    def _finish(result, lang, policy_version):
        result["language"] = lang
        result["policy_status"] = ("experimental" if policy_version == POLICY_VERSION else "rollback")
        result["fairness_and_risk_approval_required"] = True
        result["simulation_only"] = True
        json.dumps(result, allow_nan=False)
        return result

    def score_applicant(self, payload, lang="en", *, model_name=PRIMARY_MODEL,
                        policy_version=ROLLBACK_POLICY_VERSION):
        self._validate(lang, model_name, policy_version)
        result = predict_credit(payload, model_name=model_name, policy_version=policy_version)
        result["shap_explanation"] = self._get_explainer(model_name).explain_applicant(payload, lang=lang, top_k=5)
        return self._finish(result, lang, policy_version)

    def simulate_applicant(self, payload, changes, lang="en", *, model_name=PRIMARY_MODEL,
                           policy_version=ROLLBACK_POLICY_VERSION):
        self._validate(lang, model_name, policy_version)
        result = simulate(payload, changes, model_name=model_name, policy_version=policy_version)
        return self._finish(result, lang, policy_version)

    def get_fairness_audit(self):
        if not AUDIT_REPORT_PATH.exists():
            raise FileNotFoundError("Run fairness_explainability.fairness_audit to generate the policy comparison report.")
        with AUDIT_REPORT_PATH.open(encoding="utf-8") as file:
            report = json.load(file)
        json.dumps(report, allow_nan=False)
        return report


if __name__ == "__main__":
    with (PROJECT_ROOT / "examples" / "prediction_request.json").open(encoding="utf-8") as file:
        payload = json.load(file)
    service = FairCreditService()
    for model in ("logistic_regression", "xgboost"):
        for policy in (ROLLBACK_POLICY_VERSION, POLICY_VERSION):
            for lang in ("en", "ta"):
                result = service.score_applicant(payload, lang, model_name=model, policy_version=policy)
                assert result["model_name"] == model
                assert result["policy_version"] == policy
                assert result["shap_explanation"]["model_name"] == model
                assert result["shap_explanation"]["language"] == lang
                assert result["simulation_only"] and result["human_review_required"]
                print(f"PASS: Scoring {model} / {policy} / {lang}")
            result = service.simulate_applicant(payload, {"income_cv": 0.20}, model_name=model, policy_version=policy)
            for key in ("original_prediction", "simulated_prediction"):
                assert result[key]["model_name"] == model
                assert result[key]["policy_version"] == policy
                assert result[key]["simulation_only"] and result[key]["human_review_required"]
            print(f"PASS: Simulation {model} / {policy}")
    assert service.score_applicant(payload)["policy_version"] == ROLLBACK_POLICY_VERSION
    print("PASS: Default rollback policy")
    report = service.get_fairness_audit()
    assert {"validation", "test"}.issubset(report["cohorts"])
    print("PASS: Fairness policy comparison report")
    print("All scoring service tests completed.")