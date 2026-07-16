import pandas as pd
import numpy as np
import os

def preprocess_data():
    # File paths
    raw_path = 'data/raw/Agriculture_dataset_with_metadata.csv'
    processed_path = 'data/processed/compost_data.csv'

    # Load the main dataset
    df = pd.read_csv(raw_path)

    # 1. Feature Selection: Keep the columns relevant to composting
    # We keep N, P, K because they help the Random Forest classify waste types
    cols_to_keep = ['pH', 'Temperature', 'Humidity', 'Moisture', 'N', 'P', 'K', 'Semantic_Tag']
    df_clean = df[cols_to_keep].copy()

    # 2. Data Cleaning: Fill missing values with the mean
    df_clean = df_clean.fillna(df_clean.mean(numeric_only=True))

    # 3. Create the Target Variable: "Days_to_Ready" (The logic for Linear Regression)
    # Optimal composting: Temp ~55°C, Moisture ~50%, pH ~7.0
    # This formula simulates how these factors affect speed
    df_clean['Days_to_Ready'] = (
        abs(df_clean['Temperature'] - 55) * 0.5 + 
        abs(df_clean['Moisture'] - 50) * 0.8 + 
        abs(df_clean['pH'] - 7.0) * 2.0 + 
        14 # Base days
    )

    # 4. Save the processed data
    if not os.path.exists('data/processed'):
        os.makedirs('data/processed')
        
    df_clean.to_csv(processed_path, index=False)
    print(f"Processed data saved to {processed_path}")

if __name__ == "__main__":
    preprocess_data()