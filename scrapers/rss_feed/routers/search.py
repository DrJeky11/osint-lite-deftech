import httpx
from fastapi import APIRouter, HTTPException

try:
    from ..models import RSSEntriesResponse, RSSEntry, RSSRequest, RSSSummaryResponse
    from ..services.search_service import build_request_description, fetch_entries
    from ..services.summarize_service import summarize_entries
except ImportError:
    from models import RSSEntriesResponse, RSSEntry, RSSRequest, RSSSummaryResponse
    from services.search_service import build_request_description, fetch_entries
    from services.summarize_service import summarize_entries

router = APIRouter()


@router.post("/entries", response_model=RSSEntriesResponse)
async def get_entries(req: RSSRequest):
    try:
        feed, entries = await fetch_entries(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"RSS fetch failed: {exc}") from exc

    return RSSEntriesResponse(
        feed_url=str(req.feed_url),
        feed=feed,
        entry_count=len(entries),
        entries=[RSSEntry(**entry) for entry in entries],
    )


@router.post("/summarize", response_model=RSSSummaryResponse)
async def summarize_rss_entries(req: RSSRequest):
    try:
        feed, entries = await fetch_entries(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"RSS fetch failed: {exc}") from exc

    summary = await summarize_entries(
        entries,
        request_description=build_request_description(req, feed),
        question=req.question,
    )
    return RSSSummaryResponse(
        feed_url=str(req.feed_url),
        feed=feed,
        entry_count=len(entries),
        entries=[RSSEntry(**entry) for entry in entries],
        summary=summary,
    )

