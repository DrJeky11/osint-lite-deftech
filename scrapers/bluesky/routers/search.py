import httpx
from fastapi import APIRouter, HTTPException

try:
    from ..models import BlueskyPost, BlueskyPostsResponse, BlueskyRequest, BlueskySummaryResponse
    from ..services.search_service import build_request_description, search_posts
    from ..services.summarize_service import summarize_posts
except ImportError:
    from models import BlueskyPost, BlueskyPostsResponse, BlueskyRequest, BlueskySummaryResponse
    from services.search_service import build_request_description, search_posts
    from services.summarize_service import summarize_posts

router = APIRouter()


@router.post("/posts", response_model=BlueskyPostsResponse)
async def get_posts(req: BlueskyRequest):
    try:
        query, posts = await search_posts(req)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Bluesky search failed: {exc}") from exc

    return BlueskyPostsResponse(
        query=query,
        post_count=len(posts),
        posts=[BlueskyPost(**post) for post in posts],
    )


@router.post("/summarize", response_model=BlueskySummaryResponse)
async def summarize_bluesky_posts(req: BlueskyRequest):
    try:
        query, posts = await search_posts(req)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Bluesky search failed: {exc}") from exc

    summary = await summarize_posts(
        posts,
        request_description=build_request_description(req),
        question=req.question,
    )
    return BlueskySummaryResponse(
        query=query,
        post_count=len(posts),
        posts=[BlueskyPost(**post) for post in posts],
        summary=summary,
    )
