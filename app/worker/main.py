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
    """Parse RFC 2822 date or return current time as ISO 8601."""
    if not raw:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        dt = parsedate_to_datetime(raw)
        # Ensure UTC
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


def _signal_event_score(event: dict, ref_time: datetime) -> float:
    ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    hours_ago = _hours_between(ref_time, ts)
    source_diversity_boost = 1.0 + (event.get("corroborationCount", 1) - 1) * 0.12
    confidence_penalty = 1.0 - max(
        event["classification"].get("confidencePenalty", 0),
        1.0 - event["geo"].get("confidence", 0.5),
    )
    return (
        _recency_weight(hours_ago)
        * event["classification"].get("severity", 1)
        * (event["classification"].get("civilWeight", 0) + event["classification"].get("militaryWeight", 0))
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
) -> list[dict]:
    """Compute location scores from signal events.

    This is a Python port of the frontend's computeLocationScores() in
    scoring.js so that the dataset ships with pre-computed scores.
    """
    if not signal_events:
        return []

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
        # Civil and military components
        civil_component = 0.0
        military_component = 0.0
        for e in events:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            rw = _recency_weight(_hours_between(ref_time, ts))
            civil_component += rw * e["classification"].get("civilWeight", 0) * 6.4
            military_component += rw * e["classification"].get("militaryWeight", 0) * 6.8

        # Base heat
        if emphasis == "civil":
            base_heat = civil_component
        elif emphasis == "military":
            base_heat = military_component
        else:
            base_heat = civil_component * 0.56 + military_component * 0.44

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

        # Penalty for single-source uncorroborated
        penalty = 0.82 if (any(e.get("corroborationCount", 1) < 2 for e in events) and corroboration == 1) else 1.0

        heat = _clamp(base_heat * (1 + corroboration * 0.14) * penalty, 0, 100)
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
        confidence = avg_geo_confidence * (0.72 + corroboration * 0.08)

        # Trend (matches scoring.js)
        recent_metric = velocity_recent * 10 + base_heat
        previous_metric = velocity_previous * 10 + base_heat * 0.6
        if recent_metric - previous_metric > 8:
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
            "civilComponent": round(_clamp(civil_component, 0, 100), 1),
            "militaryComponent": round(_clamp(military_component, 0, 100), 1),
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
        logger.info("Scraping search: %s (%s)", search_label, search_id)

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
            signal = article_to_signal(art, search)
            all_signals.append(signal)

        logger.info(
            "Search %s complete: %d articles, %d signals",
            search_id,
            len(articles),
            len(articles),
        )

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
            "rss": "missing",
            "bluesky": "missing",
            "news": "loaded" if all_signals else "empty",
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

                # 4. Run scrape cycle
                dataset = await run_scrape_cycle(client, searches)

                # 5. POST dataset
                try:
                    await post_dataset(client, dataset)
                except Exception as exc:
                    logger.error("Failed to POST dataset: %s", exc)

                # 6. Sleep — short poll if disabled (to catch pending_refresh), full interval if enabled
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
