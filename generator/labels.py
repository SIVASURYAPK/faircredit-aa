"""
generator/labels.py
====================
compute_label(traits, shock_severity, rng) → int (0 or 1)

WHY THIS DESIGN (data-leakage prevention)
------------------------------------------
The default label must NOT be derived from:
  - Any single observable feature (e.g. "missed 3 bills → default").
    That would encode the answer into the training data, so a model
    could trivially learn it and fail on real data.
  - Protected attributes (gender, region, age_band).
    That would encode demographic bias directly into the target variable.

Instead we derive default from HIDDEN traits (reliability, volatility,
shock_severity) — things the model must *infer* from raw transactions,
not read off a column.  Random noise is added so the relationship is
probabilistic, not deterministic, matching real-world credit risk.
"""

import numpy as np
from generator import config


def _sigmoid(x: float) -> float:
    """
    Standard sigmoid / logistic function.
    Maps any real number to a probability in (0, 1).
    sigmoid(0) = 0.5, sigmoid(-3) ≈ 0.05, sigmoid(+3) ≈ 0.95.
    """
    return 1.0 / (1.0 + np.exp(-x))


def compute_label(
    traits: dict,
    shock_severity: float,
    rng: np.random.Generator,
) -> int:
    """
    Compute a binary default label (1 = default, 0 = no default).

    Parameters
    ----------
    traits         : dict from draw_traits() — contains reliability, volatility.
    shock_severity : float, 0 if no shock; the shock's severity (0.4–0.9) if one occurred.
    rng            : seeded generator for reproducible noise.

    Returns
    -------
    1 if predicted to default, 0 otherwise.
    """
    reliability = traits["reliability"]   # 0–1, hidden, higher = safer
    volatility  = traits["volatility"]    # 0.1–0.8, hidden, higher = riskier

    # Build the log-odds (logit) of default using hidden traits only.
    # Weights come from config.py so they're easy to tune.
    logit = (
        config.LABEL_INTERCEPT                          # baseline (keeps rate ~10%)
        + config.LABEL_W_RELIABILITY * reliability      # negative: reliable → safe
        + config.LABEL_W_VOLATILITY  * volatility       # positive: volatile → risky
        + config.LABEL_W_SHOCK       * shock_severity   # positive: shocked → risky
        + rng.normal(0, config.LABEL_NOISE_SIGMA)       # random noise
    )

    # Convert log-odds to probability, then draw 0/1
    prob_default = _sigmoid(logit)
    return int(rng.random() < prob_default)


def build_labels_table(
    all_traits: list[dict],           # one dict per applicant
    shock_severities: dict,           # applicant_id → shock severity (0 if none)
    applicant_ids: list[str],
    rng: np.random.Generator,
) -> "pd.DataFrame":                  # type hint as string to avoid circular import
    """
    Build the labels DataFrame for ALL applicants.

    Parameters
    ----------
    all_traits       : list of trait dicts, one per applicant.
    shock_severities : dict mapping applicant_id → shock severity.
    applicant_ids    : list of applicant ID strings (same order as all_traits).
    rng              : seeded generator.

    Returns
    -------
    pd.DataFrame with columns: applicant_id, default
    """
    import pandas as pd

    rows = []
    for aid, traits in zip(applicant_ids, all_traits):
        severity = shock_severities.get(aid, 0.0)
        label    = compute_label(traits, severity, rng)
        rows.append({"applicant_id": aid, "default": label})

    df = pd.DataFrame(rows)

    # Print the default rate for a quick sanity check during generation
    rate = df["default"].mean() * 100
    print(f"  → Default rate: {rate:.1f}%  (target: ~10%)")

    return df
