# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
import os
from database import Post, Recommendation, SessionLocal, Base, engine

# Flask 应用配置
app = Flask(__name__)
CORS(app)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.route("/")
def index():
    return "✅ API Running!"


@app.route("/api/posts", methods=["GET"])
def get_posts():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    search = request.args.get("search", "").strip().lower()
    source_filter = request.args.get("source", "").strip().lower()
    offset = (page - 1) * limit

    db: Session = next(get_db())

    query = db.query(Post)

    if search:
        query = query.filter(
            (func.lower(Post.title).like(f"%{search}%")) |
            (func.lower(Post.source).like(f"%{search}%"))
        )

    if source_filter:
        query = query.filter(func.lower(Post.source) == source_filter)

    total = query.count()

    posts = query.order_by(desc(Post.created_utc)).offset(offset).limit(limit).all()

    updated_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "page": page,
        "limit": limit,
        "total": total,
        "posts": [p.to_dict() for p in posts],
        "updated_time": updated_time
    })


@app.route("/api/posts/latest-time")
def get_latest_post_time():
    db: Session = next(get_db())
    latest_time = db.query(func.max(Post.created_utc)).scalar()
    return jsonify({"latest_time": latest_time})


@app.route("/api/recommendation/today")
def get_today_recommendation():
    today = datetime.utcnow().date().isoformat()
    db: Session = next(get_db())

    rows = db.query(Recommendation).filter(Recommendation.date == today).all()

    return jsonify({
        "posts": [r.to_dict() for r in rows],
        "has_data": bool(rows),
        "date": today
    })


@app.route("/api/recommendation", methods=["POST"])
def add_recommendation():
    db: Session = next(get_db())
    data = request.json
    title = data.get("title")
    url = data.get("url")
    date_str = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    exists = db.query(Recommendation).filter_by(title=title, date=date).first()
    if exists:
        return jsonify({"error": "This recommendation already exists for today"}), 400

    try:
        new_recommendation = Recommendation(title=title, url=url, date=date)
        db.add(new_recommendation)
        db.commit()
        return jsonify({"message": "Recommendation added"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)