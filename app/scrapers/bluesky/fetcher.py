from .client import normalize_post, search_posts_raw


def build_query(topics: list[str]) -> str:
    """Build a Bluesky search query from topic keywords using OR logic."""
    return " OR ".join(f'"{t}"' for t in topics)


async def fetch_posts(
    query: str,
    max_posts: int = 100,
) -> list[dict]:
    """Search Bluesky and return normalized post dicts."""
    raw_posts = await search_posts_raw(q=query, sort="latest", limit=max_posts)
    return [normalize_post(p) for p in raw_posts][:max_posts]
