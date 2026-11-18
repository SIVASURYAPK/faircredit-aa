import pandas as pd
from features.build_features import build_features

# 1. Load the list of all 5,000 applicants
applicants = pd.read_csv("data/raw/applicants.csv")

# 2. Loop through each person and compute their features
all_features = []
print("Starting feature pipeline...")

for index, row in applicants.iterrows():
    app_id = row['applicant_id']
    as_of = row['as_of_date']
    
    # Run the Antigravity function for this one person
    person_features = build_features(applicant_id=app_id, as_of_date=as_of, db_path="data/credit.db")
    all_features.append(person_features)
    
    # Print progress so you know it isn't frozen
    if (index + 1) % 500 == 0:
        print(f"Processed {index + 1} / 5000...")

# 3. Combine everyone into one massive DataFrame and save
final_df = pd.DataFrame(all_features)
final_df.to_csv("data/features.csv", index=False)
print("Success! All 5,000 features saved to data/features.csv")