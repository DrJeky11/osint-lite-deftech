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

from .country_data import COUNTRIES, generate_country_template

SEARCHES_PATH = Path(__file__).parent / "searches.json"

# Supported platform values for the "platform" field
SUPPORTED_PLATFORMS = ["google", "bluesky", "x", "rss", "wgi"]

_SEARCH_TEMPLATES = [
    {
        "label": "Sudan Conflict",
        "topics": ["Sudan conflict", "RSF Khartoum"],
        "location": "Sudan",
        "place_hints": ["Sudan", "Khartoum"],
        "max_articles": 50,
    },
    {
        "label": "Myanmar Crisis",
        "topics": ["Myanmar civil war", "Myanmar junta", "Myanmar resistance movement", "Rohingya crisis"],
        "location": "Myanmar",
        "place_hints": ["Myanmar", "Yangon", "Naypyidaw"],
        "max_articles": 50,
    },
    {
        "label": "Haiti Security",
        "topics": ["Haiti gang violence", "Haiti crisis"],
        "location": "Haiti",
        "place_hints": ["Haiti", "Port-au-Prince"],
        "max_articles": 50,
    },
    {
        "label": "Ukraine War",
        "topics": ["Ukraine war", "Ukraine front lines"],
        "location": "Ukraine",
        "place_hints": ["Ukraine", "Kyiv"],
        "max_articles": 50,
    },
    {
        "label": "Yemen Conflict",
        "topics": ["Yemen Houthi", "Yemen conflict"],
        "location": "Yemen",
        "place_hints": ["Yemen", "Sanaa"],
        "max_articles": 50,
    },
    {
        "label": "Israel-Palestine",
        "topics": ["Israel Gaza", "West Bank conflict", "Israel settlement expansion", "Israel Palestine diplomacy"],
        "location": "Israel",
        "place_hints": ["Israel", "Gaza", "West Bank", "Jerusalem"],
        "max_articles": 50,
    },
    {
        "label": "Iran Tensions",
        "topics": ["Iran nuclear", "Iran sanctions", "IRGC activity", "Strait of Hormuz", "Iran proxy conflict"],
        "location": "Iran",
        "place_hints": ["Iran", "Tehran", "Strait of Hormuz"],
        "max_articles": 50,
    },
    {
        "label": "Taiwan Strait",
        "topics": ["Taiwan China military", "Taiwan strait", "Taiwan defense", "PLA exercises Taiwan"],
        "location": "Taiwan",
        "place_hints": ["Taiwan", "Taipei", "South China Sea"],
        "max_articles": 50,
    },
    {
        "label": "Sahel Instability",
        "topics": ["Mali coup", "Sahel insurgency", "Burkina Faso"],
        "location": None,
        "place_hints": ["Mali", "Bamako", "Nigeria"],
        "max_articles": 50,
    },
    {
        "label": "DRC Conflict",
        "topics": ["Congo M23", "DRC conflict"],
        "location": "Congo",
        "place_hints": ["DRC", "Kinshasa", "Congo"],
        "max_articles": 50,
    },
    {
        "label": "Russia Military",
        "topics": [
            "Russia military movement",
            "Wagner PMC activity",
            "Russia sanctions evasion",
            "Arctic militarization Russia",
            "Russia nuclear posture",
        ],
        "location": "Russia",
        "place_hints": ["Russia", "Moscow"],
        "max_articles": 50,
    },
    {
        "label": "China Security",
        "topics": [
            "South China Sea military",
            "Taiwan strait tensions",
            "China military exercises",
            "China cyber operations",
            "Belt and Road security",
            "Xinjiang repression",
        ],
        "location": "China",
        "place_hints": ["China", "Beijing", "South China Sea"],
        "max_articles": 50,
    },
    {
        "label": "United States Defense",
        "topics": [
            "US military deployment",
            "US defense policy",
            "NATO commitment US",
            "US domestic security threat",
        ],
        "location": "United States",
        "place_hints": ["United States", "Washington", "Pentagon"],
        "max_articles": 50,
    },
    {
        "label": "North Korea Provocations",
        "topics": [
            "North Korea missile test",
            "North Korea nuclear program",
            "North Korea sanctions evasion",
            "DPRK military provocation",
        ],
        "location": None,
        "place_hints": ["North Korea", "Pyongyang", "DPRK"],
        "max_articles": 50,
    },
    {
        "label": "India-Pakistan Tensions",
        "topics": [
            "Kashmir border tensions",
            "India Pakistan military",
            "India military modernization",
            "Pakistan military modernization",
            "Line of Control incident",
        ],
        "location": None,
        "place_hints": ["India", "Pakistan", "Kashmir", "New Delhi", "Islamabad"],
        "max_articles": 50,
    },
    {
        "label": "Horn of Africa",
        "topics": [
            "Ethiopia Tigray conflict",
            "Horn of Africa instability",
            "Red Sea security threat",
            "Somalia al-Shabaab",
            "Eritrea tensions",
        ],
        "location": None,
        "place_hints": ["Ethiopia", "Tigray", "Somalia", "Eritrea", "Djibouti"],
        "max_articles": 50,
    },
    {
        "label": "Venezuela Crisis",
        "topics": [
            "Venezuela political crisis",
            "Venezuela migration crisis",
            "Venezuela oil politics",
            "Venezuela opposition crackdown",
        ],
        "location": "Venezuela",
        "place_hints": ["Venezuela", "Caracas"],
        "max_articles": 50,
    },
    {
        "label": "Governance Indicators",
        "platform": "wgi",
        "topics": [],  # not used for WGI
        "countries": [],  # filled by user
        "dimensions": [],  # empty = all 6
        "max_articles": 50,
    },
]

# Auto-generate templates for every country not already covered by a
# hand-curated template above.  Matching is case-insensitive on the
# location field so "United States" matches "United States of America", etc.
_curated_locations = {
    (t.get("location") or "").lower() for t in _SEARCH_TEMPLATES
}
_curated_labels = {t["label"].lower() for t in _SEARCH_TEMPLATES}

for _country in COUNTRIES:
    _loc_lower = _country["name"].lower()
    # Skip if the curated list already has a template whose location or
    # label contains this country name (handles "Congo" matching "DRC Conflict", etc.)
    if any(_loc_lower in cl for cl in _curated_locations) or any(
        _loc_lower in cl for cl in _curated_labels
    ):
        continue
    # Also skip if any curated location is a substring of this country name
    if any(cl and cl in _loc_lower for cl in _curated_locations):
        continue
    _SEARCH_TEMPLATES.append(generate_country_template(_country))


def _make_slug(label: str) -> str:
    return label.lower().replace(" ", "-")


def _build_default_catalog() -> list[dict]:
    """Generate one source entry per platform per search template.

    Templates that already specify a ``platform`` (e.g. WGI) are added
    once for that platform only instead of being expanded across all
    platforms.
    """
    catalog = []
    for tmpl in _SEARCH_TEMPLATES:
        slug = _make_slug(tmpl["label"])
        group = f"search-{slug}"
        # If the template pins a specific platform, only create one entry
        if "platform" in tmpl:
            platform = tmpl["platform"]
            entry = {
                **tmpl,
                "id": f"{platform}-{slug}",
                "group": group,
                "platform": platform,
            }
            catalog.append(entry)
        else:
            for platform in SUPPORTED_PLATFORMS:
                if platform == "wgi":
                    continue  # WGI is data-source specific, skip for generic templates
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
    max_articles: int = 50,
    platforms: list[str] | None = None,
) -> list[dict]:
    """Create one source per platform sharing a group ID. Returns all created sources."""
    slug = _make_slug(label)
    group = f"search-{slug}"
    use_platforms = platforms or [p for p in SUPPORTED_PLATFORMS if p not in ("rss", "wgi")]
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
