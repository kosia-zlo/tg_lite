import sqlite3

def init_db():
    conn = sqlite3.connect("vpn.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            invoice_id TEXT UNIQUE,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_payment(user_id, invoice_id, amount):
    conn = sqlite3.connect("vpn.db")
    c = conn.cursor()
    c.execute(
        'INSERT INTO payments (user_id, invoice_id, amount, status) VALUES (?, ?, ?, ?)',
        (user_id, invoice_id, amount, 'pending')
    )
    conn.commit()
    conn.close()

def mark_paid(invoice_id):
    conn = sqlite3.connect("vpn.db")
    c = conn.cursor()
    c.execute('UPDATE payments SET status="paid" WHERE invoice_id=?', (invoice_id,))
    conn.commit()
    conn.close()

def is_paid(invoice_id):
    conn = sqlite3.connect("vpn.db")
    c = conn.cursor()
    c.execute('SELECT status FROM payments WHERE invoice_id=?', (invoice_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == "paid"

def save_profile_name(user_id, profile_name):
    conn = sqlite3.connect('vpn.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, profile_name TEXT)")
    cur.execute("INSERT OR REPLACE INTO users (id, profile_name) VALUES (?, ?)", (user_id, profile_name))
    conn.commit()
    conn.close()

def get_profile_name(user_id):
    conn = sqlite3.connect('vpn.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, profile_name TEXT)")
    cur.execute("SELECT profile_name FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return f"user{user_id}"
