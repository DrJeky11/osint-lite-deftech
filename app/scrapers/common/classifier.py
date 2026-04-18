"""Simple keyword-based signal classification for OSINT events."""

import re

# Keyword lists for each signal dimension
CIVIL_KEYWORDS = [
    "protest", "riot", "crackdown", "demonstration", "unrest", "civil",
    "humanitarian", "famine", "refugee", "displaced", "civilian",
    "human rights", "arrest", "detention", "opposition", "election",
    "corruption", "sanction", "embargo", "aid", "crisis", "violence",
    "gang", "cartel", "crime", "kidnap", "abduct", "hostage",
]

MILITARY_KEYWORDS = [
    "army", "military", "coup", "troop", "troops", "airstrike", "air strike",
    "missile", "drone", "bombing", "shelling", "offensive", "artillery",
    "weapon", "arms", "defense", "defence", "naval", "navy", "fighter jet",
    "tank", "soldier", "militia", "paramilitary", "insurgent", "insurgency",
    "rebel", "warfare", "combat", "deployment", "invasion", "occupation",
    "ceasefire", "cease-fire", "nuclear", "warship", "blockade",
]

NARRATIVE_KEYWORDS = [
    "disinformation", "misinformation", "propaganda", "viral", "narrative",
    "influence", "cyber", "hack", "leak", "espionage", "spy", "intelligence",
    "social media", "information warfare", "psyop", "troll", "bot",
    "fake news", "censorship", "media", "campaign",
]

# Pre-compile patterns for efficiency
_CIVIL_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in CIVIL_KEYWORDS]
_MILITARY_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in MILITARY_KEYWORDS]
_NARRATIVE_PATTERNS = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in NARRATIVE_KEYWORDS]


def classify(title: str, description: str = "") -> dict:
    """Classify an article by checking title + description against keyword lists.

    Returns a classification dict matching the frontend's expected shape.
    """
    text = f"{title} {description}"

    civil_hits = [kw for kw, pat in zip(CIVIL_KEYWORDS, _CIVIL_PATTERNS) if pat.search(text)]
    military_hits = [kw for kw, pat in zip(MILITARY_KEYWORDS, _MILITARY_PATTERNS) if pat.search(text)]
    narrative_hits = [kw for kw, pat in zip(NARRATIVE_KEYWORDS, _NARRATIVE_PATTERNS) if pat.search(text)]

    civil_weight = min(len(civil_hits) * 0.3, 1.0)
    military_weight = min(len(military_hits) * 0.3, 1.0)
    narrative_weight = min(len(narrative_hits) * 0.3, 1.0)

    # Determine dominant signal type
    weights = {
        "civil": civil_weight,
        "military": military_weight,
        "narrative": narrative_weight,
    }
    signal_type = max(weights, key=weights.get) if any(v > 0 for v in weights.values()) else "narrative"

    # Severity: 1-5 based on total keyword hits
    total_hits = len(civil_hits) + len(military_hits) + len(narrative_hits)
    severity = min(max(total_hits, 1), 5)

    # Drivers: the matched keywords
    drivers = civil_hits + military_hits + narrative_hits

    return {
        "signalType": signal_type,
        "severity": severity,
        "civilWeight": round(civil_weight, 2),
        "militaryWeight": round(military_weight, 2),
        "narrativeWeight": round(narrative_weight, 2),
        "drivers": drivers,
        "confidencePenalty": 0,
    }
