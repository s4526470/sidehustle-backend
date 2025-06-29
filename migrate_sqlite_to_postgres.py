# backend/migrate_sqlite_to_postgres.py

import sqlite3
from datetime import datetime
from database import Post, Recommendation, SessionLocal, Base, engine

# 旧 SQLite 数据库路径
SQLITE_PATH = "backend/data.db"

def migrate_sqlite_to_postgres():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 创建表（防止目标库中没有）
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    # Migrate Posts
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    for row in posts:
        try:
            post = Post(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                source=row["source"],
                created_utc=parse_datetime(row["created_utc"])
            )
            session.merge(post)  # merge = 如果 id 存在则更新，否则插入
        except Exception as e:
            print(f"Error migrating post ID {row['id']}: {e}")

    # Migrate Recommendations
    cursor.execute("SELECT * FROM recommendations")
    recs = cursor.fetchall()
    for row in recs:
        try:
            rec = Recommendation(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                date=parse_date(row["date"])
            )
            session.merge(rec)
        except Exception as e:
            print(f"Error migrating recommendation ID {row['id']}: {e}")

    session.commit()
    session.close()
    conn.close()
    print("✅ 数据迁移完成")

def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
