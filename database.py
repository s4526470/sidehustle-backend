# backend/database.py

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            created_utc TEXT,
            source TEXT
        )
    ''')

    c.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT,
            date TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def save_posts_to_db(posts):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for post in posts:
        try:
            c.execute('''
                INSERT INTO posts (title, url, created_utc, source)
                VALUES (?, ?, ?, ?)
            ''', (
                post.get("title"),
                post.get("url"),
                post.get("created_utc"),
                post.get("source")
            ))
        except sqlite3.IntegrityError:
            # URL 已存在，不插入
            continue
    conn.commit()
    conn.close()

def query_posts(page=1, limit=10, search="", source_filter=""):
    offset = (page - 1) * limit
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM posts WHERE 1=1"
    params = []

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(source) LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    if source_filter:
        query += " AND LOWER(source) = ?"
        params.append(source_filter)

    count_query = f"SELECT COUNT(*) FROM ({query})"
    c.execute(count_query, params)
    total = c.fetchone()[0]

    query += " ORDER BY datetime(created_utc) DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    posts = [dict(row) for row in rows]
    return posts, total

def get_existing_urls():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT url FROM posts")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)
