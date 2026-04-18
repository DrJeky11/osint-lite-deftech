"""X/Twitter API v2 client for recent-search.

Ported from scrapers/x/services/x_client.py (zeetwii) into the unified
app/scrapers layout so it can be called by the consolidated refresh pipeline.
"""

import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://api.x.com"
DEFAULT_SEARCH_PATH = "/2/tweets/search/recent"

TWEET_FIELDS = ",".join(
    [
        "created_at",
        "entities",
        "lang",
        "note_tweet",
        "public_metrics",
        "referenced_tweets",
    ]
)
USER_FIELDS = ",".join(["description", "name", "profile_image_url", "username"])


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _iso_start_of_day(value: date) -> str:
    return datetime.combine(value, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_end_exclusive(value: date) -> str:
    end_value = value + timedelta(days=1)
    return datetime.combine(end_value, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _recent_search_now() -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=30)


def _clamp_recent_search_window(
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[Optional[str], Optional[str]]:
    """Clamp dates to the X recent-search 7-day rolling window."""
    now_utc = _recent_search_now()
    oldest_allowed = now_utc - timedelta(days=7)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    if start_date:
        start_time = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    if end_date:
        end_time = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

    if end_time and end_time > now_utc:
        end_time = now_utc
    if start_time and start_time < oldest_allowed:
        start_time = oldest_allowed
    if start_time and end_time and start_time >= end_time:
        start_time = max(oldest_allowed, end_time - timedelta(days=1))

    start_value = start_time.isoformat().replace("+00:00", "Z") if start_time else None
    end_value = end_time.isoformat().replace("+00:00", "Z") if end_time else None
    return start_value, end_value


# ---------------------------------------------------------------------------
# Post normalization
# ---------------------------------------------------------------------------

def _tweet_url(username: str, post_id: str) -> str:
    return f"https://x.com/{username}/status/{post_id}"


def _extract_text(post: dict[str, Any]) -> str:
    note_tweet = post.get("note_tweet") or {}
    note_text = note_tweet.get("text")
    if isinstance(note_text, str) and note_text.strip():
        return note_text
    text = post.get("text")
    if isinstance(text, str) and text.strip():
        return text
    return "X post"


def _extract_urls(post: dict[str, Any]) -> list[str]:
    entities = post.get("entities") or {}
    urls = entities.get("urls") or []
    normalized: list[str] = []
    for item in urls:
        if not isinstance(item, dict):
            continue
        expanded_url = item.get("expanded_url") or item.get("unwound_url") or item.get("url")
        if isinstance(expanded_url, str) and expanded_url:
            normalized.append(expanded_url)
    return normalized


def normalize_post(post: dict[str, Any], users_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Normalize a raw X API v2 tweet into a flat dict."""
    author_id = post.get("author_id", "")
    author = users_by_id.get(author_id, {})
    username = author.get("username") or "unknown"
    public_metrics = post.get("public_metrics") or {}

    return {
        "id": post.get("id", ""),
        "text": _extract_text(post),
        "url": _tweet_url(username, post.get("id", "")),
        "created_at": post.get("created_at"),
        "language": post.get("lang"),
        "likes": public_metrics.get("like_count", 0),
        "reposts": public_metrics.get("retweet_count", 0),
        "replies": public_metrics.get("reply_count", 0),
        "quotes": public_metrics.get("quote_count", 0),
        "bookmarks": public_metrics.get("bookmark_count", 0),
        "impressions": public_metrics.get("impression_count"),
        "author": {
            "id": author_id,
            "username": username,
            "name": author.get("name"),
            "description": author.get("description"),
            "profile_image_url": author.get("profile_image_url"),
        },
        "referenced_tweets": post.get("referenced_tweets") or [],
        "urls": _extract_urls(post),
    }


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------

def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def in_date_range(post: dict[str, Any], start_date: Optional[date], end_date: Optional[date]) -> bool:
    timestamp = _parse_timestamp(post.get("created_at"))
    if timestamp is None:
        return True
    timestamp_date = timestamp.date()
    if start_date and timestamp_date < start_date:
        return False
    if end_date and timestamp_date > end_date:
        return False
    return True


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

async def search_posts_raw(
    *,
    query: str,
    sort: str = "recency",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Call X API v2 recent-search with pagination and return (raw_posts, users_by_id)."""
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        raise RuntimeError(
            "X_BEARER_TOKEN is not configured. "
            "Set it in your environment or .env file to enable X search."
        )

    base_url = os.getenv("X_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    search_path = os.getenv("X_SEARCH_PATH", DEFAULT_SEARCH_PATH)
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "osint-lite-deftech-x/1.0",
    }

    start_time, end_time = _clamp_recent_search_window(start_date, end_date)

    all_posts: list[dict[str, Any]] = []
    users_by_id: dict[str, dict[str, Any]] = {}
    next_token: Optional[str] = None
    max_pages = 5  # safety cap to avoid runaway pagination

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for _ in range(max_pages):
            per_page = min(limit - len(all_posts), 100)
            if per_page < 10:
                per_page = 10  # X API minimum is 10
            params: dict[str, Any] = {
                "query": query,
                "max_results": per_page,
                "sort_order": sort,
                "tweet.fields": TWEET_FIELDS,
                "expansions": "author_id",
                "user.fields": USER_FIELDS,
            }
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if next_token:
                params["next_token"] = next_token

            resp = await client.get(f"{base_url}{search_path}", params=params, headers=headers)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = resp.text.strip()
                message = f"{exc}"
                if detail:
                    message = f"{message} | X response: {detail}"
                raise httpx.HTTPStatusError(message, request=exc.request, response=exc.response) from exc
            data = resp.json()

            posts = data.get("data") or []
            all_posts.extend(posts)

            includes = data.get("includes") or {}
            users = includes.get("users") or []
            for user in users:
                if isinstance(user, dict) and user.get("id"):
                    users_by_id[user["id"]] = user

            next_token = data.get("meta", {}).get("next_token")
            if not next_token or len(all_posts) >= limit:
                break

    return all_posts[:limit], users_by_id
