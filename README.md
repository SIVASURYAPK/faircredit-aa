# faircredit-aa

Alternate-data credit scoring for gig workers and MSMEs in India: consent-based cash-flow signals, explainable scores, and a fairness audit.

## Structure
- `Data_Engineering/` : synthetic data generator, feature pipeline, validation scripts, backend API (in progress)
  - `generator/` : raw synthetic data (seeded, reproducible)
  - `features/` : builds the 19 model features from the raw tables
  - `tests/`, `docs/` : tests and data dictionary
- Other team members' modules (frontend, model, fairness) are added alongside.

## Data
Data files are not stored in Git (`Data_Engineering/data/` is git-ignored). All data is synthetic. `features_final_v1.csv` is the official features file and `protected_attrs.csv` holds the protected attributes. Both are shared separately.

## Reproduce (run from inside `Data_Engineering/`, seed 42)
1. `python -m generator.run_generator`
2. `python -m generator.protected_extra`
3. `python run_pipeline.py`
4. `python merge_target.py`
5. `python final_check.py`