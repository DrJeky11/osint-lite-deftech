import re
from datetime import date
from typing import Optional
from urllib.parse import urlencode

import feedparser
import httpx

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

def build_query(
    topics: list[str],
    start_date: Optional[date],
    end_date: Optional[date],
    location: Optional[str],
) -> str:
    # Quote each topic and OR them together so multi-word topics stay intact
    topic_clause = " OR ".join(f'"{t}"' for t in topics)
    parts = [f"({topic_clause})"]
    if location:
        parts.append(f'"{location}"')
    if start_date:
        parts.append(f"after:{start_date.isoformat()}")
    if end_date:
        parts.append(f"before:{end_date.isoformat()}")
    return " ".join(parts)

def _strip_html(text: Optional[str]) -> Optional[str]:
    if not text:
        return text
    return re.sub(r"<[^>]+>", "", text).strip()

async def fetch_news(
    query: str,
    country: str = "US",
    language: str = "en",
    max_articles: int = 100,
) -> list[dict]:
    params = {
        "q": query,
        "hl": language,
        "gl": country,
        "ceid": f"{country}:{language}",
    }
    url = f"{GOOGLE_NEWS_RSS}?{urlencode(params)}"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "news-summary-bot/1.0"})
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    articles = []
    for entry in feed.entries[:max_articles]:
        src = entry.get("source")
        articles.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published"),
            "source": src.get("title") if isinstance(src, dict) else (getattr(src, "title", None) if src else None),
            "description": _strip_html(entry.get("summary")),
        })
    return articles