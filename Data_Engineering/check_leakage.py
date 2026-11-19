import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# 1. Load labels and bills
labels = pd.read_csv('data/raw/labels.csv')
bills = pd.read_csv('data/raw/bills.csv')

# 2. Create a simple aggregate feature: count of missed bills per person
# A bill is missed if paid_date is null
missed_bills = bills[bills['paid_date'].isnull()].groupby('applicant_id').size().reset_index(name='missed_count')

# 3. Merge with labels
df = labels.merge(missed_bills, on='applicant_id', how='left').fillna(0)

# 4. Train a quick Logistic Regression
X = df[['missed_count']]
y = df['default']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

# 5. Check AUC
predictions = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, predictions)

print(f"Leakage Check AUC: {auc:.3f}")