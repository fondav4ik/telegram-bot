import sqlite3
from .init_db import DB_NAME

def create_connection():
    return sqlite3.connect(DB_NAME)

def select_user_id_in_users(user_id):
    conn = create_connection()
    c = conn.cursor()

    c.execute('SELECT tg_id FROM users WHERE tg_id = ?', (user_id,))
    result = c.fetchall()


    conn.commit()
    conn.close()
    return result

def insert_user_in_db(tg_id, user_name):
    conn = create_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM users WHERE tg_id = ?', (tg_id,))
    existing_user = c.fetchone()

    if existing_user is None:
        c.execute('INSERT INTO users (tg_id, user_name) VALUES (?, ?)', (tg_id, user_name))
        conn.commit()

    conn.close()
def insert_note_in_db(user_id, description, created_at):
    conn = create_connection()
    c = conn.cursor()

    c.execute('INSERT INTO notes (user_id, description, created_at) VALUES (?, ?, ?) ', (user_id, description, created_at))

    conn.commit()
    conn.close()
def select_all_notes(user_id):
    conn = create_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM notes WHERE user_id = ?', (user_id,))

    rows = c.fetchall()

    conn.commit()
    conn.close()
    return rows
def delete_note_with_index(index):
    conn = create_connection()
    c = conn.cursor()

    c.execute('DELETE FROM notes WHERE id = ?', (index,))

    rows_affected = c.rowcount

    conn.commit()
    conn.close()

    return rows_affected > 0