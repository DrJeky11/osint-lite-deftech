"""Pre-configured search catalog for OSINT data collection.

Searches are persisted to searches.json so they can be managed at runtime
via the /searches CRUD endpoints.

Each search has a ``group`` field that ties platform-specific sources
together.  The "Add Search" UI creates one source per platform sharing
the same group slug.
"""

import json
import uuid
from pathlib import Path

SEARCHES_PATH = Path(__file__).parent / "searches.json"

# Supported platform values for the "platform" field
SUPPORTED_PLATFORMS = ["google", "bluesky", "x"]

_SEARCH_TEMPLATES = [
    {
        "label": "Sudan Conflict",
        "topics": ["Sudan conflict", "RSF Khartoum"],
        "location": "Sudan",
        "place_hints": ["Sudan", "Khartoum"],
        "max_articles": 15,
    },
    {
        "label": "Myanmar Crisis",
        "topics": ["Myanmar civil war", "Myanmar junta"],
        "location": "Myanmar",
        "place_hints": ["Myanmar", "Yangon"],
        "max_articles": 15,
    },
    {
        "label": "Haiti Security",
        "topics": ["Haiti gang violence", "Haiti crisis"],
        "location": "Haiti",
        "place_hints": ["Haiti", "Port-au-Prince"],
        "max_articles": 15,
    },
    {
        "label": "Ukraine War",
        "topics": ["Ukraine war", "Ukraine front lines"],
        "location": "Ukraine",
        "place_hints": ["Ukraine", "Kyiv"],
        "max_articles": 15,
    },
    {
        "label": "Yemen Conflict",
        "topics": ["Yemen Houthi", "Yemen conflict"],
        "location": "Yemen",
        "place_hints": ["Yemen", "Sanaa"],
        "max_articles": 15,
    },
    {
        "label": "Israel-Palestine",
        "topics": ["Israel Gaza", "West Bank conflict"],
        "location": "Israel",
        "place_hints": ["Israel", "Gaza"],
        "max_articles": 15,
    },
    {
        "label": "Iran Tensions",
        "topics": ["Iran nuclear", "Iran sanctions"],
        "location": "Iran",
        "place_hints": ["Iran", "Tehran"],
        "max_articles": 15,
    },
    {
        "label": "Taiwan Strait",
        "topics": ["Taiwan China military", "Taiwan strait"],
        "location": "Taiwan",
        "place_hints": ["Taiwan", "Taipei"],
        "max_articles": 15,
    },
    {
        "label": "Sahel Instability",
        "topics": ["Mali coup", "Sahel insurgency", "Burkina Faso"],
        "location": None,
        "place_hints": ["Mali", "Bamako", "Nigeria"],
        "max_articles": 15,
    },
    {
        "label": "DRC Conflict",
        "topics": ["Congo M23", "DRC conflict"],
        "location": "Congo",
        "place_hints": ["DRC", "Kinshasa", "Congo"],
        "max_articles": 15,
    },
]


def _make_slug(label: str) -> str:
    return label.lower().replace(" ", "-")


def _build_default_catalog() -> list[dict]:
    """Generate one source entry per platform per search template."""
    catalog = []
    for tmpl in _SEARCH_TEMPLATES:
        slug = _make_slug(tmpl["label"])
        group = f"search-{slug}"
        for platform in SUPPORTED_PLATFORMS:
            entry = {
                **tmpl,
                "id": f"{platform}-{slug}",
                "group": group,
                "platform": platform,
            }
            catalog.append(entry)
    return catalog


_DEFAULT_CATALOG = _build_default_catalog()

# In-memory cache loaded once at import time
_searches: list[dict] = []


def _load_from_disk() -> list[dict]:
    """Read searches.json, or seed from defaults if it doesn't exist."""
    if SEARCHES_PATH.exists():
        return json.loads(SEARCHES_PATH.read_text())
    # Seed with defaults
    save_searches(_DEFAULT_CATALOG)
    return list(_DEFAULT_CATALOG)


def save_searches(searches: list[dict] | None = None) -> None:
    """Persist the current search list to disk."""
    data = searches if searches is not None else _searches
    SEARCHES_PATH.write_text(json.dumps(data, indent=2))


def get_searches() -> list[dict]:
    """Return the current list of searches."""
    return _searches


def add_search(search: dict) -> dict:
    """Add a single search source entry."""
    platform = search.get("platform", "google")
    if platform not in SUPPORTED_PLATFORMS:
        platform = "google"
        search["platform"] = platform
    if "id" not in search:
        slug = _make_slug(search.get("label", uuid.uuid4().hex[:8]))
        search["id"] = f"{platform}-{slug}"
    if "group" not in search:
        slug = _make_slug(search.get("label", uuid.uuid4().hex[:8]))
        search["group"] = f"search-{slug}"
    _searches.append(search)
    save_searches()
    return search


def add_search_group(
    label: str,
    topics: list[str],
    location: str | None = None,
    place_hints: list[str] | None = None,
    max_articles: int = 15,
    platforms: list[str] | None = None,
) -> list[dict]:
    """Create one source per platform sharing a group ID. Returns all created sources."""
    slug = _make_slug(label)
    group = f"search-{slug}"
    use_platforms = platforms or list(SUPPORTED_PLATFORMS)
    created = []
    for platform in use_platforms:
        if platform not in SUPPORTED_PLATFORMS:
            continue
        entry = {
            "id": f"{platform}-{slug}",
            "group": group,
            "platform": platform,
            "label": label,
            "topics": list(topics),
            "location": location,
            "place_hints": list(place_hints or []),
            "max_articles": max_articles,
        }
        _searches.append(entry)
        created.append(entry)
    save_searches()
    return created


def delete_search(search_id: str) -> bool:
    """Delete a search by ID, save, return True if found."""
    for i, s in enumerate(_searches):
        if s["id"] == search_id:
            _searches.pop(i)
            save_searches()
            return True
    return False


def delete_search_group(group: str) -> int:
    """Delete all sources belonging to a group. Returns count deleted."""
    before = len(_searches)
    _searches[:] = [s for s in _searches if s.get("group") != group]
    after = len(_searches)
    deleted = before - after
    if deleted:
        save_searches()
    return deleted


def update_search(search_id: str, data: dict) -> dict | None:
    """Update an existing search by ID, save, return updated or None."""
    for i, s in enumerate(_searches):
        if s["id"] == search_id:
            _searches[i] = {**s, **data, "id": search_id}
            save_searches()
            return _searches[i]
    return None


# Load on import
_searches.extend(_load_from_disk())
