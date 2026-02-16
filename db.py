import sqlite3

def create_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        emotion TEXT,
        entry TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

def get_user(username, password):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def add_journal(user_id, emotion, entry, timestamp):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO journal (user_id, timestamp, emotion, entry) VALUES (?, ?, ?, ?)",
              (user_id, timestamp, emotion, entry))
    conn.commit()
    conn.close()

def get_journals(user_id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, emotion, entry FROM journal WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

