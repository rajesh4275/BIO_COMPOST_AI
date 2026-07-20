import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), 'users.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            lockout_until TEXT
        )
    ''')
    
    # IP-based login attempts table for brute-force protection
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            ip_address TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            lockout_until TEXT
        )
    ''')
    
    # Prediction history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ph REAL,
            temp REAL,
            humidity REAL,
            moisture REAL,
            n REAL,
            p REAL,
            k REAL,
            waste_category TEXT,
            predicted_days REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username.lower(), password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username.lower(),))
    user = cursor.fetchone()
    conn.close()
    return user

def check_lockout(username, ip_address):
    """
    Checks if username or IP is locked out.
    Returns (is_locked, message, remaining_attempts_user, remaining_attempts_ip)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    
    # Check IP lockout
    cursor.execute('SELECT * FROM login_attempts WHERE ip_address = ?', (ip_address,))
    ip_record = cursor.fetchone()
    ip_attempts = 0
    if ip_record:
        ip_attempts = ip_record['attempts']
        if ip_record['lockout_until']:
            lockout_time = datetime.fromisoformat(ip_record['lockout_until'])
            if now < lockout_time:
                conn.close()
                wait_min = round((lockout_time - now).total_seconds() / 60, 1)
                return True, f"IP address locked out. Try again in {wait_min} minutes.", 10, 0
            else:
                # Lockout expired, reset attempts
                cursor.execute('UPDATE login_attempts SET attempts = 0, lockout_until = NULL WHERE ip_address = ?', (ip_address,))
                conn.commit()
                ip_attempts = 0
                
    # Check Username lockout
    cursor.execute('SELECT * FROM users WHERE username = ?', (username.lower(),))
    user_record = cursor.fetchone()
    user_attempts = 0
    if user_record:
        user_attempts = user_record['failed_attempts']
        if user_record['lockout_until']:
            lockout_time = datetime.fromisoformat(user_record['lockout_until'])
            if now < lockout_time:
                conn.close()
                wait_min = round((lockout_time - now).total_seconds() / 60, 1)
                return True, f"Account locked out. Try again in {wait_min} minutes.", 0, 10 - ip_attempts
            else:
                # Lockout expired, reset attempts
                cursor.execute('UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE username = ?', (username.lower(),))
                conn.commit()
                user_attempts = 0
                
    conn.close()
    return False, "", 10 - user_attempts, 10 - ip_attempts

def record_login_success(username, ip_address):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Reset username attempts
    cursor.execute('UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE username = ?', (username.lower(),))
    
    # Reset IP attempts
    cursor.execute('UPDATE login_attempts SET attempts = 0, lockout_until = NULL WHERE ip_address = ?', (ip_address,))
    
    conn.commit()
    conn.close()

def record_login_failure(username, ip_address):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    lockout_duration = timedelta(minutes=15)
    lockout_until_str = (now + lockout_duration).isoformat()
    
    # 1. Update Username attempts
    cursor.execute('SELECT * FROM users WHERE username = ?', (username.lower(),))
    user = cursor.fetchone()
    if user:
        new_attempts = user['failed_attempts'] + 1
        if new_attempts >= 10:
            cursor.execute(
                'UPDATE users SET failed_attempts = ?, lockout_until = ? WHERE username = ?',
                (new_attempts, lockout_until_str, username.lower())
            )
        else:
            cursor.execute(
                'UPDATE users SET failed_attempts = ? WHERE username = ?',
                (new_attempts, username.lower())
            )
    else:
        # If user doesn't exist, we can't increment failed_attempts on user table,
        # but the IP tracking will handle limiting overall failed attempts
        pass
            
    # 2. Update IP attempts
    cursor.execute('SELECT * FROM login_attempts WHERE ip_address = ?', (ip_address,))
    ip_rec = cursor.fetchone()
    if ip_rec:
        new_ip_attempts = ip_rec['attempts'] + 1
        if new_ip_attempts >= 10:
            cursor.execute(
                'UPDATE login_attempts SET attempts = ?, lockout_until = ? WHERE ip_address = ?',
                (new_ip_attempts, lockout_until_str, ip_address)
            )
        else:
            cursor.execute(
                'UPDATE login_attempts SET attempts = ? WHERE ip_address = ?',
                (new_ip_attempts, ip_address)
            )
    else:
        cursor.execute(
            'INSERT INTO login_attempts (ip_address, attempts) VALUES (?, 1)',
            (ip_address,)
        )
        
    conn.commit()
    conn.close()

def add_prediction(username, ph, temp, humidity, moisture, n, p, k, waste_category, predicted_days):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (username, ph, temp, humidity, moisture, n, p, k, waste_category, predicted_days)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username.lower(), ph, temp, humidity, moisture, n, p, k, waste_category, predicted_days))
    conn.commit()
    conn.close()

def get_user_predictions(username, limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ph, temp, humidity, moisture, n, p, k, waste_category, predicted_days, timestamp
        FROM predictions
        WHERE username = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (username.lower(), limit))
    rows = cursor.fetchall()
    predictions = [dict(row) for row in rows]
    conn.close()
    return predictions
