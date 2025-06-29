from database import SessionLocal, Post

def delete_test_posts():
    session = SessionLocal()
    try:
        deleted = session.query(Post).filter(
            Post.url.in_(['https://example.com/test1', 'https://example.com/test2'])
        ).delete(synchronize_session=False)
        session.commit()
        print(f"成功删除了 {deleted} 条测试数据。")
    except Exception as e:
        session.rollback()
        print("删除测试数据时出错：", e)
    finally:
        session.close()

if __name__ == "__main__":
    delete_test_posts()
