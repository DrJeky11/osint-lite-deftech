"""High-level X/Twitter search interface matching the Bluesky fetcher pattern."""

from .client import normalize_post, search_posts_raw


def build_query(topics: list[str]) -> str:
    """Build an X search query from topic keywords, excluding retweets."""
    keyword_clause = " OR ".join(f'"{t}"' for t in topics)
    return f"({keyword_clause}) -is:retweet"


async def fetch_posts(
    query: str,
    max_posts: int = 20,
) -> list[dict]:
    """Search X and return normalized post dicts."""
    raw_posts, users_by_id = await search_posts_raw(
        query=query, sort="recency", limit=max_posts
    )
    return [normalize_post(p, users_by_id) for p in raw_posts][:max_posts]
