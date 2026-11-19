"""
generator/traits.py
====================
draw_traits(applicant_id, rng) → dict

Draws ONE applicant's random traits from the distributions
defined in config.py. This is intentionally separate from
person.py so you can:
  - Inspect / override traits for debugging.
  - Swap in different trait distributions without touching generation logic.

Protected attributes (gender, region, age_band) are drawn INSIDE
person.py, NOT here, to make it obvious they play no role in trait
generation (which drives income, spending, and the label).
"""

import numpy as np
from generator import config


def draw_traits(applicant_id: str, rng: np.random.Generator) -> dict:
    """
    Draw a random set of traits for one applicant.

    Parameters
    ----------
    applicant_id : str   — used only for context; not stored in traits dict.
    rng          : np.random.Generator — seeded generator for reproducibility.

    Returns
    -------
    dict with keys matching the traits expected by generate_person().
    """

    # --- Segment -----------------------------------------------------------
    # choice() picks one item; p= sets the probability weights.
    segment = str(rng.choice(config.SEGMENTS, p=config.SEGMENT_WEIGHTS))

    # --- Base income (lognormal) -------------------------------------------
    # lognormal(mu, sigma) always returns a positive number, which is
    # appropriate for income.  Different mu/sigma per segment.
    if segment == "gig":
        base_income = float(rng.lognormal(
            mean=config.GIG_INCOME_MU,
            sigma=config.GIG_INCOME_SIGMA,
        ))
    else:
        base_income = float(rng.lognormal(
            mean=config.MSME_INCOME_MU,
            sigma=config.MSME_INCOME_SIGMA,
        ))

    # --- Volatility (uniform) ---------------------------------------------
    # How much income swings month-to-month.
    volatility = float(rng.uniform(config.VOLATILITY_LOW, config.VOLATILITY_HIGH))

    # --- Reliability (Beta distribution) ----------------------------------
    # Beta(5, 2) is skewed toward 1 (most people are reasonably reliable).
    # This creates a realistic minority of high-risk applicants.
    reliability = float(rng.beta(config.RELIABILITY_ALPHA, config.RELIABILITY_BETA))

    # --- History length (months) ------------------------------------------
    # integers(low, high) draws from [low, high) — so +1 to include high.
    months = int(rng.integers(config.MONTHS_LOW, config.MONTHS_HIGH + 1))

    # --- Number of income sources -----------------------------------------
    n_income_sources = int(rng.integers(
        config.N_INCOME_SOURCES_LOW,
        config.N_INCOME_SOURCES_HIGH + 1,
    ))

    # --- Boolean flags (Bernoulli trials) ---------------------------------
    # rng.random() returns a float in [0, 1); compare to threshold.
    has_bill_history = bool(rng.random() < config.P_HAS_BILL_HISTORY)
    has_shock        = bool(rng.random() < config.P_HAS_SHOCK)

    return {
        "segment":          segment,
        "base_income":      round(base_income, 2),
        "volatility":       round(volatility, 4),
        "reliability":      round(reliability, 4),
        "months":           months,
        "n_income_sources": n_income_sources,
        "has_bill_history": has_bill_history,
        "has_shock":        has_shock,
    }
