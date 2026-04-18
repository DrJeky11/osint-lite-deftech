import re
import logging
from typing import Optional
import feedparser
import httpx

logger = logging.getLogger(__name__)

def _strip_html(text: Optional[str]) -> Optional[str]:
    if not text:
        return text
    return re.sub(r"<[^>]+>", "", text).strip()

async def fetch_feed(feed_url: str, max_articles: int = 20, topics: list[str] | None = None) -> list[dict]:
    """Fetch and parse an RSS/Atom feed, returning articles in the standard shape."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(feed_url, headers={"User-Agent": "signal-atlas-rss/1.0"})
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    if feed.bozo:
        logger.warning("Feed at %s is malformed: %s", feed_url, feed.bozo_exception)

    feed_title = feed.feed.get("title", "")
    articles = []
    for entry in feed.entries[:max_articles]:
        articles.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published"),
            "source": feed_title or None,
            "description": _strip_html(entry.get("summary")),
        })

    if topics:
        lower_topics = [t.lower() for t in topics]
        articles = [
            a for a in articles
            if any(
                kw in (a.get("title", "") + " " + (a.get("description") or "")).lower()
                for kw in lower_topics
            )
        ]

    return articles
