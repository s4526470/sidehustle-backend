# backend/database.py

import os
from dotenv import load_dotenv
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import or_

# 载入环境变量
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print("连接地址:", DATABASE_URL)

# 初始化数据库连接和会话
# 设置连接池的大小和最大溢出数
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_timeout=30,  # 连接超时限制
    pool_recycle=3600  # 连接池连接的最大使用时间
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------- 模型定义 --------------------

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    created_utc = Column(String)  # ISO 格式字符串
    source = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "created_utc": self.created_utc,
            "source": self.source
        }

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text)
    date = Column(String, unique=True, nullable=False)  # 格式: 'YYYY-MM-DD'

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "date": self.date
        }

# -------------------- 初始化表 --------------------

def init_db():
    Base.metadata.create_all(bind=engine)

# -------------------- Post 相关操作 --------------------

def save_posts_to_db(posts):
    # 使用 with 语句自动管理 session
    with SessionLocal() as db:
        try:
            for post in posts:
                new_post = Post(
                    title=post.get("title"),
                    url=post.get("url"),
                    created_utc=post.get("created_utc"),
                    source=post.get("source")
                )
                db.add(new_post)
            db.commit()
            print(f"Successfully added {len(posts)} posts.")
        except IntegrityError as e:
            db.rollback()  # 如果有重复数据等问题，回滚事务
            print(f"Error inserting posts: {e}")
        except Exception as e:
            db.rollback()  # 捕获其它异常并回滚
            print(f"Unexpected error: {e}")
        # 由于使用了 with 语句，db 会自动关闭

def query_posts(page=1, limit=10, search="", source_filter=""):
    # 使用 with 语句管理会话
    with SessionLocal() as session:
        query = session.query(Post)

        if search:
            search = search.lower()
            query = query.filter(
                or_(
                    func.lower(Post.title).like(f"%{search}%"),
                    func.lower(Post.source).like(f"%{search}%")
                )
            )

        if source_filter:
            query = query.filter(func.lower(Post.source) == source_filter.lower())

        total = query.count()

        posts = query.order_by(Post.created_utc.desc() if Post.created_utc else Post.id.desc()) \
                     .offset((page - 1) * limit).limit(limit).all()

        results = [p.to_dict() for p in posts]
        return results, total

def get_existing_urls():
    # 使用 with 语句管理会话
    with SessionLocal() as db:
        urls = db.query(Post.url).all()
        return set(url for (url,) in urls)

def get_latest_post_time():
    """获取最新帖子的 created_utc（字符串格式），用于增量抓取"""
    # 使用 with 语句管理会话
    with SessionLocal() as session:
        latest_post = session.query(Post).order_by(Post.created_utc.desc()).first()
        return latest_post.created_utc if latest_post else None


# -------------------- Recommendation 相关操作 --------------------

def get_today_recommendation(target_date=None):
    """获取某天的推荐（默认为今天）"""
    session = SessionLocal()
    if target_date is None:
        target_date = date.today().isoformat()
    try:
        rec = session.query(Recommendation).filter(Recommendation.date == target_date).first()
        return rec.to_dict() if rec else None
    finally:
        session.close()

def add_recommendation(title, url, date_str=None):
    """添加推荐（默认使用今天的日期）"""
    session = SessionLocal()
    if date_str is None:
        date_str = date.today().isoformat()
    try:
        recommendation = Recommendation(title=title, url=url, date=date_str)
        session.add(recommendation)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
    finally:
        session.close()
