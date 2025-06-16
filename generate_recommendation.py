# backend/generate_recommendation.py

import sqlite3
import random
from datetime import datetime

DB_PATH = "backend/data.db"

def generate_recommendation():
    today = datetime.now().date().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 检查今天是否已经有推荐，避免重复插入
    c.execute("SELECT COUNT(*) FROM recommendations WHERE date = ?", (today,))
    if c.fetchone()[0] > 0:
        print("Today’s recommendations already generated.")
        conn.close()
        return

    # 获取最近两天内的帖子
    c.execute("""
        SELECT title, url FROM posts
        WHERE datetime(created_utc) >= datetime('now', '-2 day')
    """)
    posts = c.fetchall()
    if not posts:
        print("No recent posts found.")
        conn.close()
        return

    # 随机选取最多5个推荐
    sampled = random.sample(posts, min(5, len(posts)))

    inserted_count = 0
    for post in sampled:
        try:
            c.execute("""
                INSERT INTO recommendations (title, url, date)
                VALUES (?, ?, ?)
            """, (post["title"], post["url"], today))
            inserted_count += 1
        except sqlite3.IntegrityError:
            print(f"Skipped duplicate for {post['title']}")

    conn.commit()
    conn.close()
    print(f"Generated {inserted_count} recommendations for {today}.")

if __name__ == "__main__":
    generate_recommendation()
