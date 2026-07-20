from flask import Flask, render_template, request, redirect, url_for, session, flash
import joblib
import numpy as np
import os
import database
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Set secret key for session management
app.secret_key = os.urandom(24)

# Initialize database tables
database.init_db()

# Load the trained models
try:
    rf_model = joblib.load('models/rf_classifier.pkl')
    lr_model = joblib.load('models/lr_predictor.pkl')
except Exception as e:
    print(f"Error: Models not found. Please train them first! Details: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    # Route protection - only logged-in users can access the dashboard
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    prediction_days = None
    waste_category = None
    
    if request.method == 'POST':
        try:
            # Get data from the HTML form
            ph = float(request.form['ph'])
            temp = float(request.form['temp'])
            humidity = float(request.form['humidity'])
            moisture = float(request.form['moisture'])
            n = float(request.form['n'])
            p = float(request.form['p'])
            k = float(request.form['k'])

            # 1. Classification (Random Forest)
            rf_input = np.array([[ph, temp, humidity, moisture, n, p, k]])
            waste_category = rf_model.predict(rf_input)[0]

            # 2. Prediction (Linear Regression)
            lr_input = np.array([[ph, temp, humidity, moisture]])
            prediction_days = round(lr_model.predict(lr_input)[0], 1)
            
            # Log the prediction into database history
            database.add_prediction(
                username=username,
                ph=ph,
                temp=temp,
                humidity=humidity,
                moisture=moisture,
                n=n,
                p=p,
                k=k,
                waste_category=waste_category,
                predicted_days=prediction_days
            )
        except Exception as e:
            flash(f"Error executing prediction: {e}", "danger")

    # Fetch user's prediction logs for the history panel
    history = database.get_user_predictions(username)

    return render_template('index.html', 
                           username=username,
                           days=prediction_days, 
                           category=waste_category,
                           history=history)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not username or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))
            
        # Hash password and save user
        hashed_pw = generate_password_hash(password)
        success = database.create_user(username, hashed_pw)
        
        if success:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already exists. Please choose a different one.", "danger")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
        
    ip_address = request.remote_addr
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return redirect(url_for('login'))

        # Check rate limit/lockout
        is_locked, lockout_msg, remaining_user, remaining_ip = database.check_lockout(username, ip_address)
        if is_locked:
            flash(lockout_msg, "danger")
            return redirect(url_for('login'))
            
        user = database.get_user(username)
        
        if user and check_password_hash(user['password_hash'], password):
            # Login successful
            database.record_login_success(username, ip_address)
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            # Login failed
            database.record_login_failure(username, ip_address)
            
            # Recalculate remaining attempts
            _, _, remaining_user, remaining_ip = database.check_lockout(username, ip_address)
            remaining = min(remaining_user, remaining_ip)
            
            if remaining <= 0:
                flash("Too many failed login attempts. Your account/IP has been locked out for 15 minutes.", "danger")
            else:
                flash(f"Invalid username or password. Remaining attempts: {remaining}.", "warning")
                
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)