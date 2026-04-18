import httpx
from fastapi import APIRouter, HTTPException

try:
    from ..models import XPost, XPostsResponse, XRequest, XSummaryResponse
    from ..services.search_service import build_request_description, search_posts
    from ..services.summarize_service import summarize_posts
except ImportError:
    from models import XPost, XPostsResponse, XRequest, XSummaryResponse
    from services.search_service import build_request_description, search_posts
    from services.summarize_service import summarize_posts

router = APIRouter()


@router.post("/posts", response_model=XPostsResponse)
async def get_posts(req: XRequest):
    try:
        query, posts = await search_posts(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"X search failed: {exc}") from exc

    return XPostsResponse(
        query=query,
        post_count=len(posts),
        posts=[XPost(**post) for post in posts],
    )


@router.post("/summarize", response_model=XSummaryResponse)
async def summarize_x_posts(req: XRequest):
    try:
        query, posts = await search_posts(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"X search failed: {exc}") from exc

    summary = await summarize_posts(
        posts,
        request_description=build_request_description(req),
        question=req.question,
    )
    return XSummaryResponse(
        query=query,
        post_count=len(posts),
        posts=[XPost(**post) for post in posts],
        summary=summary,
    )

