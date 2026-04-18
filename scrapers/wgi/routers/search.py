import httpx
from fastapi import APIRouter, HTTPException

try:
    from ..models import GovernanceDimension, WGIRequest, WGIResponse
    from ..services.search_service import fetch_dimension_results
except ImportError:
    from models import GovernanceDimension, WGIRequest, WGIResponse
    from services.search_service import fetch_dimension_results

router = APIRouter()


async def _get_dimension_response(req: WGIRequest, dimension: GovernanceDimension) -> WGIResponse:
    try:
        return await fetch_dimension_results(req, dimension)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"World Bank WGI request failed: {exc}") from exc


@router.post("/voice-accountability", response_model=WGIResponse)
async def get_voice_accountability(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.voice_accountability)


@router.post("/political-stability", response_model=WGIResponse)
async def get_political_stability(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.political_stability)


@router.post("/government-effectiveness", response_model=WGIResponse)
async def get_government_effectiveness(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.government_effectiveness)


@router.post("/regulatory-quality", response_model=WGIResponse)
async def get_regulatory_quality(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.regulatory_quality)


@router.post("/rule-of-law", response_model=WGIResponse)
async def get_rule_of_law(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.rule_of_law)


@router.post("/control-of-corruption", response_model=WGIResponse)
async def get_control_of_corruption(req: WGIRequest):
    return await _get_dimension_response(req, GovernanceDimension.control_of_corruption)
