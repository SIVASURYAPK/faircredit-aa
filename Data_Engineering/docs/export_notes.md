# Export Notes — features.csv and protected_attrs.csv

These notes apply to whoever runs the feature pipeline and exports files
for model training. The validator (`tests/validate_dataset.py`) enforces
most of these rules automatically.

---

## File layout

### `data/features.csv`
One row per applicant. Contains:

```
applicant_id | <19 feature columns> | TARGET
```

**Null handling:** leave nulls as blank cells (empty string in CSV).  
**Never** fill a null with `0` — a zero income and a missing income are different signals.

The 19 required feature columns (in any order):

| Column | Notes |
|---|---|
| `avg_monthly_income` | Mean monthly inflow; must be ≥ 0 |
| `income_volatility` | Coefficient of variation; range [0, 1] |
| `income_trend_ratio` | **Null when previous 3-month average is 0** (see rule below) |
| `zero_income_days_pct` | Fraction of days with no inflow; range [0, 1] |
| `num_income_sources` | Distinct source_id count |
| `months_observed` | History length; must be **6–12** (integer) |
| `obligation_to_income_ratio` | Total obligations / income |
| `rent_to_income_ratio` | Rent / income |
| `emi_coverage_ratio` | Income / EMI |
| `bill_payment_rate` | Fraction of bills paid on time; range [0, 1] |
| `avg_days_late` | Mean days between due_date and paid_date |
| `missed_bill_count` | Count of unpaid bills |
| `avg_daily_balance` | Mean of balance_snapshots |
| `min_balance_30d` | Minimum balance in last 30 days |
| `overdraft_count` | Count of overdraft events |
| `overdraft_days_pct` | Overdraft days / total days; range [0, 1] |
| `savings_ratio` | (Income − Obligations) / Income |
| `shock_occurred` | Binary 0/1 |
| `shock_severity` | **Null when shock_occurred = 0**; range [0, 1] when non-null |

---

### `data/protected_attrs.csv`
Separate file — **never** merge these columns into `features.csv`.

```
applicant_id | gender | region | age_band
```

The validator explicitly blocks any of:
`gender`, `caste`, `religion`, `age`, `age_group`, `age_band`,
`region`, `pin_code`, `latitude`, `longitude`
from appearing inside `features.csv`.

---

## Fix 2 — Label rename (IMPORTANT)

Our raw `labels.csv` uses the column name `default`.  
The validator expects `TARGET`.

**When exporting, rename the column:**

```python
labels = labels.rename(columns={"default": "TARGET"})
```

Then merge with the features DataFrame before writing `features.csv`:

```python
features_df = features_df.merge(labels[["applicant_id", "TARGET"]], on="applicant_id")
features_df.to_csv("data/features.csv", index=False)
```

---

## Running the validator

```bash
python tests/validate_dataset.py data/features.csv
```

Aim for:
```
Status: PASSED  (0 warning(s))
```

---

## Two rules the validator cannot check (our unit tests must cover these)

1. **`shock_severity` nullability:**  
   `shock_severity` must be `null` (not `0`) when no shock event exists for the applicant.  
   A `0` severity implies a shock occurred with zero impact, which is a different meaning.

2. **`income_trend_ratio` nullability:**  
   `income_trend_ratio` must be `null` when the previous 3-month average income is `0`.  
   Dividing by zero would produce `inf`; we store `null` instead.

Add these as explicit assertions in `tests/test_raw_data.py` once the feature pipeline exists.
