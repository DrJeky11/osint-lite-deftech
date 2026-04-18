import feedparser
import httpx


def _normalize_categories(entry: dict) -> list[str]:
    tags = entry.get("tags") or []
    categories: list[str] = []

    for tag in tags:
        term = tag.get("term") if isinstance(tag, dict) else None
        if isinstance(term, str):
            cleaned = term.strip()
            if cleaned:
                categories.append(cleaned)

    return categories


def normalize_entry(entry: dict, fallback_id: str) -> dict:
    title = (entry.get("title") or "").strip() or "Untitled entry"
    link = entry.get("link")

    return {
        "id": str(entry.get("id") or entry.get("guid") or link or fallback_id),
        "title": title,
        "link": link,
        "published": entry.get("published") or entry.get("pubDate"),
        "updated": entry.get("updated"),
        "author": entry.get("author"),
        "summary": entry.get("summary") or entry.get("description"),
        "categories": _normalize_categories(entry),
    }


def normalize_feed(parsed_feed) -> dict:
    feed = parsed_feed.feed
    return {
        "title": feed.get("title"),
        "link": feed.get("link"),
        "description": feed.get("subtitle") or feed.get("description"),
        "language": feed.get("language"),
    }


async def fetch_feed(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        response = await client.get(url, headers={"User-Agent": "osint-lite-deftech-rss/0.1"})
        response.raise_for_status()

    parsed = feedparser.parse(response.content)

    if parsed.bozo and not parsed.entries:
        raise ValueError("The provided URL did not return a valid RSS/Atom feed.")

    return parsed

