"""ElevenLabs Convai agent webhook tools.

Ported from the original Cloudflare Pages Functions at functions/api/tools/*.js.
The agent is wired to POST/GET /api/tools/{hotspot,trending,search,compare};
nginx strips /api/ so FastAPI sees /tools/*.

Reads the live dataset (written by the worker via POST /dataset). When the live
dataset has no locationScores / signalEvents yet, falls back to the static JSON
bundled at build time from frontend/src/generated/.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/tools", tags=["elevenlabs-tools"])

_STATIC_CANDIDATES = [
    Path("/app/static"),
    Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "generated",
]


def _static_file(name: str) -> Path | None:
    for base in _STATIC_CANDIDATES:
        p = base / name
        if p.exists():
            return p
    return None


def _load_json(path: Path | None) -> list:
    if not path:
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _live_dataset() -> dict:
    from app.api.main import load_dataset
    return load_dataset()


def all_locations() -> list[dict]:
    live = _live_dataset().get("locationScores") or []
    if live:
        return live
    return _load_json(_static_file("location-scores.json"))


def all_events() -> list[dict]:
    live = _live_dataset().get("signalEvents") or []
    if live:
        return live
    return _load_json(_static_file("signal-events.json"))


def _norm(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    return s.strip().lower()


def find_location(query: str) -> dict | None:
    q = _norm(query)
    if not q:
        return None
    locs = all_locations()
    for l in locs:
        if _norm(l.get("id")) == q:
            return l
    for l in locs:
        if _norm(l.get("name")) == q:
            return l
    for l in locs:
        name = _norm(l.get("name"))
        if name and (q in name or name in q):
            return l
    return None


def events_within_hours(hours: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
    out = []
    for e in all_events():
        ts = e.get("timestamp") or ""
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if t >= cutoff:
            out.append(e)
    return out


def brief_location(loc: dict | None) -> dict | None:
    if not loc:
        return None
    evidence = []
    for e in (loc.get("evidenceBundle") or [])[:3]:
        cls = e.get("classification") or {}
        evidence.append({
            "title": e.get("title"),
            "excerpt": e.get("excerpt"),
            "url": e.get("url"),
            "source": e.get("sourceName"),
            "timestamp": e.get("timestamp"),
            "signal_type": cls.get("signalType"),
            "drivers": cls.get("drivers"),
        })
    return {
        "id": loc.get("id"),
        "name": loc.get("name"),
        "heat": loc.get("heat"),
        "trend": loc.get("trend"),
        "delta_pct": loc.get("delta"),
        "confidence": loc.get("confidence"),
        "civil_component": loc.get("civilComponent"),
        "military_component": loc.get("militaryComponent"),
        "top_drivers": loc.get("topDrivers"),
        "source_breakdown": loc.get("sourceBreakdown"),
        "evidence": evidence,
    }


async def _body(request: Request) -> dict:
    try:
        b = await request.json()
        return b if isinstance(b, dict) else {}
    except Exception:
        return {}


@router.api_route("/hotspot", methods=["GET", "POST"])
async def hotspot(request: Request):
    location = request.query_params.get("location")
    if not location and request.method == "POST":
        location = (await _body(request)).get("location")
    if not location:
        raise HTTPException(status_code=400, detail="missing 'location' parameter")
    loc = find_location(location)
    if not loc:
        raise HTTPException(status_code=404, detail=f"no hotspot found for '{location}'")
    return {"query": location, "hotspot": brief_location(loc)}


@router.api_route("/trending", methods=["GET", "POST"])
async def trending(request: Request):
    qp = request.query_params
    try:
        top_n = int(qp.get("top_n") or 5)
    except ValueError:
        top_n = 5
    direction = (qp.get("direction") or "warming").lower()
    top_n = max(1, min(top_n, 20))

    locs = all_locations()
    filtered = [l for l in locs if direction == "all" or (l.get("trend") or "").lower() == direction]
    filtered.sort(
        key=lambda a: (float(a.get("delta") or 0), float(a.get("heat") or 0)),
        reverse=True,
    )
    return {
        "direction": direction,
        "top_n": top_n,
        "hotspots": [brief_location(l) for l in filtered[:top_n]],
    }


@router.api_route("/search", methods=["GET", "POST"])
async def search(request: Request):
    qp = request.query_params
    query = qp.get("query")
    hours_raw = qp.get("hours")
    source_family = qp.get("source_family")
    limit_raw = qp.get("limit")

    if request.method == "POST":
        b = await _body(request)
        query = b.get("query", query)
        hours_raw = b.get("hours", hours_raw)
        source_family = b.get("source_family", source_family)
        limit_raw = b.get("limit", limit_raw)

    if not query:
        raise HTTPException(status_code=400, detail="missing 'query' parameter")

    try:
        hours = int(hours_raw) if hours_raw is not None else 24
    except (TypeError, ValueError):
        hours = 24
    try:
        limit = int(limit_raw) if limit_raw is not None else 10
    except (TypeError, ValueError):
        limit = 10
    hours = max(1, min(hours, 168))
    limit = max(1, min(limit, 50))

    q = str(query).lower()
    pool = events_within_hours(hours)
    matches = []
    for e in pool:
        if source_family and (e.get("sourceFamily") or "").lower() != str(source_family).lower():
            continue
        cls = e.get("classification") or {}
        hay = " ".join([
            e.get("title") or "",
            e.get("excerpt") or "",
            " ".join(cls.get("drivers") or []),
            e.get("displayLocationName") or "",
        ]).lower()
        if q in hay:
            matches.append(e)
    matches.sort(key=lambda a: a.get("timestamp") or "", reverse=True)

    def _shape(e: dict) -> dict:
        cls = e.get("classification") or {}
        geo = e.get("geo") or {}
        return {
            "title": e.get("title"),
            "excerpt": e.get("excerpt"),
            "url": e.get("url"),
            "source": e.get("sourceName"),
            "source_family": e.get("sourceFamily"),
            "timestamp": e.get("timestamp"),
            "location": e.get("displayLocationName") or geo.get("name"),
            "signal_type": cls.get("signalType"),
            "drivers": cls.get("drivers"),
        }

    return {
        "query": query,
        "hours": hours,
        "source_family": source_family,
        "total_matches": len(matches),
        "results": [_shape(m) for m in matches[:limit]],
    }


@router.api_route("/compare", methods=["GET", "POST"])
async def compare(request: Request):
    qp = request.query_params
    a = qp.get("a")
    b = qp.get("b")
    if request.method == "POST":
        body = await _body(request)
        a = body.get("a", a)
        b = body.get("b", b)
    if not a or not b:
        raise HTTPException(status_code=400, detail="missing 'a' or 'b' parameter")
    loc_a = find_location(a)
    loc_b = find_location(b)
    if not loc_a or not loc_b:
        raise HTTPException(
            status_code=404,
            detail=f"one or both locations not found (a_found={bool(loc_a)}, b_found={bool(loc_b)})",
        )
    heat_delta = float(loc_a.get("heat") or 0) - float(loc_b.get("heat") or 0)
    if heat_delta > 0:
        hotter = loc_a.get("name")
    elif heat_delta < 0:
        hotter = loc_b.get("name")
    else:
        hotter = "tie"
    return {
        "query": {"a": a, "b": b},
        "verdict": {
            "hotter": hotter,
            "heat_difference": round(heat_delta * 100) / 100,
            "trend_a": loc_a.get("trend"),
            "trend_b": loc_b.get("trend"),
        },
        "a": brief_location(loc_a),
        "b": brief_location(loc_b),
    }
