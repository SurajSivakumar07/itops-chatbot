import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
import pandas as pd

# Load dataset
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the CSV file
file_path = os.path.join(script_dir, "jira_issues.csv")

if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

df = pd.read_csv(file_path)
print("CSV Loaded Successfully!")

# Fill NaN values in text fields
df["Summary"] = df["Summary"].fillna("")
df["Description"] = df["Description"].fillna("")

# Convert text fields to numerical using TF-IDF
vectorizer = TfidfVectorizer()
X_text = vectorizer.fit_transform(df["Summary"] + " " + df["Description"])

# Encode categorical fields
encoder = LabelEncoder()
X_impact = encoder.fit_transform(df["Impact"].fillna("Unknown"))
X_urgency = encoder.fit_transform(df["Urgency"].fillna("Unknown"))
X_issuetype = encoder.fit_transform(df["Issue Type"].fillna("Unknown"))
X_priority = encoder.fit_transform(df["Priority"])  # Target variable

# Combine features
X = np.hstack((X_text.toarray(),
               X_impact.reshape(-1, 1),
               X_urgency.reshape(-1, 1),
               X_issuetype.reshape(-1, 1)))
y = X_priority

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate model
accuracy = model.score(X_test, y_test)
print(f"Model accuracy: {accuracy:.2f}")


# Function to predict priority for new issues
def predict_priority(new_issue_summary, new_issue_description="", impact="Unknown", urgency="Unknown",
                     issue_type="Unknown"):
    # Prepare text features
    text_combined = new_issue_summary + " " + new_issue_description
    text_vectorized = vectorizer.transform([text_combined]).toarray()

    # Prepare categorical features
    impact_encoded = encoder.transform([impact])[0] if impact in encoder.classes_ else 0
    urgency_encoded = encoder.transform([urgency])[0] if urgency in encoder.classes_ else 0
    issuetype_encoded = encoder.transform([issue_type])[0] if issue_type in encoder.classes_ else 0

    # Combine features
    features = np.hstack((text_vectorized,
                          [[impact_encoded]],
                          [[urgency_encoded]],
                          [[issuetype_encoded]]))

    # Make prediction
    prediction = model.predict(features)
    priority_label = encoder.inverse_transform(prediction)[0]

    return priority_label


 