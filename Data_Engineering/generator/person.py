"""
generator/person.py
====================
Core function: generate_person()

Generates raw synthetic records for ONE applicant.
Returns 8 pandas DataFrames (no features computed here).

Design principle
----------------
Protected attributes (gender, region, age_band) live ONLY in the
`protected_attributes` table. They play no role in income, bills,
or the default label — this prevents the model from learning a
proxy for a protected class.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta

# Import the single source of truth for constants
from generator.config import SEASONAL_INDEX

# ---------------------------------------------------------------------------
# 2. Helper: build date range
# ---------------------------------------------------------------------------

def _build_date_range(as_of_date: date, months: int) -> list[date]:
    """
    Return every calendar date from (as_of_date − months) to as_of_date.
    'months' is approximate: we subtract 30*months days for simplicity.
    """
    start = as_of_date - timedelta(days=30 * months)
    total_days = (as_of_date - start).days + 1          # +1 to include as_of_date
    return [start + timedelta(days=i) for i in range(total_days)]


# ---------------------------------------------------------------------------
# 3. Helper: generate daily inflows
# ---------------------------------------------------------------------------

def _generate_daily_inflows(
    applicant_id: str,
    traits: dict,
    all_dates: list[date],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Build inflow_transactions: one row per date that has income > 0.

    Key ideas
    ---------
    - Base daily income = monthly_base / 30, then scaled by seasonal index.
    - Lognormal noise: rng.lognormal(mean, sigma) always returns positive
      values, which is perfect for income — it can't go negative.
    - Zero-income days: drawn from a Bernoulli trial per day.
      Risky people (high volatility, low reliability) have more zero-income days.
    - Weekly pattern: Sunday is a rest day for many gig workers.
    - n_income_sources: some applicants have multiple income streams
      (e.g. Uber + food delivery), so we sum contributions from each source.
    - Shock events (handled later) suppress income for a period.
    """
    base_income   = traits["base_income"]          # monthly INR
    volatility    = traits["volatility"]            # 0.1 – 0.8
    reliability   = traits["reliability"]           # 0 – 1
    segment       = traits["segment"]
    n_sources     = traits["n_income_sources"]

    daily_base = base_income / 30.0                 # average daily income

    # Probability of earning anything on a given day.
    # Reliable people rarely have zero-income days; risky people often do.
    # Gig workers have more zero-income days than MSMEs overall.
    zero_day_prob = volatility * (1 - reliability) * (0.6 if segment == "gig" else 0.3)
    zero_day_prob = float(np.clip(zero_day_prob, 0.0, 0.7))  # cap at 70 %

    rows = []

    for d in all_dates:
        # Skip income on this day? (Bernoulli trial)
        if rng.random() < zero_day_prob:
            continue

        # Sunday rest day (more pronounced for gig workers)
        if d.weekday() == 6 and segment == "gig":        # 6 = Sunday in Python
            if rng.random() < 0.70:                      # 70 % chance of no work Sunday
                continue

        seasonal = SEASONAL_INDEX[d.month]               # seasonal multiplier

        # FIX: emit ONE ROW PER SOURCE (not one row per day).
        # The rng calls are identical to before — same number of uniform() and
        # lognormal() calls per earning day — so the rng sequence is preserved.
        # Bills, balances, and labels remain numerically unchanged.
        for source_idx in range(n_sources):
            # Each source contributes a fraction of daily_base
            source_weight = rng.uniform(0.5, 1.5)        # each source has its own scale
            # lognormal: mu=0 → median ≈ 1; sigma=volatility → spread
            noise = rng.lognormal(mean=0.0, sigma=volatility)
            contribution = (daily_base / n_sources) * source_weight * noise * seasonal

            # Clamp to zero (lognormal is always positive, but be safe)
            contribution = max(0.0, round(contribution, 2))

            # Append one row for this source on this day
            rows.append({
                "applicant_id": applicant_id,
                "date":         d,
                "amount_inr":   contribution,
                "source_id":    f"src_{source_idx + 1}",   # FIXED: unique per source
            })

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["applicant_id", "date", "amount_inr", "source_id"]
    )
    return df


# ---------------------------------------------------------------------------
# 4. Helper: generate monthly obligations
# ---------------------------------------------------------------------------

def _generate_obligations(
    applicant_id: str,
    traits: dict,
    all_dates: list[date],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    obligations: one row per (month, obligation type).

    Types: rent, utilities, subscription, insurance, emi
    MSMEs tend to have higher obligations (rent for shop, EMIs for equipment).
    Missing obligations are simply absent — no row, not a 0.
    """
    base_income = traits["base_income"]
    segment     = traits["segment"]

    # Identify which (year, month) pairs fall in the window
    months_in_window = sorted(set((d.year, d.month) for d in all_dates))

    # Obligation budgets as a fraction of monthly income
    obligation_fractions = {
        "rent":         rng.uniform(0.20, 0.40),   # 20–40 % of income
        "utilities":    rng.uniform(0.03, 0.08),
        "subscription": rng.uniform(0.01, 0.03),
        "insurance":    rng.uniform(0.02, 0.05) if rng.random() < 0.6 else None,
        "emi":          rng.uniform(0.10, 0.25) if (
                            segment == "msme" or rng.random() < 0.4
                        ) else None,
    }

    rows = []
    for (yr, mo) in months_in_window:
        # Month label string: "2024-06"
        month_label = f"{yr}-{mo:02d}"

        for ob_type, fraction in obligation_fractions.items():
            if fraction is None:                    # this person doesn't have this type
                continue
            # Small month-to-month variation (bills fluctuate slightly)
            monthly_variation = rng.uniform(0.9, 1.1)
            amount = round(base_income * fraction * monthly_variation, 2)
            rows.append({
                "applicant_id": applicant_id,
                "month":        month_label,
                "type":         ob_type,
                "amount_inr":   amount,
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Helper: generate bill payment events
# ---------------------------------------------------------------------------

def _generate_bills(
    applicant_id: str,
    traits: dict,
    obligations_df: pd.DataFrame,
    as_of_date: date,
    rng: np.random.Generator,
    bill_rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """
    bills: one row per billable obligation-month.

    Billable obligations are utilities, subscriptions, insurance, and EMIs (rent is excluded).
    This produces ~2 to 4 bills per month (12 to 24 bills in a 6-month window).

    Payment behaviour:
    - Reliability drives on-time payment probability: high-reliability pays on time
      ~85-98% of bills; low-reliability ~30-60%.
    - Late payments have a small delay (1 to 10 days).
    - A few bills are missed (paid_date = None).
    - Per-applicant noise ensures realistic overlap across reliability tiers.

    has_bill_history=False → return empty DataFrame (simulate no bill data).
    """
    # -----------------------------------------------------------------------
    # Step 1: Replay exact child_rng calls to keep downstream shock_events
    # and balance_snapshots identical.
    # -----------------------------------------------------------------------
    if traits.get("has_bill_history", True):
        orig_rel = traits["reliability"]
        for _, row in obligations_df.iterrows():
            yr, mo = int(row["month"][:4]), int(row["month"][5:7])
            due_day = rng.integers(1, 10)
            d_date = date(yr, mo, int(due_day))
            if d_date > as_of_date:
                continue
            missed_prob = max(0.0, (1 - orig_rel) * 0.3)
            if rng.random() < missed_prob:
                pass
            else:
                if orig_rel > 0.7:
                    _ = rng.integers(0, 3)
                elif orig_rel > 0.4:
                    _ = rng.integers(0, 8)
                else:
                    _ = rng.integers(2, 20)

    # -----------------------------------------------------------------------
    # Step 2: New bill generation using bill_rng (seed + 4 stream)
    # -----------------------------------------------------------------------
    if not traits.get("has_bill_history", True):
        return pd.DataFrame(
            columns=["applicant_id", "due_date", "paid_date", "amount_inr"]
        )

    if bill_rng is None:
        bill_rng = rng

    reliability = traits["reliability"]

    # Applicant-level noise gives realistic overlap across tiers
    app_noise = float(bill_rng.normal(0, 0.05))
    app_miss_noise = float(bill_rng.normal(0, 0.02))

    p_on_time = float(np.clip(0.32 + 0.60 * reliability + app_noise, 0.25, 0.98))
    p_miss = float(np.clip((1.0 - reliability) * 0.10 + app_miss_noise, 0.01, 0.15))

    # Rent is a tenancy payment, not a billed invoice. Billable types give 2–4 bills/mo.
    billable = obligations_df[
        obligations_df["type"].isin(["utilities", "subscription", "insurance", "emi"])
    ]

    rows = []
    for _, row in billable.iterrows():
        yr, mo = int(row["month"][:4]), int(row["month"][5:7])

        # Due dates in India typically fall between the 5th and 10th of the month
        due_day = int(bill_rng.integers(5, 11))
        due_date = date(yr, mo, due_day)

        if due_date > as_of_date:
            continue

        u = bill_rng.random()
        if u < p_miss:
            paid_date = None
        elif u < p_miss + p_on_time * (1.0 - p_miss):
            paid_date = due_date  # on time (0 delay)
        else:
            max_delay = int(round(10 - 5 * reliability))
            late_days = int(bill_rng.integers(1, max(2, max_delay + 1)))
            paid_date = due_date + timedelta(days=late_days)
            if paid_date > as_of_date:
                paid_date = None

        rows.append({
            "applicant_id": applicant_id,
            "due_date":     due_date,
            "paid_date":    paid_date,
            "amount_inr":   row["amount_inr"],
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. Helper: balance snapshots and overdraft events
# ---------------------------------------------------------------------------

def _generate_balance_and_overdrafts(
    applicant_id: str,
    traits: dict,
    inflow_df: pd.DataFrame,
    obligations_df: pd.DataFrame,
    all_dates: list[date],
    rng: np.random.Generator,
    overdraft_rng: np.random.Generator | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    balance_snapshots: running balance at end of each day.
    overdraft_events:  dates where balance went below zero.

    Logic
    -----
    - Start with an initial savings buffer (reliable people save more).
    - Each day: add inflows, subtract 1/30th of monthly obligations.
    - If balance < 0, record an overdraft event and clamp to 0
      (simulating bank coverage / borrowing from family).
    - Add a small daily random noise to simulate petty cash.
    """
    reliability = traits["reliability"]
    base_income = traits["base_income"]

    # Reliable people start with 1–3 months of savings; risky people near zero
    initial_buffer = base_income * rng.uniform(
        1.0 * reliability,          # low reliability → almost no buffer
        3.0 * reliability + 0.1,    # +0.1 so even reliability=0 gets a tiny buffer
    )
    balance = max(0.0, initial_buffer)

    # Daily obligation outflow (spread monthly obligations evenly)
    if obligations_df.empty:
        total_monthly_obligations = 0.0
    else:
        # Average obligations per month
        total_monthly_obligations = obligations_df.groupby("month")["amount_inr"].sum().mean()
    daily_outflow = total_monthly_obligations / 30.0

    # Build a lookup: date → total inflow amount (0 if no inflow that day).
    # FIX: use groupby().sum() instead of dict(zip(...)) because after the
    # source_id fix there are now MULTIPLE rows per date (one per source).
    # dict(zip()) would only keep the LAST row's amount — badly wrong.
    # groupby("date").sum() correctly adds all sources together per day.
    if inflow_df.empty:
        inflow_by_date = {}
    else:
        inflow_by_date = inflow_df.groupby("date")["amount_inr"].sum().to_dict()

    balance_rows   = []
    overdraft_rows = []

    for d in all_dates:
        inflow  = inflow_by_date.get(d, 0.0)
        balance += inflow
        balance -= daily_outflow

        # Small random petty-cash noise (±2 % of daily base)
        petty_noise = rng.normal(0, base_income * 0.002)
        balance += petty_noise

        balance_rows.append({
            "applicant_id": applicant_id,
            "date":         d,
            "balance_inr":  round(balance, 2),
        })

    # Overdraft events: generated from the daily balance trajectory using overdraft_rng.
    # An overdraft happens when the balance dips below a minimum operating safety threshold.
    # Risky applicants (low reliability, high volatility) experience more events, with
    # overlap across risk profiles. Uses a separate overdraft_rng so existing generation is undisturbed.
    if overdraft_rng is None:
        overdraft_rng = np.random.default_rng(45)

    bals = [r["balance_inr"] for r in balance_rows]
    min_b = min(bals) if bals else 0.0
    volatility = traits["volatility"]

    # Risk factor: higher for low reliability, high volatility
    noise = overdraft_rng.normal(0, 0.12)
    risk = (1.0 - reliability) * 1.6 + volatility * 0.3 - 0.25 + noise

    overdraft_rows = []
    if risk > 0 and bals:
        factor = 1.0 + risk * 0.4
        threshold = min_b * factor
        last_idx = -999
        event_count = 0
        for idx, r in enumerate(balance_rows):
            if r["balance_inr"] <= threshold:
                if idx - last_idx >= 14:
                    p = np.clip(
                        (0.6 * (1.0 - reliability) + 0.3 * volatility) * (0.6 ** event_count),
                        0.08, 0.8
                    )
                    if overdraft_rng.random() < p:
                        overdraft_rows.append({"applicant_id": applicant_id, "date": r["date"]})
                        last_idx = idx
                        event_count += 1

    balance_df   = pd.DataFrame(balance_rows)
    overdraft_df = pd.DataFrame(overdraft_rows) if overdraft_rows else pd.DataFrame(
        columns=["applicant_id", "date"]
    )
    return balance_df, overdraft_df


# ---------------------------------------------------------------------------
# 7. Helper: shock events
# ---------------------------------------------------------------------------

def _generate_shock_events(
    applicant_id: str,
    traits: dict,
    all_dates: list[date],
    inflow_df: pd.DataFrame,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Shock events: periods where income drops 40 %+ for 2+ weeks.
    Examples: flood, illness, equipment breakdown, lockdown.

    Returns
    -------
    - Updated inflow_df (income suppressed during shock)
    - shock_events DataFrame

    has_shock=False → return empty shock_events (no shock for this person).

    A "qualifying shock" means:
    - Duration ≥ 14 days
    - Severity: how far income drops (severity=1 → income falls to 0)
    - Recovery: income gradually returns post-shock
    """
    if not traits.get("has_shock", False):
        return inflow_df, pd.DataFrame(
            columns=["applicant_id", "start_date", "end_date", "severity"]
        )

    if len(all_dates) < 30:         # not enough history for a shock
        return inflow_df, pd.DataFrame(
            columns=["applicant_id", "start_date", "end_date", "severity"]
        )

    # Shock starts somewhere in the first 80 % of the window
    max_start_idx = int(len(all_dates) * 0.8)
    start_idx     = rng.integers(0, max_start_idx)

    # Duration: 14 to 30 days (always ≥ 14, so it's always a qualifying shock)
    duration  = int(rng.integers(14, 31))
    end_idx   = min(start_idx + duration, len(all_dates) - 1)

    # Severity: 0.4 to 0.9 (at least 40 % income drop, per spec)
    severity  = round(float(rng.uniform(0.4, 0.9)), 2)

    start_date = all_dates[start_idx]
    end_date   = all_dates[end_idx]

    shock_dates = set(all_dates[start_idx: end_idx + 1])

    # Recovery dates: 7 days after the shock — income gradually rebuilds
    recovery_dates = {}
    for i in range(1, 8):
        idx = end_idx + i
        if idx < len(all_dates):
            # Linear ramp back up over 7 days
            recovery_dates[all_dates[idx]] = 1 - (severity * (1 - i / 7.0))

    # Apply suppression to existing inflow rows
    new_rows = []
    for _, row in inflow_df.iterrows():
        d = row["date"] if isinstance(row["date"], date) else row["date"].date()
        if d in shock_dates:
            # Suppress by severity: amount * (1 - severity)
            suppressed = round(row["amount_inr"] * (1 - severity), 2)
            new_rows.append({**row.to_dict(), "amount_inr": suppressed})
        elif d in recovery_dates:
            # Partial recovery
            factor = recovery_dates[d]
            recovered = round(row["amount_inr"] * factor, 2)
            new_rows.append({**row.to_dict(), "amount_inr": recovered})
        else:
            new_rows.append(row.to_dict())

    updated_inflow = pd.DataFrame(new_rows) if new_rows else inflow_df

    shock_df = pd.DataFrame([{
        "applicant_id": applicant_id,
        "start_date":   start_date,
        "end_date":     end_date,
        "severity":     severity,
    }])

    return updated_inflow, shock_df


# ---------------------------------------------------------------------------
# 8. Main function: generate_person()
# ---------------------------------------------------------------------------

def generate_person(
    applicant_id: str,
    traits: dict,
    rng: np.random.Generator,
    as_of_date: date,
    overdraft_rng: np.random.Generator | None = None,
    bill_rng: np.random.Generator | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Generate all raw tables for a single applicant.

    Parameters
    ----------
    applicant_id : str
        Unique identifier, e.g. "APP_0001".
    traits : dict
        {
          "segment":          "gig" | "msme",
          "base_income":      float,   # monthly INR
          "volatility":       float,   # 0.1 – 0.8
          "reliability":      float,   # 0 – 1 (hidden)
          "months":           int,     # 6 – 12
          "n_income_sources": int,     # 1 – 4
          "has_bill_history": bool,
          "has_shock":        bool,
        }
    rng : np.random.Generator
        A seeded numpy random generator for reproducibility.
    as_of_date : date
        The cutoff date. No data is generated after this date.

    Returns
    -------
    dict of table_name → pd.DataFrame
    """

    months     = traits["months"]
    all_dates  = _build_date_range(as_of_date, months)

    # ----- Table 1: applicants ------------------------------------------
    applicants_df = pd.DataFrame([{
        "applicant_id": applicant_id,
        "segment":      traits["segment"],
        "as_of_date":   as_of_date,
    }])

    # ----- Table 2: protected_attributes --------------------------------
    # These are NEVER used in generation logic above.
    # They're only stored here so the model can be audited for fairness.
    genders      = ["male", "female", "non_binary"]
    regions      = ["north", "south", "east", "west", "northeast"]
    age_bands    = ["18-25", "26-35", "36-45", "46-55", "55+"]

    protected_df = pd.DataFrame([{
        "applicant_id": applicant_id,
        "gender":       rng.choice(genders),
        "region":       rng.choice(regions),
        "age_band":     rng.choice(age_bands),
    }])

    # ----- Table 3: inflow_transactions ---------------------------------
    inflow_df = _generate_daily_inflows(applicant_id, traits, all_dates, rng)

    # ----- Table 4: obligations -----------------------------------------
    obligations_df = _generate_obligations(applicant_id, traits, all_dates, rng)

    # ----- Table 5: bills -----------------------------------------------
    bills_df = _generate_bills(
        applicant_id, traits, obligations_df, as_of_date, rng, bill_rng=bill_rng
    )

    # ----- Table 7 (computed first): shock events -----------------------
    # We apply shock BEFORE computing balance, so balance reflects the dip.
    inflow_df, shock_df = _generate_shock_events(
        applicant_id, traits, all_dates, inflow_df, rng
    )

    # ----- Tables 6 & 8: balance snapshots + overdraft events -----------
    balance_df, overdraft_df = _generate_balance_and_overdrafts(
        applicant_id, traits, inflow_df, obligations_df, all_dates, rng,
        overdraft_rng=overdraft_rng,
    )

    return {
        "applicants":          applicants_df,
        "protected_attributes": protected_df,
        "inflow_transactions": inflow_df,
        "obligations":         obligations_df,
        "bills":               bills_df,
        "balance_snapshots":   balance_df,
        "overdraft_events":    overdraft_df,
        "shock_events":        shock_df,
    }
