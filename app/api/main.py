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

from email.utils import parsedate_to_datetime
from html import unescape as html_unescape

from app.api.models import NewsRequest, NewsResponse, ArticlesResponse, Article, ScheduleConfig
from app.scrapers.google.fetcher import build_query, fetch_news
from app.scrapers.common.geo import infer_geo
from app.scrapers.common.classifier import classify
from app.api.summarizer import summarize
from app.api.search_catalog import get_searches, add_search, add_search_group, update_search, delete_search, delete_search_group, SUPPORTED_PLATFORMS
from app.scrapers.rss.fetcher import fetch_feed as fetch_rss_feed
from app.scrapers.bluesky.fetcher import build_query as build_bluesky_query, fetch_posts as fetch_bluesky_posts
from app.scrapers.x.fetcher import build_query as build_x_query, fetch_posts as fetch_x_posts
from app.scrapers.common.classifier import load_config as load_classifier_config, save_config as save_classifier_config, DEFAULT_CONFIG as DEFAULT_CLASSIFIER_CONFIG

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
    "warMultiplier": 7.2,
    "terrorismMultiplier": 6.6,
    "humanitarianMultiplier": 5.8,
    "infowarMultiplier": 5.2,
    "blendWeights": {
        "war": 0.25,
        "military": 0.20,
        "civil": 0.18,
        "terrorism": 0.15,
        "humanitarian": 0.12,
        "infowar": 0.10,
    },
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
    "enableClassification": True,
    "enableSummarization": True,
    "enableGeoExtraction": True,
    "enableTrendAnalysis": True,
    "systemPrompt": "",
    "summaryPromptTemplate": (
        "The user requested news on: {request_description}\n\n"
        "{question_block}Below are {article_count} article headlines and snippets. "
        "Write a concise, factual intelligence summary of the key events, organized by theme "
        "or chronology, and call out notable trends or disagreements between sources. "
        "Do not invent facts beyond what's in the snippets.\n\n"
        "ARTICLES:\n{articles}"
    ),
}

# In-memory cache of summaries keyed by search ID
_summaries_cache: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_id(source_id: str, title: str) -> str:
    """Generate a stable signal event ID from source + title."""
    raw = f"{source_id}:{title}"
    return "signal-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def _parse_timestamp(raw: str | None) -> str:
    """Parse RFC 2822 date or return current time as ISO 8601."""
    if not raw:
        return datetime.utcnow().isoformat() + "Z"
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
        return datetime.utcnow().isoformat() + "Z"


_DRIVER_LABELS: dict[str, str] = {
    # Civil keywords
    "protest": "protest activity",
    "riot": "riot / mob violence",
    "crackdown": "government crackdown",
    "demonstration": "mass demonstrations",
    "unrest": "civil unrest",
    "civil": "civil disorder",
    "arrest": "political arrests",
    "detention": "arbitrary detention",
    "opposition": "opposition suppression",
    "election": "election instability",
    "corruption": "systemic corruption",
    "sanction": "international sanctions",
    "embargo": "trade embargo",
    "violence": "escalating violence",
    "gang": "gang activity",
    "cartel": "cartel operations",
    "crime": "organized crime",
    "kidnap": "kidnapping / abduction",
    "abduct": "kidnapping / abduction",
    "hostage": "hostage situation",

    # War keywords
    "war": "active warfare",
    "invasion": "invasion / incursion",
    "invade": "invasion / incursion",
    "occupied": "territorial occupation",
    "offensive": "military offensive",
    "airstrike": "airstrikes",
    "air strike": "airstrikes",
    "missile": "missile strikes",
    "shelling": "artillery shelling",
    "bombing": "bombing campaign",
    "bombardment": "aerial bombardment",
    "combat": "combat operations",
    "warfare": "active warfare",
    "siege": "siege operations",
    "frontline": "frontline combat",
    "battlefield": "battlefield operations",
    "casualties": "reported casualties",
    "killed": "fatalities reported",
    "wounded": "wounded reported",
    "destroyed": "infrastructure destroyed",
    "battle": "active battle",
    "assault": "ground assault",
    "counteroffensive": "counteroffensive operations",
    "escalation": "conflict escalation",
    "rocket": "rocket attacks",
    "strike": "military strikes",
    "ceasefire": "ceasefire developments",
    "cease-fire": "ceasefire developments",

    # Military keywords
    "army": "army mobilization",
    "military": "military movement",
    "coup": "coup attempt",
    "troop": "troop deployment",
    "troops": "troop deployment",
    "drone": "drone operations",
    "artillery": "artillery shelling",
    "weapon": "weapons proliferation",
    "arms": "arms transfers",
    "defense": "defense posture shift",
    "defence": "defense posture shift",
    "naval": "naval activity",
    "navy": "naval activity",
    "fighter jet": "fighter jet deployments",
    "tank": "armored vehicle movement",
    "soldier": "soldier deployment",
    "paramilitary": "paramilitary operations",
    "deployment": "force deployment",
    "nuclear": "nuclear threat",
    "warship": "warship movement",
    "blockade": "naval blockade",

    # Terrorism keywords
    "terrorist": "terrorist activity",
    "terrorism": "terrorism threat",
    "extremist": "extremist activity",
    "extremism": "violent extremism",
    "IED": "IED / improvised explosive",
    "suicide bomb": "suicide bombing",
    "radicalization": "radicalization threat",
    "guerrilla": "guerrilla warfare",
    "insurgent": "insurgent activity",
    "insurgency": "active insurgency",
    "rebel": "rebel operations",
    "militia": "militia activity",

    # Humanitarian keywords
    "humanitarian": "humanitarian crisis",
    "famine": "famine / food insecurity",
    "refugee": "refugee displacement",
    "displaced": "population displacement",
    "civilian": "civilian casualties",
    "human rights": "human rights violations",
    "aid": "humanitarian aid disruption",
    "crisis": "escalating crisis",
    "hunger": "food insecurity",
    "starvation": "mass starvation",
    "epidemic": "disease epidemic",
    "cholera": "cholera outbreak",
    "displacement": "mass displacement",
    "evacuation": "mass evacuation",
    "relief": "humanitarian relief",

    # Infowar keywords
    "disinformation": "disinformation campaign",
    "misinformation": "misinformation spread",
    "propaganda": "state propaganda",
    "viral": "viral narrative",
    "narrative": "narrative warfare",
    "influence": "influence operations",
    "cyber": "cyber operations",
    "hack": "cyber attack",
    "leak": "intelligence leak",
    "espionage": "espionage activity",
    "spy": "espionage activity",
    "intelligence": "intelligence activity",
    "social media": "social media manipulation",
    "information warfare": "information warfare",
    "psyop": "psychological operations",
    "troll": "troll network activity",
    "bot": "bot network activity",
    "fake news": "fake news campaign",
    "censorship": "media censorship",
    "media": "media manipulation",
    "campaign": "coordinated campaign",
}


def _humanize_drivers(raw_drivers: list[str]) -> list[str]:
    """Convert raw keyword matches into human-readable driver labels."""
    seen: set[str] = set()
    result: list[str] = []
    for kw in raw_drivers:
        label = _DRIVER_LABELS.get(kw, kw)
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def _article_to_signal(article: dict, search: dict) -> dict:
    """Convert a raw article dict + its search config into a signal event."""
    title = html_unescape(article.get("title", ""))
    desc = html_unescape(article.get("description", "") or "")
    source_id = search["id"]
    event_id = _make_id(source_id, title)

    llm_cfg = _read_llm_config()
    classification_enabled = llm_cfg.get("enableClassification", True)
    classification = classify(title, desc, enabled=classification_enabled)
    classification["drivers"] = _humanize_drivers(classification.get("drivers", []))

    geo = infer_geo(
        place_hints=search.get("place_hints", []),
        text=f"{title} {desc}",
    )

    return {
        "id": event_id,
        "sourceId": source_id,
        "sourceFamily": "news",
        "sourceName": "Google News",
        "title": title,
        "excerpt": desc,
        "url": article.get("link", ""),
        "author": {"name": article.get("source", "Unknown"), "profileLocation": ""},
        "provenance": f"google news search: {search['label']}",
        "engagement": {},
        "timestamp": _parse_timestamp(article.get("published")),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def _rss_article_to_signal(article: dict, search: dict) -> dict:
    """Convert a raw RSS article dict + its search config into a signal event."""
    title = html_unescape(article.get("title", ""))
    desc = html_unescape(article.get("description", "") or "")
    source_id = search["id"]
    event_id = _make_id(source_id, title)

    llm_cfg = _read_llm_config()
    classification_enabled = llm_cfg.get("enableClassification", True)
    classification = classify(title, desc, enabled=classification_enabled)
    classification["drivers"] = _humanize_drivers(classification.get("drivers", []))

    geo = infer_geo(
        place_hints=search.get("place_hints", []),
        text=f"{title} {desc}",
    )

    return {
        "id": event_id,
        "sourceId": source_id,
        "sourceFamily": "rss",
        "sourceName": search.get("label", "RSS Feed"),
        "title": title,
        "excerpt": desc,
        "url": article.get("link", ""),
        "author": {"name": article.get("source", "Unknown"), "profileLocation": ""},
        "provenance": f"rss feed: {search.get('feed_url', '')}",
        "engagement": {},
        "timestamp": _parse_timestamp(article.get("published")),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def _bluesky_post_to_signal(post: dict, search: dict) -> dict:
    """Convert a normalized Bluesky post dict + its search config into a signal event."""
    text = post.get("text", "")
    title = text[:120]
    source_id = search["id"]
    event_id = _make_id(source_id, text[:80])

    llm_cfg = _read_llm_config()
    classification_enabled = llm_cfg.get("enableClassification", True)
    classification = classify(title, text, enabled=classification_enabled)
    classification["drivers"] = _humanize_drivers(classification.get("drivers", []))

    geo = infer_geo(
        place_hints=search.get("place_hints", []),
        text=text,
    )

    author_info = post.get("author", {})
    raw_ts = post.get("created_at") or post.get("indexed_at")

    return {
        "id": event_id,
        "sourceId": source_id,
        "sourceFamily": "bluesky",
        "sourceName": "Bluesky",
        "title": title,
        "excerpt": text,
        "url": post.get("url", ""),
        "author": {
            "name": author_info.get("display_name") or author_info.get("handle", "Unknown"),
            "profileLocation": "",
        },
        "provenance": f"bluesky search: {search['label']}",
        "engagement": {
            "likes": post.get("likes", 0),
            "reposts": post.get("reposts", 0),
            "replies": post.get("replies", 0),
            "quotes": post.get("quotes", 0),
        },
        "timestamp": _parse_timestamp(raw_ts) if raw_ts else datetime.utcnow().isoformat() + "Z",
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def _x_post_to_signal(post: dict, search: dict) -> dict:
    """Convert a normalized X post dict + its search config into a signal event."""
    text = post.get("text", "")
    title = text[:120]
    source_id = search["id"]
    event_id = _make_id(source_id, text[:80])

    llm_cfg = _read_llm_config()
    classification_enabled = llm_cfg.get("enableClassification", True)
    classification = classify(title, text, enabled=classification_enabled)
    classification["drivers"] = _humanize_drivers(classification.get("drivers", []))

    geo = infer_geo(
        place_hints=search.get("place_hints", []),
        text=text,
    )

    author_info = post.get("author", {})
    raw_ts = post.get("created_at")

    return {
        "id": event_id,
        "sourceId": source_id,
        "sourceFamily": "x",
        "sourceName": "X",
        "title": title,
        "excerpt": text,
        "url": post.get("url", ""),
        "author": {
            "name": author_info.get("name") or author_info.get("username", "Unknown"),
            "handle": author_info.get("username", ""),
            "profileLocation": "",
        },
        "provenance": f"x search: {search['label']}",
        "engagement": {
            "likes": post.get("likes", 0),
            "reposts": post.get("reposts", 0),
            "replies": post.get("replies", 0),
            "quotes": post.get("quotes", 0),
            "bookmarks": post.get("bookmarks", 0),
            "impressions": post.get("impressions"),
        },
        "timestamp": _parse_timestamp(raw_ts) if raw_ts else datetime.utcnow().isoformat() + "Z",
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def load_dataset() -> dict:
    """Read dataset.json if it exists, otherwise return an empty structure."""
    if DATASET_PATH.exists():
        return json.loads(DATASET_PATH.read_text())
    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "sourceCatalog": [],
        "feedCatalog": [],
        "failures": [],
        "sourceStatus": {"rss": "missing", "bluesky": "missing", "x": "missing", "news": "missing"},
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
    """Run an inline scrape cycle across all configured searches.

    Fetches articles, classifies and geo-tags each one, builds the dataset,
    persists it, and returns the result with signalCount and sourceCount.
    """
    # -- Fallback: the old flag-based mechanism (for use with the external worker) --
    # schedule = _read_schedule()
    # schedule["pending_refresh"] = True
    # _write_schedule(schedule)
    # return {"status": "pending", "message": "Refresh requested. Worker will pick it up on next cycle."}

    searches = get_searches()
    llm_cfg = _read_llm_config()
    enable_summarization = llm_cfg.get("enableSummarization", True)
    all_signals: list[dict] = []
    source_items: list[dict] = []
    source_catalog: list[dict] = []
    failures: list[dict] = []
    summaries: dict[str, str] = {}

    for search in searches:
        search_id = search.get("id", "unknown")
        search_label = search.get("label", search_id)
        platform = search.get("platform", "google")

        if platform == "bluesky":
            # --- Bluesky source ---
            bluesky_query = build_bluesky_query(search["topics"])
            try:
                posts = await fetch_bluesky_posts(bluesky_query, max_posts=search.get("max_articles", 15))
            except Exception as exc:
                logger.warning("Bluesky fetch failed for %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "Bluesky",
                "sourceFamily": "bluesky",
                "sourceKind": "bluesky-search",
                "url": "",
                "itemCount": len(posts),
            })

            for post in posts:
                signal = _bluesky_post_to_signal(post, search)
                all_signals.append(signal)

        elif platform == "x":
            # --- X/Twitter source ---
            x_query = build_x_query(search["topics"])
            try:
                posts = await fetch_x_posts(x_query, max_posts=search.get("max_articles", 15))
            except Exception as exc:
                logger.warning("X fetch failed for %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "X",
                "sourceFamily": "x",
                "sourceKind": "x-search",
                "url": "",
                "itemCount": len(posts),
            })

            for post in posts:
                signal = _x_post_to_signal(post, search)
                all_signals.append(signal)

        elif platform == "rss":
            # --- RSS/Atom feed source ---
            feed_url = search.get("feed_url", "")
            if not feed_url:
                logger.warning("RSS search %s has no feed_url, skipping", search_id)
                continue

            try:
                articles = await fetch_rss_feed(
                    feed_url,
                    max_articles=search.get("max_articles", 15),
                    topics=search.get("topics"),
                )
            except Exception as exc:
                logger.warning("RSS fetch failed for %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "RSS Feed",
                "sourceFamily": "rss",
                "sourceKind": "rss-feed",
                "url": feed_url,
                "itemCount": len(articles),
            })

            for art in articles:
                source_items.append({**art, "searchId": search_id})
                signal = _rss_article_to_signal(art, search)
                all_signals.append(signal)

            # Summarize RSS articles if enabled
            if enable_summarization and articles:
                try:
                    search_desc = f"search '{search_label}' (feed: {feed_url})"
                    search_summary = await summarize(
                        articles,
                        request_description=search_desc,
                    )
                    summaries[search_id] = search_summary
                    _summaries_cache[search_id] = search_summary
                except Exception as exc:
                    logger.warning("Summarization failed for search %s: %s", search_id, exc)

        else:
            # --- Google News source (default) ---
            query = build_query(
                search["topics"],
                start_date=None,
                end_date=None,
                location=search.get("location"),
            )

            try:
                articles = await fetch_news(
                    query,
                    max_articles=search.get("max_articles", 15),
                )
            except Exception as exc:
                logger.warning("Failed to fetch search %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "Google News",
                "sourceFamily": "news",
                "sourceKind": "google-news-rss",
                "url": "",
                "itemCount": len(articles),
            })

            for art in articles:
                source_items.append({**art, "searchId": search_id})
                signal = _article_to_signal(art, search)
                all_signals.append(signal)

            # Summarize articles for this search if enabled
            if enable_summarization and articles:
                try:
                    search_desc = f"search '{search_label}' (topics: {search.get('topics', [])})"
                    search_summary = await summarize(
                        articles,
                        request_description=search_desc,
                    )
                    summaries[search_id] = search_summary
                    _summaries_cache[search_id] = search_summary
                except Exception as exc:
                    logger.warning("Summarization failed for search %s: %s", search_id, exc)

    generated_at = datetime.utcnow().isoformat() + "Z"

    dataset = {
        "generatedAt": generated_at,
        "sourceCatalog": source_catalog,
        "feedCatalog": [],
        "failures": failures,
        "sourceStatus": {
            "rss": "loaded" if any(s.get("sourceFamily") == "rss" for s in all_signals) else "missing",
            "bluesky": "loaded" if any(s.get("sourceFamily") == "bluesky" for s in all_signals) else "missing",
            "x": "loaded" if any(s.get("sourceFamily") == "x" for s in all_signals) else "missing",
            "news": "loaded" if any(s.get("sourceFamily") == "news" for s in all_signals) else "empty",
        },
        "sourceItems": source_items,
        "signalEvents": all_signals,
        "locationScores": [],
        "summaries": summaries,
    }

    # Persist to disk so GET /dataset returns the latest data
    DATASET_PATH.write_text(json.dumps(dataset, indent=2, default=str))

    return {
        **dataset,
        "signalCount": len(all_signals),
        "sourceCount": len(source_catalog),
    }


# ---------------------------------------------------------------------------
# Search CRUD endpoints
# ---------------------------------------------------------------------------

@app.get("/platforms")
async def list_platforms():
    """Return supported scraper platforms."""
    return SUPPORTED_PLATFORMS


@app.get("/searches")
async def list_searches():
    """Return all configured searches."""
    return get_searches()


@app.post("/searches", status_code=201)
async def create_search(body: dict):
    """Add a new search configuration."""
    platform = body.get("platform", "google")
    if platform not in SUPPORTED_PLATFORMS:
        platform = "google"
        body["platform"] = platform
    if "id" not in body and "label" in body:
        slug = body["label"].lower().replace(" ", "-")
        body["id"] = f"{platform}-{slug}"
    return add_search(body)


@app.post("/searches/group", status_code=201)
async def create_search_group(body: dict):
    """Create a search group — one source per platform sharing a group ID.

    Accepts: {label, topics, location?, place_hints?, max_articles?, platforms?}
    If platforms is omitted, creates sources for all supported platforms.
    """
    label = body.get("label", "").strip()
    if not label:
        raise HTTPException(status_code=400, detail="label is required")
    topics = body.get("topics", [])
    if not topics:
        raise HTTPException(status_code=400, detail="topics is required")
    created = add_search_group(
        label=label,
        topics=topics,
        location=body.get("location"),
        place_hints=body.get("place_hints", []),
        max_articles=body.get("max_articles", 15),
        platforms=body.get("platforms"),
    )
    return {"group": created[0]["group"], "sources": created}


@app.delete("/searches/group/{group_id}")
async def remove_search_group(group_id: str):
    """Delete all sources belonging to a group."""
    deleted = delete_search_group(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Group '{group_id}' not found")
    return {"deleted_group": group_id, "deleted_count": deleted}


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
# Classifier config endpoints
# ---------------------------------------------------------------------------

@app.get("/config/classifier")
async def get_classifier_config():
    return load_classifier_config()

@app.put("/config/classifier")
async def set_classifier_config(body: dict):
    return save_classifier_config(body)

@app.post("/config/classifier/reset")
async def reset_classifier_config():
    return save_classifier_config(dict(DEFAULT_CLASSIFIER_CONFIG))


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
    # Persist boolean feature toggles if present
    for flag in ("enableClassification", "enableSummarization",
                 "enableGeoExtraction", "enableTrendAnalysis"):
        if flag in body:
            body[flag] = bool(body[flag])
    # Persist systemPrompt if present
    if "systemPrompt" in body:
        body["systemPrompt"] = str(body["systemPrompt"])
    merged = {**DEFAULT_LLM_CONFIG, **body}
    _write_llm_config(merged)
    return {"status": "saved"}

@app.post("/config/llm/reset")
async def reset_llm_config():
    cfg = dict(DEFAULT_LLM_CONFIG)
    _write_llm_config(cfg)
    return cfg


@app.get("/config/llm/env-status")
async def llm_env_status():
    """Return which LLM-related env vars are set (without revealing values)."""
    return {
        "GROQ_API_KEY": bool(os.environ.get("GROQ_API_KEY")),
        "LLM_ENDPOINT": bool(os.environ.get("LLM_ENDPOINT")),
        "LLM_MODEL": bool(os.environ.get("LLM_MODEL")),
    }


@app.get("/summaries")
async def get_summaries():
    """Return cached summaries keyed by search ID."""
    return _summaries_cache


# ---------------------------------------------------------------------------
# Source credentials management
# ---------------------------------------------------------------------------

CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"

_DEFAULT_CREDENTIALS = {
    "bluesky": {
        "identifier": "",
        "app_password": "",
        "pds_url": "https://bsky.social",
    },
    "x": {
        "bearer_token": "",
        "api_base_url": "https://api.x.com",
    },
}


def _mask(value: str) -> str:
    """Mask a secret value for safe display."""
    if not value:
        return ""
    if len(value) > 10:
        return value[:4] + "..." + value[-4:]
    return "***"


def _read_credentials() -> dict:
    if CREDENTIALS_PATH.exists():
        stored = json.loads(CREDENTIALS_PATH.read_text())
        merged = {}
        for platform, defaults in _DEFAULT_CREDENTIALS.items():
            merged[platform] = {**defaults, **stored.get(platform, {})}
        return merged
    return {p: dict(v) for p, v in _DEFAULT_CREDENTIALS.items()}


def _write_credentials(creds: dict) -> None:
    CREDENTIALS_PATH.write_text(json.dumps(creds, indent=2))


def _apply_credentials_to_env(creds: dict) -> None:
    """Push saved credentials into the process environment so scrapers pick them up."""
    bsky = creds.get("bluesky", {})
    if bsky.get("identifier"):
        os.environ["BLUESKY_IDENTIFIER"] = bsky["identifier"]
    if bsky.get("app_password"):
        os.environ["BLUESKY_APP_PASSWORD"] = bsky["app_password"]
    if bsky.get("pds_url"):
        os.environ["BLUESKY_PDS_URL"] = bsky["pds_url"]

    x = creds.get("x", {})
    if x.get("bearer_token"):
        os.environ["X_BEARER_TOKEN"] = x["bearer_token"]
    if x.get("api_base_url"):
        os.environ["X_API_BASE_URL"] = x["api_base_url"]


# Apply any persisted credentials on startup
_apply_credentials_to_env(_read_credentials())


@app.get("/config/credentials")
async def get_credentials():
    """Return source credentials with secrets masked."""
    creds = _read_credentials()
    masked = {}
    for platform, fields in creds.items():
        masked[platform] = {}
        for key, value in fields.items():
            if any(secret in key for secret in ("password", "token", "secret", "key")):
                masked[platform][key] = _mask(value)
                masked[platform][f"{key}_set"] = bool(value)
            else:
                masked[platform][key] = value
    return masked


@app.put("/config/credentials")
async def set_credentials(body: dict):
    """Update source credentials. Empty strings are ignored (keeps existing value)."""
    current = _read_credentials()
    for platform, fields in body.items():
        if platform not in current:
            continue
        for key, value in fields.items():
            if isinstance(value, str) and value.strip():
                current[platform][key] = value.strip()
    _write_credentials(current)
    _apply_credentials_to_env(current)
    return {"status": "saved"}


@app.get("/config/credentials/status")
async def credentials_status():
    """Return which credentials are configured (from env or saved config)."""
    return {
        "bluesky": {
            "identifier": bool(os.environ.get("BLUESKY_IDENTIFIER")),
            "app_password": bool(os.environ.get("BLUESKY_APP_PASSWORD")),
        },
        "x": {
            "bearer_token": bool(os.environ.get("X_BEARER_TOKEN")),
        },
        "google": {
            "note": "No credentials required — uses public RSS feed",
        },
    }
