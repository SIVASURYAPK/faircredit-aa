# Data Dictionary

> Auto-generated stub — describes every raw table and column in `data/credit.db`.

## Table: `applicants`
One row per applicant. This is the master identity table.

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | Unique ID, e.g. `APP_00042` |
| `segment` | TEXT | `"gig"` or `"msme"` |
| `as_of_date` | DATE | Cutoff date — no data exists after this date |

---

## Table: `protected_attributes`
Demographic and geographic data stored in isolation. **Never used** in feature computation or label derivation.

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `gender` | TEXT | `male`, `female`, `non_binary` |
| `region` | TEXT | `north`, `south`, `east`, `west`, `northeast` |
| `age_band` | TEXT | `18-25`, `26-35`, `36-45`, `46-55`, `55+` |
| `urban_rural` | TEXT | Geographic classification: `urban`, `semi_urban`, `rural` |
| `shg_member` | TEXT | Self-Help Group membership: `yes`, `no` |
| `language` | TEXT | Primary language spoken |
| `pin_code` | TEXT | 6-digit postal code string |

> **Fairness note:** These columns are audited post-training for disparate impact. They must not appear in any other table and are blocked from the feature set.

### Extended Demographic & Geographic Attributes Specification

> **Disclaimer:** All distributions, conditional probabilities, and demographic parameters detailed below are **synthetic assumptions for simulation purposes only**, not real empirical statistics or census data.

1. **`urban_rural`**: Independent distribution across all applicants.
   - `urban`: 45%
   - `semi_urban`: 25%
   - `rural`: 30%

2. **`shg_member`** (`yes` / `no`): Self-Help Group membership, conditioned on `gender`.
   - `female`: P(yes) = 25%
   - `male`: P(yes) = 4%
   - `non_binary`: P(yes) = 10%

3. **`language`**: Primary language spoken, conditioned on `region` with an English share (~5%) across all regions (probabilities normalized to sum to 1.0):
   - `north`: Hindi (80%), Punjabi (15%), English (5%)
   - `west`: Marathi (40%), Gujarati (35%), Hindi (20%), English (5%)
   - `south`: Tamil (35%), Telugu (30%), Kannada (20%), Malayalam (10%), English (5%)
   - `east`: Bengali (55%), Odia (25%), Hindi (15%), English (5%)
   - `northeast`: Assamese (50%), Bengali (30%), Hindi (15%), English (5%)

4. **`pin_code`**: A 6-digit string (stored strictly as text/string to preserve leading digits). Prefix determined by `region`, remaining digits drawn uniformly at random:
   - `north`: Starts with `1` or `2` (5 remaining random digits)
   - `west`: Starts with `3` or `4` (5 remaining random digits)
   - `south`: Starts with `5` or `6` (5 remaining random digits)
   - `east`: Starts with `7` or `8` (5 remaining random digits)
   - `northeast`: Starts with `78` or `79` (4 remaining random digits)

---

## Table: `inflow_transactions`
Daily income records. Zero-income days are absent (not stored as 0).

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `date` | DATE | Calendar date of income |
| `amount_inr` | REAL | Gross inflow in Indian Rupees (always ≥ 0) |
| `source_id` | TEXT | Income source tag, e.g. `src_1`, `src_2` |

> Missing = NULL (no row). Never store 0 for a no-income day.

---

## Table: `obligations`
Fixed monthly commitments (rent, EMI, utilities, etc.).

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `month` | TEXT | `YYYY-MM` format, e.g. `2024-06` |
| `type` | TEXT | `rent`, `utilities`, `subscription`, `insurance`, `emi` |
| `amount_inr` | REAL | Obligation amount that month |

---

## Table: `bills`
Actual bill payment events linked to obligations.

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `due_date` | DATE | When the bill was due |
| `paid_date` | DATE | When actually paid; **NULL if unpaid** |
| `amount_inr` | REAL | Bill amount in INR |

> `paid_date IS NULL` = missed payment. `paid_date > due_date` = late payment.

---

## Table: `balance_snapshots`
End-of-day running balance.

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `date` | DATE | Calendar date |
| `balance_inr` | REAL | Estimated account balance at end of day (INR) |

---

## Table: `overdraft_events`
Days where the computed balance went below zero.

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `date` | DATE | Date of overdraft |

---

## Table: `shock_events`
Income shock periods (flood, illness, lockdown, etc.).

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `start_date` | DATE | First day of shock |
| `end_date` | DATE | Last day of shock |
| `severity` | REAL | 0–1; fraction of income lost (≥ 0.4 = qualifying shock) |

> A qualifying shock = income ≥ 40% below baseline for ≥ 14 days.

---

## Table: `labels`
Training-only default labels. **Not available at inference time.**

| Column | Type | Description |
|---|---|---|
| `applicant_id` | TEXT | FK → applicants |
| `default` | INTEGER | `1` = defaulted within window, `0` = did not |

> Derived from hidden traits (reliability, volatility, shock severity) + random noise.  
> Target default rate: ~10%. Acceptable range for tests: 8–15%.

---

## Realism Rules Summary

| Rule | Detail |
|---|---|
| Seasonal income | Festival highs (Oct–Nov), monsoon lows (Jun–Aug) |
| Zero-income days | Driven by volatility × (1 − reliability); gig workers more than MSMEs |
| Bill punctuality | Reliable people (reliability > 0.7) pay on time or 1–2 days late |
| Shock events | 20% of applicants; income dips ≥ 40% for 14–30 days, then recovers |
| Groups overlap | Reliability drawn from Beta(5,2) → smooth spectrum, not two clusters |
| No future data | All dates ≤ as_of_date per applicant |
| INR amounts | Always ≥ 0; missing = NULL row, never 0-filled |
