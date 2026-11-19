import pandas as pd
import numpy as np

# Load the final dataset
df = pd.read_csv("data/features.csv")

# 1. Check the shape (Should be exactly 5000 rows and 21 columns: 19 features + id + date)
print(f"Dataset Shape: {df.shape}")

# 2. Check for unexpected infinite values (usually caused by division by zero)
numeric_cols = df.select_dtypes(include=np.number)
inf_counts = np.isinf(numeric_cols).sum()
print("\nInfinite Values Found:")
print(inf_counts[inf_counts > 0])

# 3. Check the null counts to ensure they match your expected rules
print("\nNull Values per Feature:")
print(df.isna().sum())