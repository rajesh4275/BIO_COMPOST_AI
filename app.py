from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)

# Load the trained models
try:
    rf_model = joblib.load('models/rf_classifier.pkl')
    lr_model = joblib.load('models/lr_predictor.pkl')
except:
    print("Error: Models not found. Please train them first!")

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction_days = None
    waste_category = None
    
    if request.method == 'POST':
        # Get data from the HTML form
        ph = float(request.form['ph'])
        temp = float(request.form['temp'])
        humidity = float(request.form['humidity'])
        moisture = float(request.form['moisture'])
        n = float(request.form['n'])
        p = float(request.form['p'])
        k = float(request.form['k'])

        # 1. Classification (Random Forest)
        # RF needs all features including NPK to classify the type
        rf_input = np.array([[ph, temp, humidity, moisture, n, p, k]])
        waste_category = rf_model.predict(rf_input)[0]

        # 2. Prediction (Linear Regression)
        # LR predicts days based on environmental sensors
        lr_input = np.array([[ph, temp, humidity, moisture]])
        prediction_days = round(lr_model.predict(lr_input)[0], 1)

    return render_template('index.html', 
                           days=prediction_days, 
                           category=waste_category)

if __name__ == '__main__':
    app.run(debug=True)