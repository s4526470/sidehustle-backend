# backend/generate_recommendation.py

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal,Post, Recommendation,Base


def generate_recommendation():
    session: Session = SessionLocal()
    today = datetime.now().date()

    try:
        # 检查今天是否已经生成推荐
        existing = session.query(Recommendation).filter(Recommendation.date == today).count()
        if existing > 0:
            print("Today's recommendations already generated.")
            return

        # 获取最近两天内的帖子
        two_days_ago = datetime.now() - timedelta(days=2)
        recent_posts = session.query(Post).filter(Post.created_utc >= two_days_ago).all()

        if not recent_posts:
            print("No recent posts found.")
            return

        # 随机选取最多5个推荐
        sampled = random.sample(recent_posts, min(5, len(recent_posts)))

        inserted_count = 0
        for post in sampled:
            try:
                recommendation = Recommendation(
                    title=post.title,
                    url=post.url,
                    date=today
                )
                session.add(recommendation)
                inserted_count += 1
            except IntegrityError:
                session.rollback()
                print(f"Skipped duplicate for {post.title}")

        session.commit()
        print(f"Generated {inserted_count} recommendations for {today}.")

    finally:
        session.close()


if __name__ == "__main__":
    generate_recommendation()
