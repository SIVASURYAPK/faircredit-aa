"""
features/build_features.py
===========================
Feature pipeline: computes engineered features for ONE applicant
from raw tables in the SQLite database.

Current state:
  Task 1 — data loading
  Task 2 — basic averages (months_observed, source_count, avg/median inflow)
  Task 3 — obligation ratios (obligation_to_inflow_ratio, emi_to_inflow_ratio)
  Task 4 — bill behaviour (bills_due_count_6m, missed_count, avg_days_late, on_time_rate)
  Task 5 — balances & overdrafts (overdraft_event_count_6m, balance_buffer_months)
  Task 6 — volatility & trends (active_day_ratio, longest_zero_income_gap_days, income_cv, income_trend_ratio)
  Task 7 — shock & seasonality (shock_severity, recovery_time_days, seasonality_adjusted_income)
All 19 features complete.

Usage:
    from features.build_features import build_features
    result = build_features("APP_00001", date(2024, 11, 1), "data/credit.db")
"""

import sqlite3
from datetime import date

import numpy as np       # added for Task 3: np.nan for safe null handling
import pandas as pd


# =============================================================================
# TASK 1 — DATA LOADING
# =============================================================================
# We load only the rows for this one applicant.
# Using a parameterised query (the ? placeholder) is safer than
# string-formatting the applicant_id directly into the SQL — it
# prevents SQL injection and handles special characters cleanly.

def _load_inflows(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load all inflow_transactions rows for this applicant.

    Returns a DataFrame with columns:
        date        — transaction date (we'll convert to datetime below)
        amount_inr  — INR amount of that day's inflow
        source_id   — which income source (e.g. "src_1", "src_2")
    """
    query = """
        SELECT date, amount_inr, source_id
        FROM   inflow_transactions
        WHERE  applicant_id = ?
        ORDER  BY date          -- sorted ascending so earliest is first
    """
    # pd.read_sql runs the SQL and returns a DataFrame straight away.
    # params=(applicant_id,) is a tuple that fills the ? placeholder.
    df = pd.read_sql(query, conn, params=(applicant_id,))

    # SQLite stores dates as strings ("2024-06-15").
    # pd.to_datetime converts them to proper datetime objects so we can
    # do date arithmetic (subtraction, grouping by month, etc.)
    df["date"] = pd.to_datetime(df["date"])

    return df


def _load_bills(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load all bills rows for this applicant.

    Returns a DataFrame with columns:
        due_date   — when the bill was due
        paid_date  — when paid (NaT / null if still unpaid)
        amount_inr — bill amount in INR
    """
    query = """
        SELECT due_date, paid_date, amount_inr
        FROM   bills
        WHERE  applicant_id = ?
        ORDER  BY due_date
    """
    df = pd.read_sql(query, conn, params=(applicant_id,))

    # Convert both date columns; errors="coerce" turns unparseable values
    # (including SQL NULLs) into NaT ("Not a Time") instead of crashing.
    df["due_date"]  = pd.to_datetime(df["due_date"],  errors="coerce")
    df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# Task 1 loader: obligations
# ---------------------------------------------------------------------------
# NOTE — two column names differ from the spec your teammate shared:
#   spec said "obligation_type"  → actual DB column is "type"
#   spec said "amount"           → actual DB column is "amount_inr"
#   spec said type value 'EMI'   → actual DB stores it as lowercase 'emi'
# Always verify against the real schema before trusting any spec.

def _load_obligations(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load all obligations rows for this applicant.

    Returns a DataFrame with columns:
        month      — billing month string "YYYY-MM" (e.g. "2024-06")
        type       — obligation category: 'rent','utilities','subscription',
                     'insurance','emi'  (all lowercase in our DB)
        amount_inr — INR amount for that month's obligation
    """
    query = """
        SELECT month, type, amount_inr
        FROM   obligations
        WHERE  applicant_id = ?
        ORDER  BY month
    """
    # Same pattern as the other loaders: parameterised query → DataFrame
    df = pd.read_sql(query, conn, params=(applicant_id,))
    return df


# ---------------------------------------------------------------------------
# Task 1 loaders: balance_snapshots and overdraft_events  (added for Task 5)
# ---------------------------------------------------------------------------
# NOTE — spec said column "end_of_day_balance"; actual DB column is "balance_inr".

def _load_balance_snapshots(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load daily end-of-day balance rows for this applicant.

    Returns a DataFrame with columns:
        date        — calendar date (string; we convert to datetime below)
        balance_inr — account balance at end of that day (INR)
    """
    query = """
        SELECT date, balance_inr
        FROM   balance_snapshots
        WHERE  applicant_id = ?
        ORDER  BY date
    """
    df = pd.read_sql(query, conn, params=(applicant_id,))
    df["date"] = pd.to_datetime(df["date"])   # string → datetime for future date ops
    return df


def _load_overdraft_events(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load overdraft event rows for this applicant.

    Each row = one day where the balance went below zero.
    We only need the count, so we select just the date column.

    Returns a DataFrame with columns:
        date — the overdraft date
    """
    query = """
        SELECT date
        FROM   overdraft_events
        WHERE  applicant_id = ?
    """
    df = pd.read_sql(query, conn, params=(applicant_id,))
    return df


# ---------------------------------------------------------------------------
# Task 1 loader: shock_events  (added for Task 7)
# ---------------------------------------------------------------------------
# NOTE — In the SQLite database, the shock dates are stored as:
#   start_date (first day of shock) and end_date (last day of shock).
# We query start_date as shock_date so it matches the expected interface.

def _load_shock_events(applicant_id: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load shock event rows for this applicant.

    Returns a DataFrame with columns:
        shock_date — when the shock started (datetime)
        end_date   — when the shock ended (datetime)
        severity   — float fraction of income drop (0.4 to 0.9)
    """
    query = """
        SELECT start_date AS shock_date, end_date, severity
        FROM   shock_events
        WHERE  applicant_id = ?
        ORDER  BY start_date
    """
    df = pd.read_sql(query, conn, params=(applicant_id,))
    df["shock_date"] = pd.to_datetime(df["shock_date"])
    df["end_date"]   = pd.to_datetime(df["end_date"])
    return df


# =============================================================================
# TASK 2 — BASIC AVERAGES (first 4 features)
# =============================================================================

def _compute_basic_features(
    inflows: pd.DataFrame,
    as_of_date: date,
    window_start: pd.Timestamp | date | None = None,
) -> dict:
    """
    Compute the first 4 features from the inflow_transactions data.

    Parameters
    ----------
    inflows     : DataFrame from _load_inflows()
    as_of_date  : the cutoff date for this applicant

    Returns
    -------
    dict with keys: months_observed, income_source_count,
                    avg_monthly_inflow, median_monthly_inflow
    """

    # --- Guard: no inflow data at all ---
    # If the person has zero rows, all 4 features are None (null).
    # We use None here; pandas will write it as NaN in the DataFrame,
    # which becomes NULL in SQLite and blank in the CSV. Never use 0.
    if inflows.empty:
        return {
            "months_observed":      None,
            "income_source_count":  None,
            "avg_monthly_inflow":   None,
            "median_monthly_inflow": None,
        }

    # ------------------------------------------------------------------
    # Feature 1: months_observed
    # ------------------------------------------------------------------
    # Spec definition: "months with usable financial observations" (integer 6 to 12).
    #
    # The generator creates observation windows in 30-day blocks:
    #   window_start = as_of_date - 30 * months (where months is an integer in [6, 12]).
    #
    # Previously, months_observed was computed as (as_of_date - earliest_inflow) / 30.
    # Because an applicant's first inflow may occur a few days into their window
    # due to zero-income days (e.g. up to 5 days later), this produced fractional
    # values like 5.83 or 7.90.
    #
    # Rule: Compute the calendar day span from the window start (if available, e.g. from
    # balance_snapshots) or earliest transaction date to as_of_date, divide by 30, and round
    # to the nearest integer. Cast explicitly to int.
    as_of_ts = pd.Timestamp(as_of_date)
    if window_start is not None:
        start_ts = pd.Timestamp(window_start)
    else:
        start_ts = inflows["date"].min()

    total_days = (as_of_ts - start_ts).days
    months_observed = int(round(total_days / 30))

    # ------------------------------------------------------------------
    # Feature 2: income_source_count
    # ------------------------------------------------------------------
    # Rule: unique count of source_id values in the inflow data.
    #
    # .nunique() = "number of unique values" — equivalent to len(set(...))
    # A person with Uber + food delivery + freelance has source_count = 3.

    income_source_count = int(inflows["source_id"].nunique())
    # ------------------------------------------------------------------
    # Features 3 & 4: avg_monthly_inflow, median_monthly_inflow
    # ------------------------------------------------------------------
    # Rule: aggregate inflows to monthly totals first, THEN take mean/median.
    # This is important: we want the average month's income,
    # not the average single transaction (which would weight busy days too much).
    #
    # Step A — Set the date column as the DataFrame's index.
    #   resample() needs a datetime index to group by time periods.
    #   We don't modify the original; we work on a copy.
    #
    # Step B — resample("ME") groups rows by calendar month-end.
    #   "ME" = Month End frequency. Every row whose date falls in
    #   the same calendar month gets grouped together.
    #   Other common codes: "W" = week, "QE" = quarter, "YE" = year.
    #
    # Step C — .sum() adds up all amount_inr values within each month group.
    #   Result: one row per month, one column (amount_inr = that month's total inflow).
    #
    # Step D — .mean() / .median() across those monthly totals.

    # Step A: copy and set index
    inflows_indexed = inflows.set_index("date")     # date becomes the row label

    # Step B + C: group by month and sum
    monthly_totals = (
        inflows_indexed["amount_inr"]               # select just the amount column
        .resample("ME")                             # group by calendar month-end
        .sum()                                      # total inflow per month
    )
    # monthly_totals is now a Series like:
    #   2024-02-29    15230.5
    #   2024-03-31    18450.2
    #   ...

    # Step D: mean and median across months
    avg_monthly_inflow    = round(float(monthly_totals.mean()),   2)
    median_monthly_inflow = round(float(monthly_totals.median()), 2)

    return {
        "months_observed":       months_observed,
        "income_source_count":   income_source_count,
        "avg_monthly_inflow":    avg_monthly_inflow,
        "median_monthly_inflow": median_monthly_inflow,
    }


# =============================================================================
# TASK 3 — OBLIGATION RATIOS
# =============================================================================
# Two features that compare what a person OWES each month to what they EARN.
# A high ratio = most of their income is already committed → higher risk.
#
# New pandas ideas used here:
#   .groupby("type")["amount_inr"].sum()
#       — groups rows by their 'type' value, then sums amount_inr within each group
#       — result is a Series indexed by type name: {"rent": 45000, "emi": 18000, ...}
#   .get("emi", 0.0)
#       — safely fetches a value from that Series by label; returns 0.0 if the
#         label doesn't exist (some applicants have no EMI row at all)

def _compute_ratio_features(
    obligations: pd.DataFrame,
    avg_monthly_inflow: float,
) -> dict:
    """
    Compute obligation-to-inflow ratios.

    Parameters
    ----------
    obligations        : DataFrame from _load_obligations()
    avg_monthly_inflow : float from _compute_basic_features()
                         (may be np.nan if inflow data was missing)

    Returns
    -------
    dict with keys: obligation_to_inflow_ratio, emi_to_inflow_ratio
    """

    # ------------------------------------------------------------------
    # Null guard: if avg_monthly_inflow is 0 or NaN, dividing would
    # produce inf or raise an error. Rule: set both ratios to np.nan.
    #
    # pd.isna() returns True for both float('nan') and np.nan.
    # We check both conditions with 'or' to be explicit.
    # ------------------------------------------------------------------
    if avg_monthly_inflow is None or pd.isna(avg_monthly_inflow) or avg_monthly_inflow == 0:
        return {
            "obligation_to_inflow_ratio": np.nan,
            "emi_to_inflow_ratio":        np.nan,
        }

    # ------------------------------------------------------------------
    # Feature 5: obligation_to_inflow_ratio
    # ------------------------------------------------------------------
    # = Sum of ALL obligation amounts (across all types and all months)
    #   divided by avg_monthly_inflow.
    #
    # But obligations has one row per (month, type).
    # We want a single average monthly total to compare against avg_monthly_inflow.
    #
    # Strategy:
    #   Step A — sum all amounts per month (collapse all types within a month)
    #   Step B — take the mean of those monthly totals
    #   Step C — divide by avg_monthly_inflow
    #
    # Step A: group by 'month', sum all obligation amounts within each month.
    # obligations.groupby("month")["amount_inr"].sum() gives:
    #   2024-05    11564.24
    #   2024-06    10893.17
    #   ...  (one number per month = total obligations that month)

    monthly_obligation_totals = (
        obligations
        .groupby("month")["amount_inr"]   # for each month, look at amount_inr
        .sum()                             # add up all types (rent + emi + utilities...)
    )

    # Step B: average across months (comparable to avg_monthly_inflow)
    avg_monthly_obligations = monthly_obligation_totals.mean()

    # Step C: ratio — round to 4 decimal places for readability
    obligation_to_inflow_ratio = round(avg_monthly_obligations / avg_monthly_inflow, 4)

    # ------------------------------------------------------------------
    # Feature 6: emi_to_inflow_ratio
    # ------------------------------------------------------------------
    # Same idea, but only the 'emi' obligation type.
    #
    # Step A — filter to only 'emi' rows, then group by month and sum.
    #   obligations["type"] == "emi"  → a boolean mask (True/False per row)
    #   obligations[mask]             → only the rows where type is 'emi'
    #
    # Some applicants have NO emi rows at all — the filtered DataFrame
    # will be empty, and .mean() on an empty Series returns NaN.
    # We handle that explicitly below.

    emi_rows = obligations[obligations["type"] == "emi"]   # filter to EMI rows only

    if emi_rows.empty:
        # This applicant has no EMI — ratio is null, not 0
        # (0 would imply we confirmed EMI=0; null means "no EMI data")
        emi_to_inflow_ratio = np.nan
    else:
        # Group the emi rows by month, sum within each month, then average
        avg_monthly_emi    = emi_rows.groupby("month")["amount_inr"].sum().mean()
        emi_to_inflow_ratio = round(avg_monthly_emi / avg_monthly_inflow, 4)

    return {
        "obligation_to_inflow_ratio": obligation_to_inflow_ratio,
        "emi_to_inflow_ratio":        emi_to_inflow_ratio,
    }


# =============================================================================
# TASK 4 — BILL BEHAVIOUR
# =============================================================================
# Four features that describe HOW reliably an applicant pays their bills.
# This is a strong real-world signal: someone who consistently pays on time
# is a very different credit risk from someone who misses bills repeatedly.
#
# The bills DataFrame already has parsed datetime columns from _load_bills().
# That means we can subtract two date columns directly — pandas handles it.
#
# New pandas ideas used here:
#
#   df["paid_date"].isna()
#       — returns a boolean Series: True where paid_date is NaT (null/missed)
#       — .sum() on a boolean Series counts the Trues (like counting Trues in a list)
#
#   (df["paid_date"] - df["due_date"]).dt.days
#       — subtracts two datetime columns element-by-element → timedelta per row
#       — .dt.days extracts just the integer number of days from each timedelta
#       — positive = paid after due (late), negative = paid before due (early)
#
#   boolean mask filtering:
#       late_mask = (df["days_late"] > 0)   # True for each late-paid row
#       df[late_mask]                        # keep only those rows

def _compute_bill_features(
    bills: pd.DataFrame,
    as_of_date: date | None = None,
) -> dict:
    """
    Compute bill-behaviour features from the bills DataFrame for the 6 months ending at as_of_date.

    Parameters
    ----------
    bills      : DataFrame from _load_bills() — columns: due_date, paid_date, amount_inr
                 due_date and paid_date are already datetime (or NaT for null paid_date)
    as_of_date : date | None — cutoff date. If provided, filters to bills due in the 6 months
                 ending at as_of_date.

    Returns
    -------
    dict with keys:
        bills_due_count_6m       — total bills due in the 6 months ending at as_of_date
        missed_payment_count_6m  — bills with no paid_date (null)
        avg_days_late            — average delay in days across PAID bills (on-time counts as 0 delay)
        on_time_bill_rate        — fraction of bills paid on or before due_date
    """

    # ------------------------------------------------------------------
    # Step A — Empty DataFrame guard
    # ------------------------------------------------------------------
    if bills.empty:
        return {
            "bills_due_count_6m":      0,
            "missed_payment_count_6m": np.nan,
            "avg_days_late":           np.nan,
            "on_time_bill_rate":       np.nan,
        }

    # ------------------------------------------------------------------
    # Step B — Filter to the 6 months ending at as_of_date (if provided)
    # ------------------------------------------------------------------
    if as_of_date is not None:
        as_of_ts = pd.Timestamp(as_of_date)
        window_start_ts = as_of_ts - pd.DateOffset(months=6)
        bills = bills[
            (bills["due_date"] >= window_start_ts) & (bills["due_date"] <= as_of_ts)
        ].copy()

    # ------------------------------------------------------------------
    # Feature 7: bills_due_count_6m
    # ------------------------------------------------------------------
    bills_due_count = len(bills)

    # ------------------------------------------------------------------
    # Null guard: if there is no bill history in the 6-month window,
    # return np.nan for all three derived features. bills_due_count is 0.
    # ------------------------------------------------------------------
    if bills_due_count == 0:
        return {
            "bills_due_count_6m":      0,
            "missed_payment_count_6m": np.nan,
            "avg_days_late":           np.nan,
            "on_time_bill_rate":       np.nan,
        }

    # ------------------------------------------------------------------
    # Feature 8: missed_payment_count_6m
    # ------------------------------------------------------------------
    # A missed bill = paid_date is null (NaT in pandas).
    missed_count = int(bills["paid_date"].isna().sum())

    # ------------------------------------------------------------------
    # Paid bills analysis
    # ------------------------------------------------------------------
    paid_bills = bills[bills["paid_date"].notna()].copy()

    if paid_bills.empty:
        avg_days_late = np.nan
        on_time_bill_rate = 0.0
    else:
        # ------------------------------------------------------------------
        # Feature 9: avg_days_late
        # ------------------------------------------------------------------
        # Average delay across all PAID bills.
        # On-time payments (paid on or before due date) count as 0 delay.
        paid_bills["delay"] = (
            paid_bills["paid_date"] - paid_bills["due_date"]
        ).dt.days.clip(lower=0)

        avg_days_late = round(float(paid_bills["delay"].mean()), 2)

        # ------------------------------------------------------------------
        # Feature 10: on_time_bill_rate
        # ------------------------------------------------------------------
        # On-time = paid AND paid_date <= due_date (delay == 0).
        # Missed bills are in the denominator but not numerator.
        on_time_count = int((paid_bills["delay"] == 0).sum())
        on_time_bill_rate = round(on_time_count / bills_due_count, 4)

    return {
        "bills_due_count_6m":      bills_due_count,
        "missed_payment_count_6m": missed_count,
        "avg_days_late":           avg_days_late,
        "on_time_bill_rate":       on_time_bill_rate,
    }


# =============================================================================
# TASK 5 — BALANCES & OVERDRAFTS
# =============================================================================
# Two features that describe the applicant's cash cushion and stress moments.
#
#   overdraft_event_count_6m
#       — how many times did their balance go negative? Even one overdraft
#         is a warning sign; ten is a serious red flag.
#
#   balance_buffer_months
#       — if they stopped earning tomorrow, how many months of fixed costs
#         could they cover from their average balance?
#         = avg_daily_balance / avg_monthly_obligations
#         A value of 0.5 means they could only last half a month.
#         A value of 3.0 means they have a solid 3-month cushion.
#
# New pandas ideas used here:
#
#   len(df)
#       — the simplest possible thing: just count rows.
#         For overdraft_events, one row = one overdraft day, so len = count.
#
#   df["balance_inr"].mean()
#       — the mean of a numeric column across all rows.
#         balance_snapshots has one row per calendar day, so this gives
#         the average daily balance over the whole observation window.
#
#   obligations["amount_inr"].sum() vs groupby().sum().mean()
#       — "total sum" in the spec would give a number that grows with
#         history length (more months → bigger sum → smaller ratio),
#         making the feature incomparable across applicants with different
#         window lengths. We use avg_monthly_obligations instead, so the
#         ratio is always "months of coverage" regardless of window length.

def _compute_balance_features(
    balance_snapshots: pd.DataFrame,
    overdraft_events:  pd.DataFrame,
    obligations:       pd.DataFrame,
    as_of_date:        date | None = None,
) -> dict:
    """
    Compute balance and overdraft features.

    Parameters
    ----------
    balance_snapshots : DataFrame from _load_balance_snapshots()
                        columns: date, balance_inr
    overdraft_events  : DataFrame from _load_overdraft_events()
                        columns: date
    obligations       : DataFrame from _load_obligations() — reused from Task 3,
                        columns: month, type, amount_inr

    Returns
    -------
    dict with keys: overdraft_event_count_6m, balance_buffer_months
    """

    # ------------------------------------------------------------------
    # Feature 11: overdraft_event_count_6m
    # ------------------------------------------------------------------
    # Count of distinct overdraft events within the 6 months ending at as_of_date.
    # If as_of_date is not provided (e.g. standalone test), counts total rows in overdraft_events.
    if overdraft_events.empty:
        overdraft_event_count_6m = 0
    elif as_of_date is not None:
        as_of_ts = pd.Timestamp(as_of_date)
        cutoff_6m = as_of_ts - pd.Timedelta(days=180)
        od_dates = pd.to_datetime(overdraft_events["date"])
        in_window = overdraft_events[(od_dates >= cutoff_6m) & (od_dates <= as_of_ts)]
        overdraft_event_count_6m = int(in_window["date"].nunique())
    else:
        overdraft_event_count_6m = len(overdraft_events)

    # ------------------------------------------------------------------
    # Feature 12: balance_buffer_months
    # ------------------------------------------------------------------
    # = avg daily balance / avg monthly obligations
    #
    # Step A — compute avg daily balance from balance_snapshots.
    #   Each row is one day's end-of-day balance.
    #   .mean() across all rows gives the typical balance level.

    if balance_snapshots.empty:
        # No balance data at all — we can't compute the buffer
        return {
            "overdraft_event_count_6m": overdraft_event_count_6m,
            "balance_buffer_months":    np.nan,
        }

    avg_daily_balance = float(balance_snapshots["balance_inr"].mean())

    # Step B — compute avg monthly obligations from the obligations table.
    #   We already have this loaded from Task 3; no second DB query needed.
    #
    #   obligations has one row per (month, type).
    #   groupby("month").sum() collapses all types within each month → one
    #   total per month. Then .mean() across months gives the average monthly
    #   obligation — the right denominator for a "months of coverage" ratio.
    #
    #   Why not obligations["amount_inr"].sum() directly?
    #   That raw total grows larger the more months of history we have,
    #   so a 12-month applicant would appear to have 2× the obligations of
    #   a 6-month applicant with identical monthly costs. Using the monthly
    #   average makes the feature comparable across all applicants.

    if obligations.empty:
        avg_monthly_obligations = 0.0
    else:
        avg_monthly_obligations = float(
            obligations
            .groupby("month")["amount_inr"]   # sum all types within each month
            .sum()
            .mean()                            # then average across months
        )

    # Null guard: if obligations are 0 or missing, the division is meaningless
    if pd.isna(avg_monthly_obligations) or avg_monthly_obligations == 0:
        balance_buffer_months = np.nan
    else:
        # Result: how many months of fixed costs does the avg balance cover?
        # e.g. avg_balance=30000, avg_monthly_obligations=10000 → 3.0 months
        balance_buffer_months = round(avg_daily_balance / avg_monthly_obligations, 4)

    return {
        "overdraft_event_count_6m": overdraft_event_count_6m,
        "balance_buffer_months":    balance_buffer_months,
    }


# =============================================================================
# TASK 6 — VOLATILITY & TRENDS
# =============================================================================
# Four features that capture how steady or unpredictable an applicant's income is,
# and whether their earnings are growing or deteriorating heading into evaluation.
#
#   active_day_ratio
#       — proportion of days where the person actually worked / earned.
#         A gig worker active on 80% of days is steadier than one active on 20%.
#
#   longest_zero_income_gap_days
#       — the largest stretch between consecutive earnings. A gap of 20+ days
#         signals a sudden disruption (e.g. sickness, vehicle breakdown).
#
#   income_cv (Coefficient of Variation)
#       — std(monthly_income) / mean(monthly_income).
#         Normalises volatility by scale: allows comparing volatility across
#         low-earners and high-earners equally.
#
#   income_trend_ratio
#       — (inflows in last 30 days) / (average monthly inflow in earlier months).
#         > 1.0 means recent income is growing; < 1.0 means declining.
#
# New pandas ideas used here:
#
#   df["date"].dt.normalize().nunique()
#       — .dt.normalize() resets timestamp times to midnight (pure dates)
#       — .nunique() counts distinct dates (ignores multiple transactions on the same day)
#
#   series.diff().dt.days
#       — .diff() computes the difference between each element and the previous element
#         (row[i] - row[i-1]). On datetimes, this gives a Timedelta series.
#       — .dt.days extracts the number of days as an integer.
#
#   series.std()
#       — sample standard deviation across monthly aggregated values.

def _compute_volatility_and_trends(
    inflows: pd.DataFrame,
    months_observed: float,
    as_of_date: date,
    window_start: pd.Timestamp | None = None,
) -> dict:
    """
    Compute volatility and income trend features from inflow_transactions.

    Parameters
    ----------
    inflows         : DataFrame from _load_inflows()
                      columns: date (datetime), amount_inr, source_id
    months_observed : float from _compute_basic_features()
    as_of_date      : cutoff date

    Returns
    -------
    dict with keys:
        active_day_ratio, longest_zero_income_gap_days,
        income_cv, income_trend_ratio
    """

    # --- Guard: no inflow records at all ---
    if inflows.empty:
        return {
            "active_day_ratio":             np.nan,
            "longest_zero_income_gap_days": np.nan,
            "income_cv":                     np.nan,
            "income_trend_ratio":           np.nan,
        }

    # ------------------------------------------------------------------
    # Feature 13: active_day_ratio
    # ------------------------------------------------------------------
    # Count of unique calendar days with ≥ 1 transaction / Total days observed.
    #
    # Denominator: actual number of calendar days in the observation window,
    # inclusive: (window_end - window_start).days + 1.
    # Uses the same window definition the generator uses:
    #   window_start = as_of_date - timedelta(days=30 * months)
    #   window_end   = as_of_date
    #
    # If window_start is not explicitly passed, we derive months as
    # int(round(months_observed)) (the 6-12 month trait) and subtract 30*months days.

    as_of_ts = pd.Timestamp(as_of_date)
    window_end = as_of_ts

    if window_start is None:
        if months_observed is not None and not pd.isna(months_observed) and months_observed > 0:
            obs_months = int(round(months_observed))
            window_start = window_end - pd.Timedelta(days=30 * obs_months)
        else:
            window_start = None

    if window_start is None:
        total_days = 0
    else:
        window_start = pd.Timestamp(window_start)
        total_days = (window_end - window_start).days + 1

    if total_days <= 0:
        active_day_ratio = np.nan
    else:
        # Count active days as DISTINCT dates with inflow inside that window
        inflow_dates = inflows["date"].dt.normalize()
        window_mask = (inflow_dates >= window_start) & (inflow_dates <= window_end)
        unique_active_days = int(inflow_dates[window_mask].nunique())
        active_day_ratio = round(float(unique_active_days / total_days), 4)

    # ------------------------------------------------------------------
    # Feature 14: longest_zero_income_gap_days
    # ------------------------------------------------------------------
    # Longest run of CONSECUTIVE calendar days inside the observation window
    # (window start through as_of_date, inclusive) on which the applicant had
    # no inflow at all (using distinct dates; multiple sources on one day count as earning).
    #
    # Zero-income days at the start and end of the window are counted as well.
    # If the applicant earned on every single day, the value is 0.
    # Rule: If fewer than 2 transactions, return np.nan.

    if len(inflows) < 2:
        longest_zero_income_gap_days = np.nan
    else:
        if window_start is not None:
            win_start_ts = pd.Timestamp(window_start).normalize()
            win_end_ts   = pd.Timestamp(as_of_date).normalize()
            all_window_days = pd.date_range(win_start_ts, win_end_ts, freq="D")
            earning_dates = set(inflows["date"].dt.normalize())

            max_gap = 0
            curr_gap = 0
            for d in all_window_days:
                if d in earning_dates:
                    if curr_gap > max_gap:
                        max_gap = curr_gap
                    curr_gap = 0
                else:
                    curr_gap += 1
            if curr_gap > max_gap:
                max_gap = curr_gap

            longest_zero_income_gap_days = int(max_gap)
        else:
            sorted_unique_dates = pd.Series(sorted(inflows["date"].dt.normalize().unique()))
            diffs = sorted_unique_dates.diff().dt.days - 1
            longest_zero_income_gap_days = int(max(0, diffs.dropna().max())) if not diffs.dropna().empty else 0

    # ------------------------------------------------------------------
    # Feature 15: income_cv (Coefficient of Variation)
    # ------------------------------------------------------------------
    # std(monthly_inflow_totals) / mean(monthly_inflow_totals)
    #
    # We aggregate inflows into calendar month totals first (resample("ME").sum()).
    # Null Rule: If mean is 0 or NaN, income_cv must explicitly be np.nan.

    inflows_indexed = inflows.set_index("date")
    monthly_totals = inflows_indexed["amount_inr"].resample("ME").sum()

    monthly_mean = float(monthly_totals.mean())

    if pd.isna(monthly_mean) or monthly_mean == 0:
        income_cv = np.nan
    else:
        monthly_std = float(monthly_totals.std())
        # If there's only 1 month of history, std() is NaN
        if pd.isna(monthly_std):
            income_cv = np.nan
        else:
            income_cv = round(monthly_std / monthly_mean, 4)

    # ------------------------------------------------------------------
    # Feature 16: income_trend_ratio
    # ------------------------------------------------------------------
    # (Inflows in most recent 30 days) / (Average monthly inflow of preceding months)
    #
    # Step A — Define the 30-day cutoff: as_of_ts - 30 days.
    # Step B — Sum inflows where (date > cutoff) and (date <= as_of_ts).
    # Step C — Take inflows where (date <= cutoff), group by month ("ME"),
    #          sum each month, and take the mean across those preceding months.
    # Null Rule: If preceding months average is 0 or NaN, set to np.nan.

    as_of_ts = pd.Timestamp(as_of_date)
    cutoff_30d = as_of_ts - pd.Timedelta(days=30)

    # Recent 30 days
    recent_mask = (inflows["date"] > cutoff_30d) & (inflows["date"] <= as_of_ts)
    recent_30d_sum = float(inflows.loc[recent_mask, "amount_inr"].sum())

    # Preceding period
    preceding_mask = inflows["date"] <= cutoff_30d
    preceding_inflows = inflows[preceding_mask]

    if preceding_inflows.empty:
        avg_preceding_monthly = np.nan
    else:
        preceding_monthly_totals = (
            preceding_inflows.set_index("date")["amount_inr"]
            .resample("ME")
            .sum()
        )
        avg_preceding_monthly = float(preceding_monthly_totals.mean())

    # Null Rule
    if pd.isna(avg_preceding_monthly) or avg_preceding_monthly == 0:
        income_trend_ratio = np.nan
    else:
        income_trend_ratio = round(recent_30d_sum / avg_preceding_monthly, 4)


    

    return {
        "active_day_ratio":             active_day_ratio,
        "longest_zero_income_gap_days": longest_zero_income_gap_days,
        "income_cv":                     income_cv,
        "income_trend_ratio":           income_trend_ratio,
    }


# =============================================================================
# TASK 7 — SHOCK EVENTS & SEASONALITY ADJUSTMENT
# =============================================================================
# Three features capturing external economic disruptions and baseline earning power:
#
#   shock_severity
#       — severity of income shock from shock_events (e.g. 0.65 = 65% drop).
#         Null rule: 0.0 if no shock event occurred.
#
#   recovery_time_days
#       — days from the shock_date until their 30-day rolling income returned
#         to their pre-shock baseline level.
#         Null rule: np.nan if no shock occurred or if not yet recovered.
#
#   seasonality_adjusted_income
#       — average monthly inflow excluding the single highest and single lowest
#         earning months (trims out festive spike and monsoon dip).
#         Null rule: equal to avg_monthly_inflow if fewer than 3 months of history.
#
# New pandas ideas used here:
#
#   daily.reindex(full_date_range, fill_value=0.0)
#       — expands sparse transaction dates to a continuous daily calendar index,
#         filling zero-income days with 0.0 so rolling(30) calculates genuine 30-day sums.
#
#   series.iloc[1:-1]
#       — position-based slicing: drops index 0 (lowest) and index -1 (highest)
#         after sort_values(), keeping only the middle months.

def _compute_shock_and_seasonality_features(
    shock_events:       pd.DataFrame,
    inflows:            pd.DataFrame,
    avg_monthly_inflow: float,
    as_of_date:         date,
) -> dict:
    """
    Compute shock severity, recovery time, and seasonality-adjusted income.

    Parameters
    ----------
    shock_events       : DataFrame from _load_shock_events()
                         columns: shock_date, end_date, severity
    inflows            : DataFrame from _load_inflows()
    avg_monthly_inflow : float from _compute_basic_features()
    as_of_date         : cutoff date
    """

    # ------------------------------------------------------------------
    # Feature 17 & 18: shock_severity and recovery_time_days
    # ------------------------------------------------------------------
    # Null Rule: If no shock rows, shock_severity MUST be 0.0,
    # and recovery_time_days MUST be np.nan.

    if shock_events.empty:
        shock_severity = 0.0
        recovery_time_days = np.nan
    else:
        shock_row = shock_events.iloc[0]
        shock_severity = float(shock_row["severity"])
        shock_date = shock_row["shock_date"]

        if inflows.empty:
            recovery_time_days = np.nan
        else:
            as_of_ts = pd.Timestamp(as_of_date)

            # Step A: Build continuous calendar daily series from earliest date to as_of_date
            daily = inflows.groupby("date")["amount_inr"].sum()
            full_idx = pd.date_range(start=inflows["date"].min(), end=as_of_ts, freq="D")
            daily_full = daily.reindex(full_idx, fill_value=0.0)

            # Step B: 30-day rolling income across the entire calendar history
            rolling_30d = daily_full.rolling(window=30, min_periods=1).sum()

            # Step C: Pre-shock average 30-day rolling income
            pre_shock = rolling_30d[rolling_30d.index < shock_date]

            if pre_shock.empty:
                recovery_time_days = np.nan
            else:
                pre_shock_avg = float(pre_shock.mean())

                # Step D: Track post-shock trajectory
                post_shock = rolling_30d[rolling_30d.index >= shock_date]
                dip_series = post_shock[post_shock < pre_shock_avg]

                if dip_series.empty:
                    # Income never fell below pre-shock baseline
                    recovery_time_days = np.nan
                else:
                    first_dip_date = dip_series.index[0]
                    # Find when rolling income returned to >= pre_shock_avg on or after the dip
                    recovered = post_shock[
                        (post_shock.index > first_dip_date) & (post_shock >= pre_shock_avg)
                    ]
                    if recovered.empty:
                        # Has not yet recovered to pre-shock level before as_of_date
                        recovery_time_days = np.nan
                    else:
                        recovered_date = recovered.index[0]
                        recovery_time_days = int((recovered_date - shock_date).days)

    # ------------------------------------------------------------------
    # Feature 19: seasonality_adjusted_income
    # ------------------------------------------------------------------
    # Exclude the single highest and single lowest earning calendar months.
    # Null rule: If fewer than 3 months of data, equals avg_monthly_inflow.

    if inflows.empty or pd.isna(avg_monthly_inflow):
        seasonality_adjusted_income = np.nan
    else:
        inflows_indexed = inflows.set_index("date")
        monthly_totals = inflows_indexed["amount_inr"].resample("ME").sum()

        if len(monthly_totals) < 3:
            seasonality_adjusted_income = avg_monthly_inflow
        else:
            # Sort monthly totals ascending
            sorted_months = monthly_totals.sort_values()
            # iloc[1:-1] slices off index 0 (lowest) and index -1 (highest)
            trimmed_months = sorted_months.iloc[1:-1]
            seasonality_adjusted_income = round(float(trimmed_months.mean()), 2)

    return {
        "shock_severity":              shock_severity,
        "recovery_time_days":          recovery_time_days,
        "seasonality_adjusted_income": seasonality_adjusted_income,
    }


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def build_features(
    applicant_id: str,
    as_of_date: date,
    db_path: str,
) -> dict:
    """
    Compute all 19 engineered features for one applicant.

    Parameters
    ----------
    applicant_id : str   — e.g. "APP_00001"
    as_of_date   : date  — cutoff; no data after this date should be used
    db_path      : str   — path to the SQLite database, e.g. "data/credit.db"

    Returns
    -------
    dict with keys: applicant_id, as_of_date, + all 19 computed features
    """

    conn = sqlite3.connect(db_path)

    try:
        # --- Task 1: load raw data ---
        inflows           = _load_inflows(applicant_id, conn)
        bills             = _load_bills(applicant_id, conn)
        obligations       = _load_obligations(applicant_id, conn)
        balance_snapshots = _load_balance_snapshots(applicant_id, conn)
        overdraft_events  = _load_overdraft_events(applicant_id, conn)
        shock_events      = _load_shock_events(applicant_id, conn)       # Task 7

        win_start = balance_snapshots["date"].min() if not balance_snapshots.empty else None

        # --- Task 2: basic averages (4 features) ---
        basic = _compute_basic_features(inflows, as_of_date, window_start=win_start)

        # --- Task 3: obligation ratios (2 features) ---
        ratios = _compute_ratio_features(obligations, basic["avg_monthly_inflow"])

        # --- Task 4: bill behaviour (4 features) ---
        bill_features = _compute_bill_features(bills, as_of_date=as_of_date)

        # --- Task 5: balances & overdrafts (2 features) ---
        balance_features = _compute_balance_features(
            balance_snapshots, overdraft_events, obligations, as_of_date=as_of_date
        )

        # --- Task 6: volatility & trends (4 features) ---
        win_start = balance_snapshots["date"].min() if not balance_snapshots.empty else None
        volatility_features = _compute_volatility_and_trends(
            inflows, basic["months_observed"], as_of_date, window_start=win_start
        )

        # --- Task 7: shock events & seasonality (3 features) ---
        shock_features = _compute_shock_and_seasonality_features(
            shock_events, inflows, basic["avg_monthly_inflow"], as_of_date
        )

    finally:
        conn.close()

    # Assemble final output dictionary with all 19 features
    result = {
        "applicant_id": applicant_id,
        "as_of_date":   str(as_of_date),
    }
    result.update(basic)                # 4 features
    result.update(ratios)               # 2 features
    result.update(bill_features)        # 4 features
    result.update(balance_features)     # 2 features
    result.update(volatility_features)  # 4 features
    result.update(shock_features)       # 3 features

    return result
