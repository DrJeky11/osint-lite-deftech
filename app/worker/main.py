"""Standalone scraper worker for the OSINT system.

Pulls search config from the API, scrapes Google News, classifies and
geo-tags each article, then POSTs the assembled dataset back to the API.

Usage:
    API_BASE_URL=http://localhost:8000 python -m app.worker.main
"""

import asyncio
import hashlib
import logging
import math
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from app.scrapers.rss.fetcher import fetch_feed as fetch_rss_feed
from app.scrapers.bluesky.fetcher import build_query as build_bluesky_query, fetch_posts as fetch_bluesky_posts
from app.scrapers.x.fetcher import build_query as build_x_query, fetch_posts as fetch_x_posts
from app.scrapers.common.classifier import classify
from app.scrapers.common.geo import infer_geo
from app.scrapers.google.fetcher import build_query, fetch_news

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("worker")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_id(source_id: str, title: str) -> str:
    """Generate a stable signal event ID from source + title."""
    raw = f"{source_id}:{title}"
    return "signal-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def parse_timestamp(raw: str | None) -> str:
    """Parse RFC 2822 or ISO 8601 date, or return current time as ISO 8601."""
    if not raw:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        # Try ISO 8601 first (Bluesky uses this format)
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            # Fall back to RFC 2822 (Google News)
            dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Driver label mapping — turn raw keywords into human-readable labels
# ---------------------------------------------------------------------------

_DRIVER_LABELS: dict[str, str] = {
    "protest": "protest activity",
    "riot": "riot / mob violence",
    "crackdown": "government crackdown",
    "demonstration": "mass demonstrations",
    "unrest": "civil unrest",
    "civil": "civil disorder",
    "humanitarian": "humanitarian crisis",
    "famine": "famine / food insecurity",
    "refugee": "refugee displacement",
    "displaced": "population displacement",
    "civilian": "civilian casualties",
    "human rights": "human rights violations",
    "arrest": "political arrests",
    "detention": "arbitrary detention",
    "opposition": "opposition suppression",
    "election": "election instability",
    "corruption": "systemic corruption",
    "sanction": "international sanctions",
    "embargo": "trade embargo",
    "aid": "humanitarian aid disruption",
    "crisis": "escalating crisis",
    "violence": "escalating violence",
    "gang": "gang activity",
    "cartel": "cartel operations",
    "crime": "organized crime",
    "kidnap": "kidnapping / abduction",
    "abduct": "kidnapping / abduction",
    "hostage": "hostage situation",
    "army": "army mobilization",
    "military": "military movement",
    "coup": "coup attempt",
    "troop": "troop deployment",
    "troops": "troop deployment",
    "airstrike": "airstrikes",
    "air strike": "airstrikes",
    "missile": "missile strikes",
    "drone": "drone operations",
    "bombing": "bombing campaign",
    "shelling": "artillery shelling",
    "offensive": "military offensive",
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
    "militia": "militia activity",
    "paramilitary": "paramilitary operations",
    "insurgent": "insurgent activity",
    "insurgency": "active insurgency",
    "rebel": "rebel operations",
    "warfare": "active warfare",
    "combat": "combat operations",
    "deployment": "force deployment",
    "invasion": "invasion / incursion",
    "occupation": "territorial occupation",
    "ceasefire": "ceasefire developments",
    "cease-fire": "ceasefire developments",
    "nuclear": "nuclear threat",
    "warship": "warship movement",
    "blockade": "naval blockade",
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
    # War keywords (expanded)
    "drone strike": "drone strike",
    "drone attack": "drone attack",
    "ballistic missile": "ballistic missile launch",
    "cruise missile": "cruise missile strike",
    "missile attack": "missile attack",
    "missile strike": "missile strike",
    "naval blockade": "naval blockade",
    "strait closure": "strait closure",
    "military retaliation": "military retaliation",
    "retaliatory strike": "retaliatory strike",
    "military operation": "military operation",
    "kinetic strike": "kinetic strike",
    "infrastructure strike": "infrastructure strike",
    "troop mobilization": "troop mobilization",
    "army mobilization": "army mobilization",
    "military buildup": "military buildup",
    # Military keywords (expanded)
    "drone swarm": "drone swarm",
    "unmanned aircraft": "unmanned aircraft operations",
    "air defense": "air defense activation",
    "interceptor": "interceptor deployment",
    "naval deployment": "naval deployment",
    "fleet deployment": "fleet deployment",
    "combat readiness": "combat readiness",
    "military drill": "military drill",
    "military exercise": "military exercise",
    # Civil keywords (expanded)
    "martial law": "martial law",
    "curfew": "curfew imposed",
    "state of emergency": "state of emergency",
    # Terrorism keywords (expanded)
    "car bomb": "car bomb attack",
    "suicide attack": "suicide attack",
    "mass shooting": "mass shooting",
    "lone wolf": "lone wolf attack",
    "terrorist attack": "terrorist attack",
    "bombing attack": "bombing attack",
    # Humanitarian keywords (expanded)
    "war crime": "war crimes",
    "ethnic cleansing": "ethnic cleansing",
    "genocide": "genocide",
    "mass grave": "mass grave discovered",
    "civilian casualties": "civilian casualties",
    "infrastructure destroyed": "infrastructure destroyed",
    # Narrative keywords (expanded)
    "cyber attack": "cyber attack",
    "cyberwarfare": "cyberwarfare",
    "electronic warfare": "electronic warfare",
    "deepfake": "deepfake campaign",
}


def humanize_drivers(raw_drivers: list[str]) -> list[str]:
    """Convert raw keyword matches into human-readable driver labels.

    Deduplicates labels (e.g. 'kidnap' and 'abduct' both map to the same
    label) and preserves order of first occurrence.
    """
    seen: set[str] = set()
    result: list[str] = []
    for kw in raw_drivers:
        label = _DRIVER_LABELS.get(kw, kw)
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def article_to_signal(article: dict, search: dict) -> dict:
    """Convert a raw article dict + its search config into a signal event."""
    title = article.get("title", "")
    desc = article.get("description", "") or ""
    source_id = search["id"]
    event_id = make_id(source_id, title)

    classification = classify(title, desc)
    # Humanize driver labels for frontend display
    classification["drivers"] = humanize_drivers(classification.get("drivers", []))

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
        "timestamp": parse_timestamp(article.get("published")),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def bluesky_post_to_signal(post: dict, search: dict) -> dict:
    """Convert a normalized Bluesky post dict + its search config into a signal event."""
    text = post.get("text", "")
    title = text[:120]
    source_id = search["id"]
    event_id = make_id(source_id, text[:80])

    classification = classify(title, text)
    classification["drivers"] = humanize_drivers(classification.get("drivers", []))

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
        "timestamp": parse_timestamp(raw_ts),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def rss_article_to_signal(article: dict, search: dict) -> dict:
    """Convert a raw RSS article dict + its search config into a signal event."""
    title = article.get("title", "")
    desc = article.get("description", "") or ""
    source_id = search["id"]
    event_id = make_id(source_id, title)

    classification = classify(title, desc)
    classification["drivers"] = humanize_drivers(classification.get("drivers", []))

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
        "timestamp": parse_timestamp(article.get("published")),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def x_post_to_signal(post: dict, search: dict) -> dict:
    """Convert a normalized X/Twitter post dict + its search config into a signal event."""
    text = post.get("text", "")
    title = text[:120]
    source_id = search["id"]
    event_id = make_id(source_id, text[:80])

    classification = classify(title, text)
    classification["drivers"] = humanize_drivers(classification.get("drivers", []))

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
        "sourceName": "X / Twitter",
        "title": title,
        "excerpt": text,
        "url": post.get("url", ""),
        "author": {
            "name": author_info.get("name") or author_info.get("username", "Unknown"),
            "profileLocation": "",
        },
        "provenance": f"x search: {search['label']}",
        "engagement": {
            "likes": post.get("likes", 0),
            "reposts": post.get("reposts", 0),
            "replies": post.get("replies", 0),
            "quotes": post.get("quotes", 0),
        },
        "timestamp": parse_timestamp(raw_ts),
        "geo": geo,
        "classification": classification,
        "corroborationCount": 1,
    }


def _classify_wgi_dimension(obs: dict) -> dict:
    """Map a WGI governance dimension to signal classification weights.

    Low governance scores (high risk_level) produce higher threat weights,
    distributed across categories based on which dimension is being measured.
    """
    dimension = obs.get("dimension", "")
    value = obs.get("value", 50)

    # Low governance scores indicate risk
    risk_level = max(0, (100 - value) / 100)

    mapping = {
        "voice_accountability": {"civilWeight": risk_level * 0.7, "narrativeWeight": risk_level * 0.3},
        "political_stability": {"warWeight": risk_level * 0.5, "civilWeight": risk_level * 0.3, "terrorismWeight": risk_level * 0.2},
        "government_effectiveness": {"civilWeight": risk_level * 0.8, "humanitarianWeight": risk_level * 0.2},
        "regulatory_quality": {"civilWeight": risk_level * 0.6, "narrativeWeight": risk_level * 0.4},
        "rule_of_law": {"civilWeight": risk_level * 0.5, "warWeight": risk_level * 0.3, "terrorismWeight": risk_level * 0.2},
        "control_of_corruption": {"civilWeight": risk_level * 0.6, "humanitarianWeight": risk_level * 0.2, "narrativeWeight": risk_level * 0.2},
    }

    base = {
        "warWeight": 0, "militaryWeight": 0, "civilWeight": 0,
        "terrorismWeight": 0, "humanitarianWeight": 0, "narrativeWeight": 0,
        "drivers": [],
    }
    if dimension in mapping:
        base.update(mapping[dimension])
        if risk_level > 0.5:
            base["drivers"].append(f"weak_{dimension}")

    return base


def _wgi_observation_to_signal(obs: dict, search: dict) -> dict:
    """Convert a WGI observation dict into a signal event.

    Produces a governance-family signal with a synthetic title, country-level
    geo, and classification weights derived from the governance dimension.
    """
    dimension_label = obs.get("dimension_label", obs.get("dimension", ""))
    country = obs.get("country", "Unknown")
    value = obs.get("value", 0)
    year = obs.get("year", "")

    title = f"{country}: {dimension_label} — {value:.1f} percentile ({year})"

    raw = f"{country}|{obs.get('dimension', '')}|{year}"
    eid = "signal-" + hashlib.md5(raw.encode()).hexdigest()[:12]

    return {
        "id": eid,
        "sourceId": search.get("id", ""),
        "sourceFamily": "governance",
        "sourceName": f"WGI – {dimension_label}",
        "title": title,
        "excerpt": f"{dimension_label} for {country}: {value:.1f}/100 percentile rank ({year})",
        "url": "https://info.worldbank.org/governance/wgi/",
        "author": {"name": "World Bank", "profileLocation": ""},
        "provenance": "World Bank Worldwide Governance Indicators",
        "engagement": {},
        "timestamp": f"{year}-01-01T00:00:00Z",
        "geo": {
            "lat": None,
            "lon": None,
            "country": country,
            "resolution": "country",
            "confidence": 1.0,
        },
        "classification": _classify_wgi_dimension(obs),
        "corroborationCount": 0,
    }


# ---------------------------------------------------------------------------
# Location scoring — server-side port of frontend scoring.js
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _hours_between(newer: datetime, older: datetime) -> float:
    return abs((newer - older).total_seconds()) / 3600.0


def _recency_weight(hours_ago: float) -> float:
    return math.exp(-hours_ago / 16.0)


def _unique(values: list) -> list:
    """Deduplicate preserving order."""
    seen: set = set()
    result = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


_DEFAULT_SCORING_CONFIG = {
    "warMultiplier": 7.2,
    "militaryMultiplier": 6.8,
    "terrorismMultiplier": 6.6,
    "civilMultiplier": 6.4,
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
    "corroborationBoost": 0.14,
    "singleSourcePenalty": 0.92,
    "confidenceBaseWeight": 0.72,
    "confidenceCorrobWeight": 0.08,
}


def _signal_event_score(event: dict, ref_time: datetime) -> float:
    ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    hours_ago = _hours_between(ref_time, ts)
    source_diversity_boost = 1.0 + (event.get("corroborationCount", 1) - 1) * 0.12
    confidence_penalty = 1.0 - max(
        event["classification"].get("confidencePenalty", 0),
        1.0 - event["geo"].get("confidence", 0.5),
    )
    c = event["classification"]
    total_weight = (
        (c.get("warWeight", 0))
        + (c.get("militaryWeight", 0))
        + (c.get("civilWeight", 0))
        + (c.get("terrorismWeight", 0))
        + (c.get("humanitarianWeight", 0))
        + (c.get("narrativeWeight", 0))
    )
    return (
        _recency_weight(hours_ago)
        * c.get("severity", 1)
        * total_weight
        * source_diversity_boost
        * confidence_penalty
    )


def _compute_history(events: list[dict], ref_time: datetime) -> list[float]:
    windows = [6, 12, 18, 24, 30, 36]  # scoring.js reverses [36,30,24,18,12,6]
    result = []
    for window_hours in windows:
        window_events = [
            e for e in events
            if _hours_between(ref_time, datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))) <= window_hours
        ]
        total = sum(_signal_event_score(e, ref_time) for e in window_events)
        result.append(round(total, 2))
    return result


def _dominant_source_families(events: list[dict]) -> list[str]:
    counts: dict[str, int] = {}
    for e in events:
        sf = e.get("sourceFamily", "unknown")
        counts[sf] = counts.get(sf, 0) + 1
    return [sf for sf, _ in sorted(counts.items(), key=lambda x: -x[1])]


def compute_location_scores(
    signal_events: list[dict],
    reference_time: str | None = None,
    emphasis: str = "blend",
    scoring_config: dict | None = None,
) -> list[dict]:
    """Compute location scores from signal events.

    This is a Python port of the frontend's computeLocationScores() in
    scoring.js so that the dataset ships with pre-computed scores.
    """
    if not signal_events:
        return []

    cfg = {**_DEFAULT_SCORING_CONFIG, **(scoring_config or {})}
    bw = cfg["blendWeights"]

    ref_time = datetime.fromisoformat(
        (reference_time or datetime.now(timezone.utc).isoformat())
        .replace("Z", "+00:00")
    )

    # Group by location key (roll up non-city / low-confidence to country)
    grouped: dict[str, list[dict]] = {}
    for event in signal_events:
        geo = event.get("geo", {})
        should_roll_up = geo.get("resolution") != "city" or geo.get("confidence", 0) < 0.68
        location_key = (geo.get("country") or geo.get("name", "Unknown")) if should_roll_up else geo.get("name", "Unknown")
        grouped.setdefault(location_key, []).append({**event, "displayLocationName": location_key})

    scores = []
    for location_name, events in grouped.items():
        # All six signal components (matching frontend scoring.js)
        war_component = 0.0
        military_component = 0.0
        civil_component = 0.0
        terrorism_component = 0.0
        humanitarian_component = 0.0
        infowar_component = 0.0
        for e in events:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            rw = _recency_weight(_hours_between(ref_time, ts))
            c = e["classification"]
            war_component += rw * c.get("warWeight", 0) * cfg["warMultiplier"]
            military_component += rw * c.get("militaryWeight", 0) * cfg["militaryMultiplier"]
            civil_component += rw * c.get("civilWeight", 0) * cfg["civilMultiplier"]
            terrorism_component += rw * c.get("terrorismWeight", 0) * cfg["terrorismMultiplier"]
            humanitarian_component += rw * c.get("humanitarianWeight", 0) * cfg["humanitarianMultiplier"]
            infowar_component += rw * c.get("narrativeWeight", 0) * cfg["infowarMultiplier"]

        # Base heat — blended across all six components (matches frontend)
        component_map = {
            "war": war_component,
            "military": military_component,
            "civil": civil_component,
            "terrorism": terrorism_component,
            "humanitarian": humanitarian_component,
            "infowar": infowar_component,
        }
        if emphasis in component_map:
            base_heat = component_map[emphasis]
        else:
            base_heat = sum(component_map[k] * bw.get(k, 0) for k in component_map)

        # Corroboration
        corroboration = len(_unique([e.get("sourceFamily", "unknown") for e in events]))

        # Velocity
        velocity_recent = len([
            e for e in events
            if _hours_between(ref_time, datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))) <= 12
        ])
        velocity_previous = len([
            e for e in events
            if 12 < _hours_between(ref_time, datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))) <= 24
        ])

        # Penalty for single-source uncorroborated (less harsh than before)
        penalty = cfg["singleSourcePenalty"] if (any(e.get("corroborationCount", 1) < 2 for e in events) and corroboration == 1) else 1.0

        heat = _clamp(base_heat * (1 + corroboration * cfg["corroborationBoost"]) * penalty, 0, 100)
        delta = _clamp(
            (velocity_recent - velocity_previous) * 6 + (4 if base_heat > 45 else 0),
            -40, 40,
        )

        # Strongest event
        sorted_events = sorted(events, key=lambda e: _signal_event_score(e, ref_time), reverse=True)
        strongest = sorted_events[0]

        # History
        history = _compute_history(events, ref_time)

        # Confidence
        avg_geo_confidence = sum(e["geo"].get("confidence", 0.5) for e in events) / max(len(events), 1)
        confidence = avg_geo_confidence * (cfg["confidenceBaseWeight"] + corroboration * cfg["confidenceCorrobWeight"])

        # Trend (matches scoring.js — suppress when heat is negligible)
        recent_metric = velocity_recent * 10 + base_heat
        previous_metric = velocity_previous * 10 + base_heat * 0.6
        if heat < 1:
            trend = "steady"
        elif recent_metric - previous_metric > 8:
            trend = "warming"
        elif recent_metric - previous_metric < -5:
            trend = "cooling"
        else:
            trend = "steady"

        # Top drivers (deduplicated across all events)
        all_drivers = []
        for e in events:
            all_drivers.extend(e["classification"].get("drivers", []))
        top_drivers = _unique(all_drivers)[:6]

        # Evidence bundle — top 4 signal events
        evidence_bundle = sorted_events[:4]

        location_id = re.sub(r"[^\w]+", "-", location_name.lower())

        scores.append({
            "id": location_id,
            "name": location_name,
            "heat": round(heat, 1),
            "delta": round(delta, 1),
            "confidence": _clamp(round(confidence, 2), 0.12, 0.97),
            "warComponent": round(_clamp(war_component, 0, 100), 1),
            "militaryComponent": round(_clamp(military_component, 0, 100), 1),
            "civilComponent": round(_clamp(civil_component, 0, 100), 1),
            "terrorismComponent": round(_clamp(terrorism_component, 0, 100), 1),
            "humanitarianComponent": round(_clamp(humanitarian_component, 0, 100), 1),
            "infowarComponent": round(_clamp(infowar_component, 0, 100), 1),
            "trend": trend,
            "history": history,
            "sourceBreakdown": _dominant_source_families(events),
            "topDrivers": top_drivers,
            "evidenceBundle": evidence_bundle,
            "center": {
                "lat": strongest["geo"].get("lat", 0),
                "lon": strongest["geo"].get("lon", 0),
            },
            "resolution": strongest["geo"].get("resolution", "country"),
        })

    # Sort by heat descending
    scores.sort(key=lambda s: s["heat"], reverse=True)
    return scores


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


async def sync_credentials(client: httpx.AsyncClient) -> None:
    """Fetch credentials from the API and apply them to the process environment.

    This lets the worker pick up token changes made via the frontend UI
    without requiring a container restart.
    """
    try:
        resp = await client.get(f"{API_BASE_URL}/config/credentials/raw")
        resp.raise_for_status()
        creds = resp.json()

        # Map credential fields to environment variables
        env_map = {
            ("x", "bearer_token"): "X_BEARER_TOKEN",
            ("x", "api_base_url"): "X_API_BASE_URL",
            ("bluesky", "identifier"): "BLUESKY_IDENTIFIER",
            ("bluesky", "app_password"): "BLUESKY_APP_PASSWORD",
            ("bluesky", "pds_url"): "BLUESKY_PDS_URL",
        }
        for (platform, field), env_var in env_map.items():
            value = creds.get(platform, {}).get(field, "")
            if isinstance(value, str) and value:
                os.environ[env_var] = value
        logger.info("Credentials synced from API")
    except Exception as exc:
        logger.debug("Could not sync credentials from API: %s", exc)


async def fetch_config(client: httpx.AsyncClient) -> tuple[list[dict], dict]:
    """Fetch searches and schedule from the API.

    Returns (searches, schedule).  Raises on HTTP or connection errors.
    """
    searches_resp = await client.get(f"{API_BASE_URL}/searches")
    searches_resp.raise_for_status()
    searches: list[dict] = searches_resp.json()

    schedule_resp = await client.get(f"{API_BASE_URL}/schedule")
    schedule_resp.raise_for_status()
    schedule: dict = schedule_resp.json()

    return searches, schedule


async def post_dataset(client: httpx.AsyncClient, dataset: dict) -> None:
    """POST the assembled dataset to the API."""
    resp = await client.post(f"{API_BASE_URL}/dataset", json=dataset)
    resp.raise_for_status()
    logger.info("POST /dataset succeeded (%s signals)", len(dataset.get("signalEvents", [])))


# ---------------------------------------------------------------------------
# Scrape cycle
# ---------------------------------------------------------------------------


async def run_scrape_cycle(client: httpx.AsyncClient, searches: list[dict]) -> dict:
    """Run one full scrape cycle across all configured searches.

    Returns the assembled dataset dict ready to POST.
    """
    all_signals: list[dict] = []
    source_items: list[dict] = []
    source_catalog: list[dict] = []
    failures: list[dict] = []

    for search in searches:
        search_id = search.get("id", "unknown")
        search_label = search.get("label", search_id)
        platform = search.get("platform", "google")
        logger.info("Scraping search: %s (%s) [platform=%s]", search_label, search_id, platform)

        if platform == "bluesky":
            # --- Bluesky source ---
            bluesky_query = build_bluesky_query(search["topics"])
            try:
                posts = await fetch_bluesky_posts(bluesky_query, max_posts=search.get("max_articles", 50))
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
                signal = bluesky_post_to_signal(post, search)
                all_signals.append(signal)

            logger.info("Search %s bluesky complete: %d posts", search_id, len(posts))

        elif platform == "x":
            # --- X / Twitter source ---
            x_query = build_x_query(search["topics"])
            try:
                posts = await fetch_x_posts(x_query, max_posts=search.get("max_articles", 50))
            except Exception as exc:
                logger.warning("X fetch failed for %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "X / Twitter",
                "sourceFamily": "x",
                "sourceKind": "x-search",
                "url": "",
                "itemCount": len(posts),
            })

            for post in posts:
                signal = x_post_to_signal(post, search)
                all_signals.append(signal)

            logger.info("Search %s x complete: %d posts", search_id, len(posts))

        elif platform == "rss":
            # --- RSS/Atom feed source ---
            feed_url = search.get("feed_url", "")
            if not feed_url:
                logger.warning("RSS search %s has no feed_url, skipping", search_id)
                continue

            try:
                articles = await fetch_rss_feed(
                    feed_url,
                    max_articles=search.get("max_articles", 50),
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
                signal = rss_article_to_signal(art, search)
                all_signals.append(signal)

            logger.info("Search %s rss complete: %d articles", search_id, len(articles))

        elif platform == "wgi":
            # --- WGI (World Governance Indicators) source ---
            from app.scrapers.wgi.fetcher import fetch_wgi_data

            try:
                observations = await fetch_wgi_data(
                    countries=search.get("countries", search.get("topics", [])),
                    dimensions=search.get("dimensions"),
                    metric=search.get("metric", "percentile_rank"),
                )
            except Exception as exc:
                logger.warning("WGI fetch failed for %s: %s", search_id, exc)
                failures.append({"sourceId": search_id, "error": str(exc)})
                continue

            source_catalog.append({
                "id": search_id,
                "label": search_label,
                "source": "World Bank WGI",
                "sourceFamily": "governance",
                "sourceKind": "wgi-indicators",
                "url": "https://info.worldbank.org/governance/wgi/",
                "itemCount": len(observations),
            })

            for obs in observations:
                signal = _wgi_observation_to_signal(obs, search)
                all_signals.append(signal)

            logger.info("Search %s wgi complete: %d observations", search_id, len(observations))

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
                    max_articles=search.get("max_articles", 50),
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
                signal = article_to_signal(art, search)
                all_signals.append(signal)

            logger.info("Search %s news complete: %d articles", search_id, len(articles))

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Compute location scores server-side so the frontend has them immediately
    location_scores = compute_location_scores(
        all_signals,
        reference_time=generated_at,
        emphasis="blend",
    )
    logger.info("Computed %d location scores from %d signals", len(location_scores), len(all_signals))

    dataset = {
        "generatedAt": generated_at,
        "sourceCatalog": source_catalog,
        "feedCatalog": [],
        "failures": failures,
        "sourceStatus": {
            "rss": "loaded" if any(s.get("sourceFamily") == "rss" for s in all_signals) else "missing",
            "bluesky": "loaded" if any(s.get("sourceFamily") == "bluesky" for s in all_signals) else "missing",
            "news": "loaded" if any(s.get("sourceFamily") == "news" for s in all_signals) else "empty",
            "x": "loaded" if any(s.get("sourceFamily") == "x" for s in all_signals) else "missing",
            "governance": "loaded" if any(s.get("sourceFamily") == "governance" for s in all_signals) else "missing",
        },
        "sourceItems": source_items,
        "signalEvents": all_signals,
        "locationScores": location_scores,
    }

    return dataset


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


async def main() -> None:
    logger.info("Worker starting. API_BASE_URL=%s", API_BASE_URL)

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            try:
                # 1. Fetch config
                try:
                    searches, schedule = await fetch_config(client)
                except Exception as exc:
                    logger.warning("API unreachable, retrying in 30s: %s", exc)
                    await asyncio.sleep(30)
                    continue

                interval_minutes = schedule.get("interval_minutes", 5)
                enabled = schedule.get("enabled", True)

                logger.info(
                    "Config loaded: %d searches, interval=%dm, enabled=%s",
                    len(searches),
                    interval_minutes,
                    enabled,
                )

                # 2. Check for pending_refresh flag (manual trigger from frontend)
                pending = schedule.get("pending_refresh", False)

                # 3. If disabled and no pending refresh, wait and re-check
                if not enabled and not pending:
                    logger.info("Schedule disabled, sleeping 30s before re-check")
                    await asyncio.sleep(30)
                    continue

                if pending:
                    logger.info("Pending refresh detected — running immediately")
                    # Clear the flag via the API
                    try:
                        schedule.pop("pending_refresh", None)
                        await client.put(f"{API_BASE_URL}/schedule", json=schedule)
                    except Exception:
                        pass  # best-effort clear

                # 4. Sync credentials from API (picks up UI changes)
                await sync_credentials(client)

                # 5. Run scrape cycle
                dataset = await run_scrape_cycle(client, searches)

                # 6. POST dataset
                try:
                    await post_dataset(client, dataset)
                except Exception as exc:
                    logger.error("Failed to POST dataset: %s", exc)

                # 7. Sleep — short poll if disabled (to catch pending_refresh), full interval if enabled
                if not enabled:
                    logger.info("Cycle complete (manual trigger). Resuming idle poll.")
                    await asyncio.sleep(30)
                else:
                    sleep_secs = interval_minutes * 60
                    logger.info("Cycle complete. Sleeping %ds (%dm)", sleep_secs, interval_minutes)
                    await asyncio.sleep(sleep_secs)

            except Exception as exc:
                logger.exception("Unexpected error in main loop: %s", exc)
                await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
