"""Configurable keyword-based signal classification for OSINT events."""

import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "api" / "classifier_config.json"

DEFAULT_CONFIG = {
    "warKeywords": [
        "war", "invasion", "invade", "occupied", "occupation", "offensive",
        "airstrike", "air strike", "missile", "shelling", "bombing",
        "bombardment", "combat", "warfare", "siege", "frontline",
        "battlefield", "casualties", "killed", "wounded", "destroyed",
        "battle", "assault", "counteroffensive", "escalation", "rocket",
        "strike", "ceasefire", "cease-fire",
        "drone strike", "drone attack", "ballistic missile", "cruise missile",
        "missile attack", "missile strike", "naval blockade", "strait closure",
        "military retaliation", "retaliatory strike", "military operation",
        "kinetic strike", "infrastructure strike", "troop mobilization",
        "army mobilization", "military buildup",
    ],
    "militaryKeywords": [
        "army", "military", "coup", "troop", "troops", "deployment", "naval",
        "navy", "warship", "fighter jet", "tank", "soldier", "defense",
        "defence", "nuclear", "blockade", "mobilization", "buildup",
        "exercises", "provocation", "arms", "weapon", "arsenal", "ammunition",
        "drone swarm", "unmanned aircraft", "air defense", "interceptor",
        "naval deployment", "fleet deployment", "combat readiness",
        "military drill", "military exercise",
    ],
    "civilKeywords": [
        "protest", "riot", "crackdown", "demonstration", "unrest", "civil",
        "opposition", "election", "corruption", "sanction", "embargo",
        "violence", "gang", "cartel", "crime", "arrest", "detention",
        "martial law", "curfew", "state of emergency",
    ],
    "terrorismKeywords": [
        "terrorist", "terrorism", "insurgent", "insurgency", "rebel",
        "extremist", "extremism", "IED", "suicide bomb", "hostage", "kidnap",
        "abduct", "radicalization", "guerrilla", "militia",
        "car bomb", "suicide attack", "mass shooting", "lone wolf",
        "terrorist attack", "bombing attack",
    ],
    "humanitarianKeywords": [
        "humanitarian", "famine", "refugee", "displaced", "civilian",
        "human rights", "aid", "crisis", "hunger", "starvation", "epidemic",
        "cholera", "displacement", "evacuation", "relief",
        "war crime", "ethnic cleansing", "genocide", "mass grave",
        "civilian casualties", "infrastructure destroyed",
    ],
    "narrativeKeywords": [
        "disinformation", "misinformation", "propaganda", "viral", "narrative",
        "influence", "cyber", "hack", "leak", "espionage", "spy", "intelligence",
        "social media", "information warfare", "psyop", "troll", "bot",
        "fake news", "censorship", "media", "campaign",
        "cyber attack", "cyberwarfare", "electronic warfare", "deepfake",
    ],
    "deescalationKeywords": [
        "peace", "ceasefire agreement", "peace deal", "peace talks", "treaty",
        "negotiation", "negotiations", "diplomatic", "diplomacy", "de-escalation",
        "deescalation", "truce", "accord", "agreement", "summit", "dialogue",
        "reconciliation", "withdrawal", "pullback", "stand-down", "détente",
        "rapprochement", "normalization", "talks", "deal", "compromise",
        "humanitarian corridor", "prisoner exchange", "confidence-building",
    ],
    "keywordWeight": 0.3,
    "categoryWeights": {
        "war": 1.5,
        "military": 1.2,
        "terrorism": 1.2,
        "civil": 1.0,
        "humanitarian": 1.0,
        "narrative": 1.0,
    },
    "deescalationDampening": 0.15,
    "maxWeight": 1.0,
    "maxSeverity": 5,
}

# Ordered list of the six signal categories and their config keys.
_CATEGORIES = [
    ("war", "warKeywords"),
    ("military", "militaryKeywords"),
    ("civil", "civilKeywords"),
    ("terrorism", "terrorismKeywords"),
    ("humanitarian", "humanitarianKeywords"),
    ("narrative", "narrativeKeywords"),
]


def _compile_patterns(keywords: list[str]):
    return [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in keywords]


def load_config() -> dict:
    if CONFIG_PATH.exists():
        stored = json.loads(CONFIG_PATH.read_text())
        return {**DEFAULT_CONFIG, **stored}
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> dict:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    return cfg


def classify(title: str, description: str = "", config: dict | None = None, *, enabled: bool = True) -> dict:
    """Classify an article by checking title + description against keyword lists.

    Returns a classification dict matching the frontend's expected shape.
    If *enabled* is False, returns a neutral default classification immediately.
    """
    if not enabled:
        return {
            "signalType": "civil",
            "severity": 1,
            "warWeight": 0,
            "militaryWeight": 0,
            "civilWeight": 0,
            "terrorismWeight": 0,
            "humanitarianWeight": 0,
            "narrativeWeight": 0,
            "drivers": [],
            "confidencePenalty": 0,
            "deescalation": False,
            "deescalationFactor": 1.0,
        }

    cfg = config or load_config()
    text = f"{title} {description}"

    kw_weight = cfg.get("keywordWeight", 0.3)
    max_w = cfg.get("maxWeight", 1.0)
    max_sev = cfg.get("maxSeverity", 5)
    dampening = cfg.get("deescalationDampening", 0.4)

    # --- Category weights for severity scoring ---
    cat_weights = cfg.get("categoryWeights", DEFAULT_CONFIG["categoryWeights"])

    # --- Compute hits and weights for each signal category ---
    hits: dict[str, list[str]] = {}
    weights: dict[str, float] = {}

    for cat_name, cfg_key in _CATEGORIES:
        kws = cfg.get(cfg_key, DEFAULT_CONFIG[cfg_key])
        pats = _compile_patterns(kws)
        hits[cat_name] = [kw for kw, pat in zip(kws, pats) if pat.search(text)]
        weights[cat_name] = min(len(hits[cat_name]) * kw_weight, max_w)

    # --- De-escalation ---
    deesc_kws = cfg.get("deescalationKeywords", DEFAULT_CONFIG["deescalationKeywords"])
    deesc_pats = _compile_patterns(deesc_kws)
    deesc_hits = [kw for kw, pat in zip(deesc_kws, deesc_pats) if pat.search(text)]

    # Only apply dampening when de-escalation signals outnumber escalation signals
    total_escalation_hits = sum(len(h) for h in hits.values())
    deesc_factor = 1.0
    if deesc_hits and len(deesc_hits) > total_escalation_hits:
        deesc_factor = max(1.0 - len(deesc_hits) * dampening, 0.1)
        for cat_name in weights:
            weights[cat_name] *= deesc_factor

    # --- Determine dominant signal type ---
    signal_type = (
        max(weights, key=weights.get)
        if any(v > 0 for v in weights.values())
        else "narrative"
    )

    # --- Severity (weighted by category importance) ---
    weighted_hits = sum(
        len(hits[cat_name]) * cat_weights.get(cat_name, 1.0)
        for cat_name in hits
    )
    severity = min(max(round(weighted_hits), 1), max_sev)
    if deesc_hits and len(deesc_hits) > total_escalation_hits:
        severity = max(1, round(severity * deesc_factor))

    # --- Drivers ---
    drivers: list[str] = []
    for cat_name, _ in _CATEGORIES:
        drivers.extend(hits[cat_name])
    if deesc_hits:
        drivers.extend(f"⟳ {kw}" for kw in deesc_hits)

    return {
        "signalType": signal_type,
        "severity": severity,
        "warWeight": round(weights["war"], 2),
        "militaryWeight": round(weights["military"], 2),
        "civilWeight": round(weights["civil"], 2),
        "terrorismWeight": round(weights["terrorism"], 2),
        "humanitarianWeight": round(weights["humanitarian"], 2),
        "narrativeWeight": round(weights["narrative"], 2),
        "drivers": drivers,
        "confidencePenalty": 0,
        "deescalation": len(deesc_hits) > 0,
        "deescalationFactor": round(deesc_factor, 2),
    }
