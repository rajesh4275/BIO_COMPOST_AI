import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

def train_rf():
    df = pd.read_csv('data/processed/compost_data.csv')

    # Features and Target
    X = df[['pH', 'Temperature', 'Humidity', 'Moisture', 'N', 'P', 'K']]
    y = df['Semantic_Tag'] # This acts as our "Waste Type"

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and Train
    rf = RandomForestClassifier(n_estimators=100)
    rf.fit(X_train, y_train)

    # Save the model
    joblib.dump(rf, 'models/rf_classifier.pkl')
    print("Random Forest model saved to models/rf_classifier.pkl")

if __name__ == "__main__":
    train_rf()