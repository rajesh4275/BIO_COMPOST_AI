import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib

def train_lr():
    df = pd.read_csv('data/processed/compost_data.csv')

    # Features and Target
    X = df[['pH', 'Temperature', 'Humidity', 'Moisture']]
    y = df['Days_to_Ready']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and Train
    lr = LinearRegression()
    lr.fit(X_train, y_train)

    # Save the model
    joblib.dump(lr, 'models/lr_predictor.pkl')
    print("Linear Regression model saved to models/lr_predictor.pkl")

if __name__ == "__main__":
    train_lr()