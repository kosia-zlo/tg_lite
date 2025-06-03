# db.py
import sqlite3

def init_db(db_path="vpn.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            profile_name TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_profile_name(user_id, profile_name, db_path="vpn.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, profile_name TEXT)")
    cur.execute("INSERT OR REPLACE INTO users (id, profile_name) VALUES (?, ?)", (user_id, profile_name))
    conn.commit()
    conn.close()

def get_profile_name(user_id, db_path="vpn.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, profile_name TEXT)")
    cur.execute("SELECT profile_name FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else f"user{user_id}"
