"""
generator/config.py
===================
Single source of truth for all constants used across the generator.
If you want to change N, seed, income ranges, or seasonal patterns,
this is the ONLY file you need to edit.
"""

# ---------------------------------------------------------------------------
# Run parameters
# ---------------------------------------------------------------------------

N_APPLICANTS = 5000      # total synthetic applicants to generate
RANDOM_SEED  = 42        # fixed seed → fully reproducible dataset
AS_OF_DATE   = "2024-11-01"   # cutoff date (string; parsed in run_generator.py)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------

DB_PATH  = "data/credit.db"
CSV_DIR  = "data/raw"

# ---------------------------------------------------------------------------
# Segment mix
# ---------------------------------------------------------------------------

SEGMENTS        = ["gig", "msme"]
SEGMENT_WEIGHTS = [0.65, 0.35]   # 65 % gig workers, 35 % MSMEs

# ---------------------------------------------------------------------------
# Income ranges (monthly INR)
# These are log-space parameters: lognormal(mu, sigma)
# mean of lognormal = exp(mu + sigma²/2)
# ---------------------------------------------------------------------------

# Gig workers: roughly ₹8k – ₹35k/month
GIG_INCOME_MU    = 9.7    # exp(9.7) ≈ ₹16 300
GIG_INCOME_SIGMA = 0.5

# MSMEs: roughly ₹20k – ₹1.2L/month
MSME_INCOME_MU    = 10.9   # exp(10.9) ≈ ₹54 000
MSME_INCOME_SIGMA = 0.6

# ---------------------------------------------------------------------------
# Trait ranges
# ---------------------------------------------------------------------------

VOLATILITY_LOW  = 0.1
VOLATILITY_HIGH = 0.8

# reliability ~ Beta(5, 2) → skewed toward higher reliability
# (most people try to pay their bills; default is the minority)
RELIABILITY_ALPHA = 5
RELIABILITY_BETA  = 2

MONTHS_LOW  = 6
MONTHS_HIGH = 12

N_INCOME_SOURCES_LOW  = 1
N_INCOME_SOURCES_HIGH = 4

# Probability that an applicant has bill history / a shock event
P_HAS_BILL_HISTORY = 0.90   # 90 % of applicants have some bill records
P_HAS_SHOCK        = 0.20   # 20 % experienced a qualifying income shock

# ---------------------------------------------------------------------------
# Seasonal index (applied as a daily income multiplier)
# Month 1 = January … Month 12 = December
# ---------------------------------------------------------------------------

SEASONAL_INDEX = {
    1:  1.05,   # January  — post-festival, moderate
    2:  1.00,   # February — quiet
    3:  1.05,   # March    — financial year-end busy
    4:  0.95,   # April    — summer starts
    5:  0.90,   # May      — peak summer
    6:  0.85,   # June     — monsoon begins
    7:  0.82,   # July     — heavy monsoon
    8:  0.85,   # August   — late monsoon
    9:  0.95,   # September — pre-festival recovery
    10: 1.20,   # October  — Navratri / Dussehra / Diwali
    11: 1.15,   # November — Diwali tail
    12: 1.05,   # December — Christmas / year-end
}

# ---------------------------------------------------------------------------
# Default label (Step E)
# ---------------------------------------------------------------------------

# Logistic function weights for P(default):
#   logit = w_rel * reliability + w_vol * volatility + w_shock * shock_exposure + noise
# Intercept is tuned to hit ~10 % default rate.
LABEL_INTERCEPT       = -0.8
LABEL_W_RELIABILITY   = -3.5   # higher reliability → less likely to default
LABEL_W_VOLATILITY    =  2.0   # higher volatility  → more likely to default
LABEL_W_SHOCK         =  1.5   # shock exposure (severity or 0)
LABEL_NOISE_SIGMA     =  0.5   # logistic noise for unpredictability
