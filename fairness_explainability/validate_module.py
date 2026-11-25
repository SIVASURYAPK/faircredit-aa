"""Regression checks for the simulation-only Member 4 integration."""
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
from pydantic import ValidationError
from src.config import FEATURE_COLUMNS, ROLLBACK_POLICY_VERSION, POLICY_VERSION
from src.schema import CreditRequest
from src.predictor import predict_credit
from fairness_explainability.scoring_service import FairCreditService
from fairness_explainability.fairness_audit import calculate_binary_fairness

ROOT = Path(__file__).resolve().parents[1]
MODELS = ('logistic_regression', 'xgboost')
POLICIES = (ROLLBACK_POLICY_VERSION, POLICY_VERSION)
ATTRS = ('gender', 'region', 'age_band', 'urban_rural')


def strict_json(value):
    json.dumps(value, allow_nan=False)


def main():
    payload = json.loads((ROOT / 'examples/prediction_request.json').read_text(encoding='utf-8'))
    service = FairCreditService()
    original = copy.deepcopy(payload)
    for model in MODELS:
        predictions = []
        for policy in POLICIES:
            expected = predict_credit(payload, model_name=model, policy_version=policy)
            en = service.score_applicant(payload, 'en', model_name=model, policy_version=policy)
            ta = service.score_applicant(payload, 'ta', model_name=model, policy_version=policy)
            for result in (en, ta):
                for key, value in expected.items():
                    assert result[key] == value, key
                assert result['human_review_required'] and result['simulation_only']
                assert result['fairness_and_risk_approval_required']
                exp = result['shap_explanation']
                assert exp['model_name'] == model
                np.testing.assert_allclose(exp['base_value'] + sum(exp['transformed_feature_contributions'].values()), exp['raw_margin'], atol=1e-5, rtol=0)
                strict_json(result)
            assert en['shap_explanation']['language'] == 'en'
            assert ta['shap_explanation']['language'] == 'ta'
            assert en['shap_explanation']['transformed_feature_contributions'] == ta['shap_explanation']['transformed_feature_contributions']
            assert any(a['label'] != b['label'] for a,b in zip(en['shap_explanation']['shap_reason_codes'], ta['shap_explanation']['shap_reason_codes']))
            changes = {'income_cv': 0.20}
            sim = service.simulate_applicant(payload, changes, model_name=model, policy_version=policy)
            modified = copy.deepcopy(payload)
            modified['features'].update(changes)
            direct = predict_credit(modified, model_name=model, policy_version=policy)
            for key in ('model_name','policy_version','pred_prob','score','decision','suggested_limit','human_review_required','simulation_only'):
                assert sim['original_prediction'][key] == expected[key], key
                assert sim['simulated_prediction'][key] == direct[key], key
            strict_json(sim)
            predictions.append(en)
            print(f'PASS: {model} / {policy}: scoring, bilingual SHAP, simulation and JSON')
        assert predictions[0]['pred_prob'] == predictions[1]['pred_prob']
        assert predictions[0]['score'] == predictions[1]['score']
        assert predictions[0]['shap_explanation']['transformed_feature_contributions'] == predictions[1]['shap_explanation']['transformed_feature_contributions']
        print(f'PASS: {model}: policy-independent model outputs')
    assert payload == original
    assert service.score_applicant(payload)['policy_version'] == ROLLBACK_POLICY_VERSION
    print('PASS: Rollback default and unchanged input')
    protected = pd.read_csv(ROOT / 'data/raw/protected_attrs.csv', dtype={'pin_code': str})
    columns = set(protected.columns) - {'applicant_id'}
    assert not columns.intersection(FEATURE_COLUMNS)
    assert not columns.intersection(payload['features'])
    for attribute in columns:
        for nested in (False, True):
            invalid = copy.deepcopy(payload)
            (invalid['features'] if nested else invalid)[attribute] = 'test'
            try:
                CreditRequest.model_validate(invalid)
            except ValidationError:
                pass
            else:
                raise AssertionError(f'Protected field accepted: {attribute}')
    print('PASS: Protected fields excluded from feature list and rejected by request schema')
    # Controlled fixture: 100 per group, 50 per target class.
    df = pd.DataFrame({'group': ['A']*100 + ['B']*100, 'TARGET': ([0]*50+[1]*50)*2})
    df['selected'] = ([1]*40+[0]*10+[1]*10+[0]*40)*2
    clean = calculate_binary_fairness(df, 'group', 'selected')
    assert clean['disparate_impact_ratio'] == 1.0
    assert clean['equalized_odds_difference'] == 0.0
    assert clean['review_status'] == 'WITHIN_EXPLORATORY_THRESHOLDS'
    df.loc[df['group']=='B', 'selected'] = 0
    biased = calculate_binary_fairness(df, 'group', 'selected')
    assert biased['disparate_impact_ratio'] == 0.0
    assert biased['equalized_odds_difference'] >= 0.79
    assert biased['review_status'] == 'REVIEW_NEEDED'
    df['selected'] = 0
    empty = calculate_binary_fairness(df, 'group', 'selected')
    assert empty['disparate_impact_ratio'] is None
    assert empty['review_status'] == 'INSUFFICIENT_EVIDENCE'
    print('PASS: Controlled parity, injected disparity and zero-approval detection')
    report = service.get_fairness_audit()
    strict_json(report)
    assert report['simulation_only'] and report['fairness_and_risk_approval_required']
    assert report['policy_status'] == 'experimental'
    for cohort in ('validation','test'):
        c = report['cohorts'][cohort]
        assert c['sample_count'] == 750
        for model in MODELS:
            old, new = [c['policies'][p]['models'][model] for p in POLICIES]
            for result in (old,new):
                counts = result['overall_results']
                assert sum(counts[k] for k in ('approval_count','review_count','decline_count')) == c['sample_count']
                assert set(ATTRS).issubset(result['policy_fairness'])
                for attr in ATTRS:
                    assert sum(g['sample_count'] for g in result['policy_fairness'][attr]['group_metrics'].values()) == c['sample_count']
            assert old['overall_results']['decline_count'] == new['overall_results']['decline_count']
            assert old['overall_results']['approval_count'] == 0
            assert all(old['policy_fairness'][a]['review_status']=='INSUFFICIENT_EVIDENCE' for a in ATTRS)
    print('PASS: Fairness report counts, group coverage and experimental safeguards')
    print('ALL MEMBER 4 VALIDATION TESTS PASSED')
    print('Technical validation only; fairness and risk approval remain pending.')


if __name__ == '__main__':
    main()
