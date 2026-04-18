try:
    from ..models import XRequest
    from .x_client import in_date_range, normalize_post, search_posts_raw
except ImportError:
    from models import XRequest
    from services.x_client import in_date_range, normalize_post, search_posts_raw


def build_search_query(req: XRequest) -> str:
    keyword_clause = " OR ".join(f'"{keyword}"' for keyword in req.keywords)
    clauses = [f"({keyword_clause})"]

    if req.language:
        clauses.append(f"lang:{req.language}")
    if req.author:
        clauses.append(f"from:{req.author}")
    if req.mention:
        clauses.append(f"@{req.mention}")
    if req.domain:
        clauses.append(f"url:{req.domain}")
    if req.url:
        clauses.append(f'"{req.url}"')

    clauses.append("-is:retweet")
    return " ".join(clauses)


def build_request_description(req: XRequest) -> str:
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
        bits.append("window=recent-search-only")
    return ", ".join(bits)


async def search_posts(req: XRequest) -> tuple[str, list[dict]]:
    query = build_search_query(req)
    raw_posts, users_by_id = await search_posts_raw(
        query=query,
        sort=req.sort,
        start_date=req.start_date,
        end_date=req.end_date,
        limit=req.max_posts,
    )

    normalized_posts = [normalize_post(post, users_by_id) for post in raw_posts]
    filtered_posts = [
        post for post in normalized_posts if in_date_range(post, req.start_date, req.end_date)
    ]

    return query, filtered_posts[: req.max_posts]
