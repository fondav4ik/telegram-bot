import sqlite3

DB_NAME = 'note.db'

def __init__db ():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id UNIQUE,
    user_name TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS notes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT,
    description TEXT,
    created_at DATE
    )
    ''')
    conn.commit()
    conn.close()