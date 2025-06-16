# backend/view_recommendations.py

import sqlite3

DB_PATH = "backend/data.db"

def view_sources():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT source FROM posts")
    rows = c.fetchall()

    for row in rows:
        print(dict(row))

    conn.close()

if __name__ == "__main__":
    view_sources()
