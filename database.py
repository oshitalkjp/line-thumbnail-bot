import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        line_user_id TEXT PRIMARY KEY,
        credits INTEGER DEFAULT 1,
        is_free_trial_used BOOLEAN DEFAULT 0,
        created_at DATETIME
    )''')
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        line_user_id TEXT,
        amount INTEGER,
        credits_added INTEGER,
        status TEXT,
        created_at DATETIME
    )''')
    
    conn.commit()
    conn.close()

def get_user(line_user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE line_user_id = ?", (line_user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def create_user(line_user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (line_user_id, credits, is_free_trial_used, created_at) VALUES (?, ?, ?, ?)",
                  (line_user_id, 1, 0, datetime.now()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # User already exists
    conn.close()

def add_credits(line_user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE line_user_id = ?", (amount, line_user_id))
    conn.commit()
    conn.close()

def decrement_credit(line_user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits - 1, is_free_trial_used = 1 WHERE line_user_id = ?", (line_user_id,))
    conn.commit()
    conn.close()

def record_transaction(tx_id, line_user_id, amount, credits_added, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (id, line_user_id, amount, credits_added, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (tx_id, line_user_id, amount, credits_added, status, datetime.now()))
    conn.commit()
    conn.close()
