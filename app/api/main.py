from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root or api/ dir
for _p in [Path(__file__).parent / ".env", Path(__file__).parent.parent.parent / ".env"]:
    if _p.exists():
        load_dotenv(_p)
        break

import hashlib
import json
import logging
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.api.models import NewsRequest, NewsResponse, ArticlesResponse, Article, ScheduleConfig
from app.scrapers.google.fetcher import build_query, fetch_news
from app.api.summarizer import summarize
from app.api.search_catalog import get_searches, add_search, update_search, delete_search

logger = logging.getLogger("osint-api")

app = FastAPI(title="OSINT Watchfloor API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_dataset_dir = Path(os.environ.get("DATASET_DIR", str(Path(__file__).parent)))
_dataset_dir.mkdir(parents=True, exist_ok=True)
DATASET_PATH = _dataset_dir / "dataset.json"

SCHEDULE_PATH = Path(__file__).parent / "schedule.json"
SCORING_CONFIG_PATH = Path(__file__).parent / "scoring_config.json"
LLM_CONFIG_PATH = Path(__file__).parent / "llm_config.json"
_DEFAULT_SCHEDULE = {"enabled": False, "interval_minutes": 60}

DEFAULT_SCORING_CONFIG = {
    "civilMultiplier": 6.4,
    "militaryMultiplier": 6.8,
    "blendCivil": 0.56,
    "blendMilitary": 0.44,
    "recencyDecayHours": 16,
    "corroborationBoost": 0.14,
    "singleSourcePenalty": 0.82,
    "warmingThreshold": 8,
    "coolingThreshold": -5,
    "confidenceFloor": 0.12,
    "confidenceCeiling": 0.97,
    "confidenceBaseWeight": 0.72,
    "confidenceCorrobWeight": 0.08,
}

DEFAULT_LLM_CONFIG = {
    "endpoint": os.environ.get("LLM_ENDPOINT", "https://api.groq.com/openai/v1"),
    "apiKey": os.environ.get("GROQ_API_KEY", ""),
    "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
    "temperature": 0.3,
    "maxTokens": 4096,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_id(source_id: str, title: str) -> str:
    """Generate a stable signal event ID from source + title."""
    raw = f"{source_id}:{title}"
    return "signal-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def load_dataset() -> dict:
    """Read dataset.json if it exists, otherwise return an empty structure."""
    if DATASET_PATH.exists():
        return json.loads(DATASET_PATH.read_text())
    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "sourceCatalog": [],
        "feedCatalog": [],
        "failures": [],
        "sourceStatus": {"rss": "missing", "bluesky": "missing", "news": "missing"},
        "sourceItems": [],
        "signalEvents": [],
        "locationScores": [],
    }


def _read_schedule() -> dict:
    """Read schedule.json, or seed with defaults if missing."""
    if SCHEDULE_PATH.exists():
        return json.loads(SCHEDULE_PATH.read_text())
    _write_schedule(_DEFAULT_SCHEDULE)
    return dict(_DEFAULT_SCHEDULE)


def _write_schedule(cfg: dict) -> None:
    SCHEDULE_PATH.write_text(json.dumps(cfg, indent=2))


# ---------------------------------------------------------------------------
# On-demand query endpoints (not part of the scrape pipeline)
# ---------------------------------------------------------------------------

def _build_description(req: NewsRequest) -> str:
    bits = [f"topics={req.topics}"]
    if req.location:
        bits.append(f"location={req.location}")
    if req.start_date or req.end_date:
        bits.append(f"dates={req.start_date}..{req.end_date}")
    return ", ".join(bits)

async def _fetch(req: NewsRequest) -> tuple[str, list[dict]]:
    query = build_query(req.topics, req.start_date, req.end_date, req.location)
    try:
        articles = await fetch_news(
            query,
            country=req.country,
            language=req.language,
            max_articles=req.max_articles,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"News fetch failed: {e}")
    return query, articles

@app.post("/articles", response_model=ArticlesResponse)
async def get_articles(req: NewsRequest):
    """Fetch and return articles only — no LLM summary."""
    query, articles = await _fetch(req)
    return ArticlesResponse(
        query=query,
        article_count=len(articles),
        articles=[Article(**a) for a in articles],
    )

@app.post("/summarize", response_model=NewsResponse)
async def summarize_news(req: NewsRequest):
    """Fetch articles and return them alongside an LLM summary."""
    query, articles = await _fetch(req)
    summary = await summarize(
        articles,
        request_description=_build_description(req),
        question=req.question,
    )
    return NewsResponse(
        query=query,
        article_count=len(articles),
        articles=[Article(**a) for a in articles],
        summary=summary,
    )

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Dataset endpoints
# ---------------------------------------------------------------------------

@app.get("/dataset")
async def get_dataset():
    """Serve the current dataset for the frontend."""
    return load_dataset()


@app.post("/dataset")
async def receive_dataset(payload: dict):
    """Receive a completed dataset from the worker and persist it."""
    DATASET_PATH.write_text(json.dumps(payload, indent=2, default=str))
    return {
        "status": "accepted",
        "signalCount": len(payload.get("signalEvents", [])),
        "sourceCount": len(payload.get("sourceCatalog", [])),
    }


@app.post("/refresh")
async def trigger_refresh():
    """Signal the worker to refresh on its next cycle.

    Sets a pending_refresh flag in schedule.json that the worker checks.
    """
    schedule = _read_schedule()
    schedule["pending_refresh"] = True
    _write_schedule(schedule)
    return {"status": "pending", "message": "Refresh requested. Worker will pick it up on next cycle."}


# ---------------------------------------------------------------------------
# Search CRUD endpoints
# ---------------------------------------------------------------------------

@app.get("/searches")
async def list_searches():
    """Return all configured searches."""
    return get_searches()


@app.post("/searches", status_code=201)
async def create_search(body: dict):
    """Add a new search configuration."""
    if "id" not in body and "label" in body:
        slug = body["label"].lower().replace(" ", "-")
        body["id"] = f"news-{slug}"
    return add_search(body)


@app.put("/searches/{search_id}")
async def modify_search(search_id: str, body: dict):
    """Update fields on an existing search."""
    result = update_search(search_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Search '{search_id}' not found")
    return result


@app.delete("/searches/{search_id}")
async def remove_search(search_id: str):
    """Delete a search by ID."""
    if not delete_search(search_id):
        raise HTTPException(status_code=404, detail=f"Search '{search_id}' not found")
    return {"deleted": search_id}


# ---------------------------------------------------------------------------
# Schedule endpoints
# ---------------------------------------------------------------------------

@app.get("/schedule")
async def get_schedule():
    """Return the current refresh schedule. Worker polls this."""
    return _read_schedule()


@app.put("/schedule")
async def set_schedule(body: ScheduleConfig):
    """Update the refresh schedule. Worker picks up changes on next poll."""
    cfg = body.model_dump()
    _write_schedule(cfg)
    return cfg


# ---------------------------------------------------------------------------
# Scoring config endpoints
# ---------------------------------------------------------------------------

def _read_scoring_config() -> dict:
    if SCORING_CONFIG_PATH.exists():
        stored = json.loads(SCORING_CONFIG_PATH.read_text())
        return {**DEFAULT_SCORING_CONFIG, **stored}
    return dict(DEFAULT_SCORING_CONFIG)

def _write_scoring_config(cfg: dict) -> None:
    SCORING_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

@app.get("/config/scoring")
async def get_scoring_config():
    return _read_scoring_config()

@app.put("/config/scoring")
async def set_scoring_config(body: dict):
    merged = {**DEFAULT_SCORING_CONFIG, **body}
    _write_scoring_config(merged)
    return merged

@app.post("/config/scoring/reset")
async def reset_scoring_config():
    cfg = dict(DEFAULT_SCORING_CONFIG)
    _write_scoring_config(cfg)
    return cfg


# ---------------------------------------------------------------------------
# LLM config endpoints — configurable AI provider/model/key
# ---------------------------------------------------------------------------

def _read_llm_config() -> dict:
    if LLM_CONFIG_PATH.exists():
        stored = json.loads(LLM_CONFIG_PATH.read_text())
        return {**DEFAULT_LLM_CONFIG, **stored}
    return dict(DEFAULT_LLM_CONFIG)

def _write_llm_config(cfg: dict) -> None:
    # Mask the API key in the saved file for security — store it but don't log it
    LLM_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

@app.get("/config/llm")
async def get_llm_config():
    """Return LLM config. API key is masked in response."""
    cfg = _read_llm_config()
    # Mask key for safe display
    key = cfg.get("apiKey", "")
    if key and len(key) > 10:
        cfg["apiKeyMasked"] = key[:6] + "..." + key[-4:]
    elif key:
        cfg["apiKeyMasked"] = "***"
    else:
        cfg["apiKeyMasked"] = ""
    return cfg

@app.put("/config/llm")
async def set_llm_config(body: dict):
    """Update LLM config. If apiKey is not provided, keep the existing one."""
    current = _read_llm_config()
    # Don't overwrite key if not provided or empty
    if not body.get("apiKey"):
        body["apiKey"] = current.get("apiKey", "")
    merged = {**DEFAULT_LLM_CONFIG, **body}
    _write_llm_config(merged)
    return {"status": "saved"}

@app.post("/config/llm/reset")
async def reset_llm_config():
    cfg = dict(DEFAULT_LLM_CONFIG)
    _write_llm_config(cfg)
    return cfg
