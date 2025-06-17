# backend/app.py

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

#本地测试使用
# app = Flask(__name__, static_folder="../frontend", static_url_path="")

#部署使用
app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/posts", methods=["GET"])
def get_posts():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    search = request.args.get("search", "").strip().lower()
    source_filter = request.args.get("source", "").strip().lower()
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

    posts = [dict(row) for row in rows]
    updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.close()
    return jsonify({
        "page": page,
        "limit": limit,
        "total": total,
        "posts": posts,
        "updated_time": updated_time
    })

@app.route("/api/posts/latest-time")
def get_latest_post_time():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(created_utc) FROM posts")
    result = c.fetchone()
    conn.close()

    latest_time = result[0] if result and result[0] else None
    return jsonify({"latest_time": latest_time})


@app.route("/api/recommendation/today")
def get_today_recommendation():
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT title, url FROM recommendations WHERE date = ?", (today,))
    rows = c.fetchall()
    conn.close()

    recommendations = [dict(row) for row in rows]
    return jsonify({
        "posts": recommendations,
        "has_data": bool(recommendations),
        "date": today
    })


@app.route("/api/recommendation", methods=["POST"])
def add_recommendation():
    data = request.json
    title = data.get("title")
    url = data.get("url")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 检查是否已存在相同标题的推荐
    c.execute("SELECT COUNT(*) FROM recommendations WHERE title = ? AND date = ?", (title, date))
    if c.fetchone()[0] > 0:
        conn.close()
        return jsonify({"error": "This recommendation already exists for today"}), 400

    try:
        c.execute("INSERT INTO recommendations (title, url, date) VALUES (?, ?, ?)", (title, url, date))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    conn.close()

    return jsonify({"message": "Recommendation added"})


#本地测试使用
# if __name__ == "__main__":
#     if not os.path.exists(DB_PATH):
#         print("⛔ 数据库不存在，请先运行 fetcher.py 抓取并初始化数据库")
#     else:
#         app.run(debug=True)

#部署使用
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("⛔ 数据库不存在，请先运行 fetcher.py 抓取并初始化数据库")
    else:
        port = int(os.environ.get("PORT", 10000))  # Render 会设置这个环境变量
        app.run(host="0.0.0.0", port=port)
