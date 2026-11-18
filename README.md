# Faircredit — Synthetic Data Generator

Alternate-data credit scoring for Indian gig workers and MSMEs.  
No public dataset has the right features, so we **generate synthetic raw records**
(dated transactions), then a separate pipeline computes features from them.

## Project layout

```
generator/   – synthetic data generation (this module)
features/    – feature pipeline (computed later)
api/         – FastAPI serving layer (later)
tests/       – pytest suite
data/raw/    – generated CSVs (git-ignored)
data/        – credit.db SQLite database (git-ignored)
docs/        – design notes
```

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# macOS / Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate data for 5000 applicants
python -m generator.run

# 4. Run tests
pytest tests/ -v
```

## Design decisions

- Raw records only — the feature pipeline is intentionally separate.
- Protected attributes (gender, region, age_band) are stored in their own table
  and are **never** used in income generation or labelling to avoid built-in bias.
- Default label is derived from hidden traits (reliability, volatility, shock
  exposure) + noise — not from any single observable feature.
