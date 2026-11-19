"""
generator/protected_extra.py
============================
Reads data/raw/protected_attributes.csv and adds 4 protected demographic/geographic columns:
  1. urban_rural: "urban" (45%), "semi_urban" (25%), "rural" (30%)
  2. shg_member: "yes" / "no" (gender-dependent: female ~0.25, male ~0.04, non_binary ~0.10)
  3. language: region-dependent with ~5% English across all regions
  4. pin_code: 6-digit string based on region prefix (north: 1 or 2, west: 3 or 4,
     south: 5 or 6, east: 7 or 8, northeast: 78 or 79)

Randomness:
  Uses its own generator np.random.default_rng(SEED + 10) (SEED from generator.config)
  and does not use or advance any other RNG. Output is strictly reproducible.

Outputs:
  - data/raw/protected_attributes.csv
  - data/credit.db (table: protected_attributes)
  - data/protected_attrs.csv
"""

import os
import shutil
import sqlite3
import numpy as np
import pandas as pd

from generator import config


URBAN_RURAL_CATEGORIES = ["urban", "semi_urban", "rural"]
URBAN_RURAL_PROBS = [0.45, 0.25, 0.30]

SHG_PROBS = {
    "female": 0.25,
    "male": 0.04,
    "non_binary": 0.10,
}

REGION_LANGUAGES = {
    "north": (["Hindi", "Punjabi", "English"], [0.80, 0.15, 0.05]),
    "west": (["Marathi", "Gujarati", "Hindi", "English"], [0.40, 0.35, 0.20, 0.05]),
    "south": (["Tamil", "Telugu", "Kannada", "Malayalam", "English"], [0.35, 0.30, 0.20, 0.10, 0.05]),
    "east": (["Bengali", "Odia", "Hindi", "English"], [0.55, 0.25, 0.15, 0.05]),
    "northeast": (["Assamese", "Bengali", "Hindi", "English"], [0.50, 0.30, 0.15, 0.05]),
}

REGION_PIN_PREFIX = {
    "north": (["1", "2"], 5),
    "west": (["3", "4"], 5),
    "south": (["5", "6"], 5),
    "east": (["7", "8"], 5),
    "northeast": (["78", "79"], 4),
}


def add_protected_attributes(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Add urban_rural, shg_member, language, and pin_code to existing protected attributes.
    Preserves original columns and row order.
    """
    df = df.copy()

    # Pre-normalize language probabilities so each region's probabilities sum strictly to 1
    normalized_langs = {}
    for reg, (langs, probs) in REGION_LANGUAGES.items():
        p = np.array(probs, dtype=float)
        p = p / p.sum()
        normalized_langs[reg] = (langs, p)

    urban_rural_list = []
    shg_member_list = []
    language_list = []
    pin_code_list = []

    for row in df.itertuples(index=False):
        # 1. urban_rural
        ur = rng.choice(URBAN_RURAL_CATEGORIES, p=URBAN_RURAL_PROBS)
        urban_rural_list.append(str(ur))

        # 2. shg_member (yes/no)
        p_yes = SHG_PROBS.get(row.gender, 0.04)
        shg = "yes" if rng.random() < p_yes else "no"
        shg_member_list.append(shg)

        # 3. language
        langs, p_langs = normalized_langs[row.region]
        lang = rng.choice(langs, p=p_langs)
        language_list.append(str(lang))

        # 4. pin_code (6-digit string)
        prefixes, rem_len = REGION_PIN_PREFIX[row.region]
        prefix = rng.choice(prefixes)
        rem_digits = f"{rng.integers(0, 10**rem_len):0{rem_len}d}"
        pin = f"{prefix}{rem_digits}"
        pin_code_list.append(str(pin))

    df["urban_rural"] = urban_rural_list
    df["shg_member"] = shg_member_list
    df["language"] = language_list
    df["pin_code"] = pin_code_list

    return df


def run_extra_generator(
    raw_csv_path: str = "data/raw/protected_attributes.csv",
    db_path: str = "data/credit.db",
    dest_csv_path: str = "data/protected_attrs.csv",
) -> pd.DataFrame:
    """
    Main execution pipeline for Step 1.
    """
    seed = getattr(config, "RANDOM_SEED", getattr(config, "SEED", 42))
    rng = np.random.default_rng(seed + 10)

    # Read original protected attributes as string types
    df = pd.read_csv(raw_csv_path, dtype=str)
    print(f"Loaded {raw_csv_path} with shape {df.shape}")

    # Generate additional columns
    df_augmented = add_protected_attributes(df, rng)

    # 1. Write back to data/raw/protected_attributes.csv
    df_augmented.to_csv(raw_csv_path, index=False)
    print(f"Saved augmented data to {raw_csv_path} (shape: {df_augmented.shape})")

    # 2. Update protected_attributes table in data/credit.db (replace only this table)
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        df_augmented.to_sql("protected_attributes", conn, if_exists="replace", index=False)
        conn.close()
        print(f"Updated 'protected_attributes' table in {db_path}")

    # 3. Copy to data/protected_attrs.csv
    shutil.copyfile(raw_csv_path, dest_csv_path)
    print(f"Copied to {dest_csv_path}")

    return df_augmented


if __name__ == "__main__":
    run_extra_generator()
