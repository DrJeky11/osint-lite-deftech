try:
    from ..models import BlueskyRequest
    from .bluesky_client import in_date_range, normalize_post, search_posts_raw
except ImportError:
    from models import BlueskyRequest
    from services.bluesky_client import in_date_range, normalize_post, search_posts_raw


def build_search_query(req: BlueskyRequest) -> str:
    keyword_clause = " OR ".join(f'"{keyword}"' for keyword in req.keywords)
    return f"({keyword_clause})"


def build_request_description(req: BlueskyRequest) -> str:
    bits = [f"keywords={req.keywords}"]
    if req.author:
        bits.append(f"author={req.author}")
    if req.mention:
        bits.append(f"mention={req.mention}")
    if req.language:
        bits.append(f"language={req.language}")
    if req.domain:
        bits.append(f"domain={req.domain}")
    if req.url:
        bits.append(f"url={req.url}")
    if req.start_date or req.end_date:
        bits.append(f"dates={req.start_date}..{req.end_date}")
    return ", ".join(bits)


async def search_posts(req: BlueskyRequest) -> tuple[str, list[dict]]:
    query = build_search_query(req)
    post_views = await search_posts_raw(
        q=query,
        sort=req.sort,
        start_date=req.start_date,
        end_date=req.end_date,
        language=req.language,
        author=req.author,
        mention=req.mention,
        domain=req.domain,
        url=req.url,
        limit=req.max_posts,
    )

    normalized_posts = [normalize_post(post_view) for post_view in post_views]
    filtered_posts = [
        post for post in normalized_posts if in_date_range(post, req.start_date, req.end_date)
    ]

    return query, filtered_posts[: req.max_posts]
