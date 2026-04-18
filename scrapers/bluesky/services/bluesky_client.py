import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

PUBLIC_APPVIEW_URL = "https://public.api.bsky.app"
API_APPVIEW_URL = "https://api.bsky.app"
DEFAULT_PDS_URL = "https://bsky.social"


def _iso_start_of_day(value: date) -> str:
    return datetime.combine(value, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_end_exclusive(value: date) -> str:
    end_value = value + timedelta(days=1)
    return datetime.combine(end_value, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _web_post_url(handle: str, uri: str) -> Optional[str]:
    if not uri.startswith("at://"):
        return None
    post_id = uri.rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{handle}/post/{post_id}"


def _extract_text(post_view: dict[str, Any]) -> str:
    record = post_view.get("record") or {}
    text = record.get("text")
    if isinstance(text, str) and text.strip():
        return text

    embed = post_view.get("embed") or {}
    external = embed.get("external") or {}
    if isinstance(external, dict):
        title = external.get("title")
        if isinstance(title, str) and title.strip():
            return title

    return "Bluesky post"


def normalize_post(post_view: dict[str, Any]) -> dict[str, Any]:
    author = post_view.get("author") or {}
    record = post_view.get("record") or {}
    handle = author.get("handle", "")

    return {
        "uri": post_view.get("uri", ""),
        "cid": post_view.get("cid", ""),
        "url": _web_post_url(handle, post_view.get("uri", "")),
        "text": _extract_text(post_view),
        "indexed_at": post_view.get("indexedAt"),
        "created_at": record.get("createdAt"),
        "likes": post_view.get("likeCount", 0),
        "reposts": post_view.get("repostCount", 0),
        "replies": post_view.get("replyCount", 0),
        "quotes": post_view.get("quoteCount", 0),
        "languages": record.get("langs") or [],
        "author": {
            "handle": handle,
            "display_name": author.get("displayName"),
            "did": author.get("did"),
            "avatar": author.get("avatar"),
            "description": author.get("description"),
        },
        "embed": post_view.get("embed"),
    }


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def in_date_range(post: dict[str, Any], start_date: Optional[date], end_date: Optional[date]) -> bool:
    timestamp = _parse_timestamp(post.get("created_at")) or _parse_timestamp(post.get("indexed_at"))
    if timestamp is None:
        return True

    timestamp_date = timestamp.date()
    if start_date and timestamp_date < start_date:
        return False
    if end_date and timestamp_date > end_date:
        return False
    return True


async def _create_session(client: httpx.AsyncClient) -> Optional[str]:
    identifier = os.getenv("BLUESKY_IDENTIFIER")
    password = os.getenv("BLUESKY_APP_PASSWORD")
    if not identifier or not password:
        return None

    pds_url = os.getenv("BLUESKY_PDS_URL", DEFAULT_PDS_URL).rstrip("/")
    resp = await client.post(
        f"{pds_url}/xrpc/com.atproto.server.createSession",
        json={"identifier": identifier, "password": password},
        headers={"User-Agent": "osint-lite-deftech-bluesky/1.0"},
    )
    resp.raise_for_status()
    return resp.json().get("accessJwt")


async def search_posts_raw(
    *,
    q: str,
    sort: str = "latest",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    language: Optional[str] = None,
    author: Optional[str] = None,
    mention: Optional[str] = None,
    domain: Optional[str] = None,
    url: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    params = {
        "q": q,
        "sort": sort,
        "limit": limit,
    }
    if start_date:
        params["since"] = _iso_start_of_day(start_date)
    if end_date:
        params["until"] = _iso_end_exclusive(end_date)
    if language:
        params["lang"] = language
    if author:
        params["author"] = author
    if mention:
        params["mentions"] = mention
    if domain:
        params["domain"] = domain
    if url:
        params["url"] = url

    encoded = urlencode(params, doseq=True)
    headers = {"User-Agent": "osint-lite-deftech-bluesky/1.0"}

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for base_url in (PUBLIC_APPVIEW_URL, API_APPVIEW_URL):
            resp = await client.get(
                f"{base_url}/xrpc/app.bsky.feed.searchPosts?{encoded}",
                headers=headers,
            )
            if resp.status_code < 400:
                data = resp.json()
                return data.get("posts", [])
            if resp.status_code not in (401, 403):
                resp.raise_for_status()

        access_jwt = await _create_session(client)
        if access_jwt:
            pds_url = os.getenv("BLUESKY_PDS_URL", DEFAULT_PDS_URL).rstrip("/")
            resp = await client.get(
                f"{pds_url}/xrpc/app.bsky.feed.searchPosts?{encoded}",
                headers={**headers, "Authorization": f"Bearer {access_jwt}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("posts", [])

        raise httpx.HTTPStatusError(
            "Bluesky search is currently blocked by the public endpoint and no authenticated credentials were configured.",
            request=httpx.Request("GET", f"{PUBLIC_APPVIEW_URL}/xrpc/app.bsky.feed.searchPosts"),
            response=resp,
        )
