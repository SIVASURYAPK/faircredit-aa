import pandas as pd
import numpy as np

def build_single_applicant_data():
    # 1. Create an 8-month date window
    dates = pd.date_range(start="2023-01-01", end="2023-08-31", freq="D")
    
    # 2. Craft fake daily inflows (INR) with multiple payments on some days
    np.random.seed(42)
    
    # Generate some base daily inflows
    inflows = np.where(
        np.random.rand(len(dates)) > 0.7, 
        np.random.randint(500, 2500, size=len(dates)), 
        0
    )
    
    # 3. Build the DataFrame
    df = pd.DataFrame({
        "applicant_id": "APP-001",
        "date": dates,
        "inflow_amount": inflows
    })
    
    # Intentionally add duplicate dates to simulate multiple payments in one day
    extra_payments = df[df['inflow_amount'] > 0].sample(15, random_state=1)
    df = pd.concat([df, extra_payments]).sort_values('date').reset_index(drop=True)
    
    return df

def build_first_three_features(df):
    # Setup
    total_days = (df['date'].max() - df['date'].min()).days + 1
    inflows_only = df[df['inflow_amount'] > 0]
    
    # --- Feature 1: avg_monthly_inflow ---
    # Group by month and sum, then find the mean of those monthly totals
    monthly_totals = df.set_index('date')['inflow_amount'].resample('ME').sum()
    avg_monthly_inflow = monthly_totals.mean()
    
    # --- Feature 2: income_cv (Coefficient of Variation) ---
    # Standard deviation of monthly totals divided by the mean
    if avg_monthly_inflow == 0:
        income_cv = None # Null rule for income_cv
    else:
        income_cv = monthly_totals.std() / avg_monthly_inflow
        
    # --- Feature 3: active_day_ratio ---
    # Count unique days with income, divided by total days in window
    unique_active_days = inflows_only['date'].nunique()
    active_day_ratio = unique_active_days / total_days
    
    # Return as a dictionary
    return {
        "applicant_id": "APP-001",
        "avg_monthly_inflow": avg_monthly_inflow,
        "income_cv": income_cv,
        "active_day_ratio": active_day_ratio
    }

if __name__ == "__main__":
    raw_data = build_single_applicant_data()
    features = build_first_three_features(raw_data)
    
    print("--- Calculated Features ---")
    for key, value in features.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
            
    # Verify the active_day_ratio isn't above 1
    assert features["active_day_ratio"] <= 1.0, "Error: active_day_ratio is greater than 1!"
    print("\nCheck passed: active_day_ratio is valid.")