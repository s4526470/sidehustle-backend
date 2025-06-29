# test_db_insert.py

from database import save_posts_to_db, SessionLocal, init_db, engine,Base


# 模拟测试数据
test_posts = [
    {
        "title": "测试文章一",
        "url": "https://example.com/test1",
        "created_utc": "2025-06-28T12:00:00Z",
        "source": "TestSource"
    },
    {
        "title": "测试文章二",
        "url": "https://example.com/test2",
        "created_utc": "2025-06-28T12:05:00Z",
        "source": "TestSource"
    }
]

# 使用 SessionLocal 进行数据库写入测试
with SessionLocal() as db:
    save_posts_to_db(db, test_posts)

print("测试数据已写入数据库")
