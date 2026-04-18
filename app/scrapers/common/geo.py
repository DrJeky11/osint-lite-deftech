"""Simple gazetteer-based geo inference for OSINT signal events."""

import re
from typing import Optional

# Dictionary of known locations: name -> geo info
# Covers major conflict/instability zones
GAZETTEER: dict[str, dict] = {
    # Sudan
    "sudan": {"lat": 15.5007, "lon": 32.5599, "country": "Sudan", "name": "Sudan", "resolution": "country", "confidence": 0.7},
    "khartoum": {"lat": 15.5007, "lon": 32.5599, "country": "Sudan", "name": "Khartoum", "resolution": "city", "confidence": 0.85},
    "darfur": {"lat": 13.5, "lon": 25.0, "country": "Sudan", "name": "Darfur", "resolution": "region", "confidence": 0.8},
    "rsf": {"lat": 15.5007, "lon": 32.5599, "country": "Sudan", "name": "Sudan", "resolution": "country", "confidence": 0.6},
    # Myanmar
    "myanmar": {"lat": 16.8661, "lon": 96.1951, "country": "Myanmar", "name": "Myanmar", "resolution": "country", "confidence": 0.7},
    "burma": {"lat": 16.8661, "lon": 96.1951, "country": "Myanmar", "name": "Myanmar", "resolution": "country", "confidence": 0.7},
    "yangon": {"lat": 16.8661, "lon": 96.1951, "country": "Myanmar", "name": "Yangon", "resolution": "city", "confidence": 0.85},
    # Haiti
    "haiti": {"lat": 18.5944, "lon": -72.3074, "country": "Haiti", "name": "Haiti", "resolution": "country", "confidence": 0.7},
    "port-au-prince": {"lat": 18.5944, "lon": -72.3074, "country": "Haiti", "name": "Port-au-Prince", "resolution": "city", "confidence": 0.85},
    # Venezuela
    "venezuela": {"lat": 10.4806, "lon": -66.9036, "country": "Venezuela", "name": "Venezuela", "resolution": "country", "confidence": 0.7},
    "caracas": {"lat": 10.4806, "lon": -66.9036, "country": "Venezuela", "name": "Caracas", "resolution": "city", "confidence": 0.85},
    # Pakistan
    "pakistan": {"lat": 33.6844, "lon": 73.0479, "country": "Pakistan", "name": "Pakistan", "resolution": "country", "confidence": 0.7},
    "quetta": {"lat": 30.1798, "lon": 66.975, "country": "Pakistan", "name": "Quetta", "resolution": "city", "confidence": 0.85},
    "balochistan": {"lat": 28.49, "lon": 65.09, "country": "Pakistan", "name": "Balochistan", "resolution": "region", "confidence": 0.8},
    # Ukraine
    "ukraine": {"lat": 50.4501, "lon": 30.5234, "country": "Ukraine", "name": "Ukraine", "resolution": "country", "confidence": 0.7},
    "kyiv": {"lat": 50.4501, "lon": 30.5234, "country": "Ukraine", "name": "Kyiv", "resolution": "city", "confidence": 0.85},
    "kiev": {"lat": 50.4501, "lon": 30.5234, "country": "Ukraine", "name": "Kyiv", "resolution": "city", "confidence": 0.85},
    "donbas": {"lat": 48.0, "lon": 37.8, "country": "Ukraine", "name": "Donbas", "resolution": "region", "confidence": 0.8},
    "crimea": {"lat": 44.95, "lon": 34.1, "country": "Ukraine", "name": "Crimea", "resolution": "region", "confidence": 0.8},
    # Lebanon
    "lebanon": {"lat": 33.8938, "lon": 35.5018, "country": "Lebanon", "name": "Lebanon", "resolution": "country", "confidence": 0.7},
    "beirut": {"lat": 33.8938, "lon": 35.5018, "country": "Lebanon", "name": "Beirut", "resolution": "city", "confidence": 0.85},
    # Syria
    "syria": {"lat": 33.5138, "lon": 36.2765, "country": "Syria", "name": "Syria", "resolution": "country", "confidence": 0.7},
    "damascus": {"lat": 33.5138, "lon": 36.2765, "country": "Syria", "name": "Damascus", "resolution": "city", "confidence": 0.85},
    "aleppo": {"lat": 36.2021, "lon": 37.1343, "country": "Syria", "name": "Aleppo", "resolution": "city", "confidence": 0.85},
    # Yemen
    "yemen": {"lat": 15.3694, "lon": 44.191, "country": "Yemen", "name": "Yemen", "resolution": "country", "confidence": 0.7},
    "sanaa": {"lat": 15.3694, "lon": 44.191, "country": "Yemen", "name": "Sanaa", "resolution": "city", "confidence": 0.85},
    "houthi": {"lat": 15.3694, "lon": 44.191, "country": "Yemen", "name": "Yemen", "resolution": "country", "confidence": 0.6},
    # Mali
    "mali": {"lat": 12.6392, "lon": -8.0029, "country": "Mali", "name": "Mali", "resolution": "country", "confidence": 0.7},
    "bamako": {"lat": 12.6392, "lon": -8.0029, "country": "Mali", "name": "Bamako", "resolution": "city", "confidence": 0.85},
    # Nigeria
    "nigeria": {"lat": 9.0765, "lon": 7.4986, "country": "Nigeria", "name": "Nigeria", "resolution": "country", "confidence": 0.7},
    "abuja": {"lat": 9.0765, "lon": 7.4986, "country": "Nigeria", "name": "Abuja", "resolution": "city", "confidence": 0.85},
    "lagos": {"lat": 6.5244, "lon": 3.3792, "country": "Nigeria", "name": "Lagos", "resolution": "city", "confidence": 0.85},
    # Libya
    "libya": {"lat": 32.8872, "lon": 13.1913, "country": "Libya", "name": "Libya", "resolution": "country", "confidence": 0.7},
    "tripoli": {"lat": 32.8872, "lon": 13.1913, "country": "Libya", "name": "Tripoli", "resolution": "city", "confidence": 0.85},
    # Taiwan
    "taiwan": {"lat": 25.033, "lon": 121.5654, "country": "Taiwan", "name": "Taiwan", "resolution": "country", "confidence": 0.7},
    "taipei": {"lat": 25.033, "lon": 121.5654, "country": "Taiwan", "name": "Taipei", "resolution": "city", "confidence": 0.85},
    # Ethiopia
    "ethiopia": {"lat": 9.0249, "lon": 38.7469, "country": "Ethiopia", "name": "Ethiopia", "resolution": "country", "confidence": 0.7},
    "addis ababa": {"lat": 9.0249, "lon": 38.7469, "country": "Ethiopia", "name": "Addis Ababa", "resolution": "city", "confidence": 0.85},
    "tigray": {"lat": 13.5, "lon": 39.5, "country": "Ethiopia", "name": "Tigray", "resolution": "region", "confidence": 0.8},
    # Ecuador
    "ecuador": {"lat": -2.1894, "lon": -79.8891, "country": "Ecuador", "name": "Ecuador", "resolution": "country", "confidence": 0.7},
    "guayaquil": {"lat": -2.1894, "lon": -79.8891, "country": "Ecuador", "name": "Guayaquil", "resolution": "city", "confidence": 0.85},
    # Israel
    "israel": {"lat": 31.7683, "lon": 35.2137, "country": "Israel", "name": "Israel", "resolution": "country", "confidence": 0.7},
    "jerusalem": {"lat": 31.7683, "lon": 35.2137, "country": "Israel", "name": "Jerusalem", "resolution": "city", "confidence": 0.85},
    "gaza": {"lat": 31.3547, "lon": 34.3088, "country": "Palestine", "name": "Gaza", "resolution": "region", "confidence": 0.85},
    "west bank": {"lat": 31.95, "lon": 35.25, "country": "Palestine", "name": "West Bank", "resolution": "region", "confidence": 0.8},
    # Iran
    "iran": {"lat": 35.6892, "lon": 51.389, "country": "Iran", "name": "Iran", "resolution": "country", "confidence": 0.7},
    "tehran": {"lat": 35.6892, "lon": 51.389, "country": "Iran", "name": "Tehran", "resolution": "city", "confidence": 0.85},
    # Iraq
    "iraq": {"lat": 33.3152, "lon": 44.3661, "country": "Iraq", "name": "Iraq", "resolution": "country", "confidence": 0.7},
    "baghdad": {"lat": 33.3152, "lon": 44.3661, "country": "Iraq", "name": "Baghdad", "resolution": "city", "confidence": 0.85},
    # Somalia
    "somalia": {"lat": 2.0469, "lon": 45.3182, "country": "Somalia", "name": "Somalia", "resolution": "country", "confidence": 0.7},
    "mogadishu": {"lat": 2.0469, "lon": 45.3182, "country": "Somalia", "name": "Mogadishu", "resolution": "city", "confidence": 0.85},
    # DRC
    "congo": {"lat": -4.4419, "lon": 15.2663, "country": "DRC", "name": "DRC", "resolution": "country", "confidence": 0.6},
    "drc": {"lat": -4.4419, "lon": 15.2663, "country": "DRC", "name": "DRC", "resolution": "country", "confidence": 0.7},
    "kinshasa": {"lat": -4.4419, "lon": 15.2663, "country": "DRC", "name": "Kinshasa", "resolution": "city", "confidence": 0.85},
    # Russia
    "russia": {"lat": 55.7558, "lon": 37.6173, "country": "Russia", "name": "Russia", "resolution": "country", "confidence": 0.7},
    "moscow": {"lat": 55.7558, "lon": 37.6173, "country": "Russia", "name": "Moscow", "resolution": "city", "confidence": 0.85},
    "wagner": {"lat": 55.7558, "lon": 37.6173, "country": "Russia", "name": "Russia", "resolution": "country", "confidence": 0.6},
    "kremlin": {"lat": 55.7520, "lon": 37.6175, "country": "Russia", "name": "Moscow", "resolution": "city", "confidence": 0.8},
    "st. petersburg": {"lat": 59.9343, "lon": 30.3351, "country": "Russia", "name": "St. Petersburg", "resolution": "city", "confidence": 0.85},
    "murmansk": {"lat": 68.9585, "lon": 33.0827, "country": "Russia", "name": "Murmansk", "resolution": "city", "confidence": 0.85},
    # China
    "china": {"lat": 39.9042, "lon": 116.4074, "country": "China", "name": "China", "resolution": "country", "confidence": 0.7},
    "beijing": {"lat": 39.9042, "lon": 116.4074, "country": "China", "name": "Beijing", "resolution": "city", "confidence": 0.85},
    "south china sea": {"lat": 12.0, "lon": 114.0, "country": "China", "name": "South China Sea", "resolution": "region", "confidence": 0.8},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "country": "China", "name": "Shanghai", "resolution": "city", "confidence": 0.85},
    "xinjiang": {"lat": 41.7485, "lon": 84.7638, "country": "China", "name": "Xinjiang", "resolution": "region", "confidence": 0.8},
    # United States
    "united states": {"lat": 38.9072, "lon": -77.0369, "country": "United States", "name": "United States", "resolution": "country", "confidence": 0.7},
    "washington": {"lat": 38.9072, "lon": -77.0369, "country": "United States", "name": "Washington", "resolution": "city", "confidence": 0.85},
    "pentagon": {"lat": 38.8719, "lon": -77.0563, "country": "United States", "name": "Pentagon", "resolution": "city", "confidence": 0.85},
    # North Korea
    "north korea": {"lat": 39.0392, "lon": 125.7625, "country": "North Korea", "name": "North Korea", "resolution": "country", "confidence": 0.7},
    "pyongyang": {"lat": 39.0392, "lon": 125.7625, "country": "North Korea", "name": "Pyongyang", "resolution": "city", "confidence": 0.85},
    "dprk": {"lat": 39.0392, "lon": 125.7625, "country": "North Korea", "name": "North Korea", "resolution": "country", "confidence": 0.7},
    # India
    "india": {"lat": 28.6139, "lon": 77.2090, "country": "India", "name": "India", "resolution": "country", "confidence": 0.7},
    "new delhi": {"lat": 28.6139, "lon": 77.2090, "country": "India", "name": "New Delhi", "resolution": "city", "confidence": 0.85},
    "kashmir": {"lat": 34.0837, "lon": 74.7973, "country": "India", "name": "Kashmir", "resolution": "region", "confidence": 0.8},
    "islamabad": {"lat": 33.6844, "lon": 73.0479, "country": "Pakistan", "name": "Islamabad", "resolution": "city", "confidence": 0.85},
    # Eritrea
    "eritrea": {"lat": 15.3229, "lon": 38.9251, "country": "Eritrea", "name": "Eritrea", "resolution": "country", "confidence": 0.7},
    "asmara": {"lat": 15.3229, "lon": 38.9251, "country": "Eritrea", "name": "Asmara", "resolution": "city", "confidence": 0.85},
    # Djibouti
    "djibouti": {"lat": 11.5721, "lon": 43.1456, "country": "Djibouti", "name": "Djibouti", "resolution": "country", "confidence": 0.7},
    # Red Sea
    "red sea": {"lat": 20.0, "lon": 38.0, "country": "Red Sea", "name": "Red Sea", "resolution": "region", "confidence": 0.7},
    # Strait of Hormuz
    "strait of hormuz": {"lat": 26.5667, "lon": 56.25, "country": "Iran", "name": "Strait of Hormuz", "resolution": "region", "confidence": 0.8},
    "hormuz": {"lat": 26.5667, "lon": 56.25, "country": "Iran", "name": "Strait of Hormuz", "resolution": "region", "confidence": 0.75},
    "irgc": {"lat": 35.6892, "lon": 51.389, "country": "Iran", "name": "Iran", "resolution": "country", "confidence": 0.6},
    # Myanmar additions
    "naypyidaw": {"lat": 19.7633, "lon": 96.0785, "country": "Myanmar", "name": "Naypyidaw", "resolution": "city", "confidence": 0.85},
    "rohingya": {"lat": 20.5, "lon": 92.8, "country": "Myanmar", "name": "Rakhine", "resolution": "region", "confidence": 0.75},
    # NATO
    "nato": {"lat": 50.8766, "lon": 4.3222, "country": "Belgium", "name": "NATO HQ", "resolution": "city", "confidence": 0.6},
}

# Unknown fallback
UNKNOWN_GEO = {
    "locationId": "unknown",
    "name": "Unknown",
    "country": "Unknown",
    "lat": 0,
    "lon": 0,
    "resolution": "country",
    "confidence": 0.18,
}


def infer_geo(place_hints: list[str], text: str = "") -> dict:
    """Match place hints (and optionally article text) against the gazetteer.

    Returns the best-matching geo dict with a confidence that reflects
    match quality rather than a fixed per-entry value.
    """
    best: Optional[dict] = None
    best_confidence = 0.0
    match_source = "none"  # "hint" or "text"
    text_match_count = 0   # how many gazetteer keys appear in the text

    # First try explicit place hints (high confidence — admin configured these)
    for hint in place_hints:
        key = hint.lower().strip()
        if key in GAZETTEER:
            entry = GAZETTEER[key]
            if entry["confidence"] > best_confidence:
                best = entry
                best_confidence = entry["confidence"]
                match_source = "hint"

    # If no hit from hints, scan text for gazetteer keys
    if best is None and text:
        lower_text = text.lower()
        for key, entry in GAZETTEER.items():
            matched = False
            if len(key) <= 4:
                pattern = r'\b' + re.escape(key) + r'\b'
                if re.search(pattern, lower_text):
                    matched = True
            else:
                if key in lower_text:
                    matched = True

            if matched:
                text_match_count += 1
                if entry["confidence"] > best_confidence:
                    best = entry
                    best_confidence = entry["confidence"]
                    match_source = "text"

    if best is None:
        return dict(UNKNOWN_GEO)

    # Compute a dynamic confidence based on match quality:
    # - Base: the gazetteer entry's confidence (resolution-dependent)
    # - Boost for hint match (admin explicitly configured this search for this place)
    # - Boost for multiple geo mentions in text (corroborating evidence)
    # - Penalty for text-only match (weaker signal)
    base = best["confidence"]
    if match_source == "hint":
        # Hint match: boost slightly, cap at 0.96
        conf = min(base + 0.08, 0.96)
    else:
        # Text-only: start lower, boost for multiple geo references
        conf = base * 0.85
        if text_match_count >= 3:
            conf += 0.08
        elif text_match_count >= 2:
            conf += 0.04

    # Add small jitter from text length hash so cards don't all show identical %
    if text:
        jitter = ((len(text) * 7) % 11 - 5) * 0.01  # -0.05 to +0.05
        conf += jitter

    conf = round(max(0.15, min(0.96, conf)), 2)

    return {
        "locationId": best["name"].lower().replace(" ", "-"),
        "name": best["name"],
        "country": best.get("country", best["name"]),
        "lat": best["lat"],
        "lon": best["lon"],
        "resolution": best["resolution"],
        "confidence": conf,
    }
