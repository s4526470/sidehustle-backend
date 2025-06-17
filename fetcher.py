import requests
import feedparser
import time
import os

from database import init_db, save_posts_to_db, get_existing_urls


def format_time(timestamp):
    if isinstance(timestamp, (int, float)):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
    return timestamp or ""

def normalize_source(source_name):
    return source_name.strip().lower()

def fetch_reddit_posts(limit=10):
    print("🔍 Fetching Reddit...")
    url = "https://www.reddit.com/r/sidehustle/new.json"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SideHustleBot/1.0)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        posts = []
        children = data.get("data", {}).get("children", [])
        for item in children[:limit]:
            post = item.get("data", {})
            posts.append({
                "title": post.get("title"),
                "url": "https://www.reddit.com" + post.get("permalink", ""),
                "created_utc": format_time(post.get("created_utc")),
                "source": normalize_source("Reddit")
            })
        return posts

    except Exception as e:
        print("❌ Reddit fetch error:", e)
        return []

def fetch_rss_posts(feed_url, source_name, limit=5):
    print(f"🔍 Fetching RSS from {source_name}...")
    try:
        feed = feedparser.parse(feed_url)
        posts = []
        for entry in feed.entries[:limit]:
            posts.append({
                "title": entry.get("title"),
                "url": entry.get("link"),
                "created_utc": entry.get("published", ""),
                "source": normalize_source(source_name)
            })
        return posts
    except Exception as e:
        print(f"❌ RSS fetch error from {source_name}:", e)
        return []

def fetch_devto_posts(limit=5):
    print("🔍 Fetching Dev.to...")
    try:
        res = requests.get("https://dev.to/api/articles?tag=sidehustle&per_page=" + str(limit), timeout=10)
        res.raise_for_status()
        data = res.json()
        posts = []
        for post in data:
            posts.append({
                "title": post.get("title"),
                "url": post.get("url"),
                "created_utc": post.get("published_at", ""),
                "source": normalize_source("Dev.to")
            })
        return posts
    except Exception as e:
        print("❌ Dev.to fetch error:", e)
        return []

def fetch_medium_rss(limit=5):
    return fetch_rss_posts("https://medium.com/feed/tag/side-hustle", "Medium", limit)

def fetch_hackernews_posts(limit=5):
    print("🔍 Fetching Hacker News...")
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:limit * 2]
        posts = []
        for id in top_ids:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json", timeout=10).json()
            if item and 'title' in item and 'url' in item:
                posts.append({
                    "title": item["title"],
                    "url": item["url"],
                    "created_utc": format_time(item.get("time", 0)),
                    "source": normalize_source("Hacker News")
                })
            if len(posts) >= limit:
                break
        return posts
    except Exception as e:
        print("❌ Hacker News fetch error:", e)
        return []

def fetch_remoteok_posts(limit=5):
    print("🔍 Fetching Remote OK...")
    try:
        res = requests.get("https://remoteok.io/api", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res.raise_for_status()
        data = res.json()
        posts = []
        for post in data:
            if isinstance(post, dict) and post.get("url") and post.get("date"):
                posts.append({
                    "title": post.get("position"),
                    "url": post.get("url"),
                    "created_utc": post.get("date"),
                    "source": normalize_source("Remote OK")
                })
            if len(posts) >= limit:
                break
        return posts
    except Exception as e:
        print("❌ Remote OK fetch error:", e)
        return []

def gather_all_posts():
    posts = []
    posts += fetch_reddit_posts(limit=10)
    posts += fetch_devto_posts(limit=5)
    posts += fetch_medium_rss(limit=5)
    posts += fetch_hackernews_posts(limit=5)
    posts += fetch_remoteok_posts(limit=5)
    rss_sources = [
        {"url": "https://www.sidehustlenation.com/feed/", "name": "Side Hustle Nation"},
        {"url": "https://www.smartpassiveincome.com/blog/rss/", "name": "Smart Passive Income"},
        {"url": "https://millennialmoney.com/feed/", "name": "Millennial Money"},
        {"url": "https://www.nichepursuits.com/feed/", "name": "Niche Pursuits"},
        {"url": "https://ryrob.com/feed/", "name": "Ryan Robinson"},
    ]
    for source in rss_sources:
        posts += fetch_rss_posts(source["url"], source["name"], limit=5)
    return posts

if __name__ == "__main__":
    print("📥 初始化数据库...")
    init_db()

    print("🌐 正在抓取所有副业资讯...")
    all_posts = gather_all_posts()
    print(f"📦 抓取完成，总数：{len(all_posts)} 条")

    print("🔍 正在检查并去除已存在的帖子...")
    existing_urls = get_existing_urls()
    new_posts = [post for post in all_posts if post["url"] not in existing_urls]

    print(f"🆕 新帖子数量：{len(new_posts)} 条")
    if new_posts:
        save_posts_to_db(new_posts)
        print("✅ 新帖子已保存到数据库")
    else:
        print("ℹ️ 没有新帖子，无需保存")
