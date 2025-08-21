# scripts/generate_daily_topic.py
import os, json, datetime, hashlib, urllib.parse, requests
from pathlib import Path
from slugify import slugify
import feedparser

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
IMAGES = ROOT / "static" / "images"
DATA = ROOT / ".data"
SEEN = DATA / "seen_trends.json"

POSTS.mkdir(parents=True, exist_ok=True)
IMAGES.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

seen = set()
if SEEN.exists():
    seen = set(json.load(SEEN))

# Source priority list (Google Trends daily RSS — geo fallback to US/IN)
SOURCES = [
    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
    "https://news.ycombinator.com/rss",
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/finance/.rss"
]

def fetch_top_topic():
    for url in SOURCES:
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                continue
            for e in feed.entries:
                title = e.title.strip()
                key = hashlib.sha1(title.encode()).hexdigest()
                if key in seen:
                    continue
                # return first unseen title and source
                return title, getattr(e,'link',url)
        except Exception:
            continue
    return None, None

def download_image_for_title(title, slug):
    q = urllib.parse.quote_plus(title.split("|")[0])
    img_url = f"https://source.unsplash.com/1600x900/?{q}"
    try:
        r = requests.get(img_url, timeout=15)
        if r.status_code == 200:
            path = IMAGES / f"{slug}.jpg"
            with open(path, "wb") as f: f.write(r.content)
            return f"/images/{slug}.jpg"
    except Exception:
        pass
    return ""

def create_post(title, source_url, img_path):
    slug = slugify(title)[:60]
    today = datetime.date.today().isoformat()
    filename = f"{today}-{slug}"
    post_dir = POSTS / filename
    post_dir.mkdir(parents=True, exist_ok=True)
    post_file = post_dir / "index.md"
    date_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    content = f"""---
title: "{title}"
date: "{date_iso}"
draft: false
tags: ["auto","trending"]
description: "Auto-generated trending topic — {title}"
image: "{img_path}"
---

**Auto-generated summary**

Source: {source_url}

This is an auto-generated seed article for **{title}**. Add more analysis if required.

_This page was generated automatically._
"""
    post_file.write_text(content, encoding="utf-8")
    return filename

def main():
    title, src = fetch_top_topic()
    if not title:
        print("No new topic found")
        return
    slug = slugify(title)[:60]
    img = download_image_for_title(title, slug)
    post_name = create_post(title, src, img)
    seen.add(hashlib.sha1(title.encode()).hexdigest())
    with open(SEEN, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, indent=2)
    print("Created", post_name)

if __name__ == "__main__":
    main()
