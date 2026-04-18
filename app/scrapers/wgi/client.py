"""World Bank WGI (Worldwide Governance Indicators) API client.

Handles country resolution, indicator data fetching, CSV parsing,
and caching with TTL expiration.
"""

import csv
import io
import logging
import time
import zipfile
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.worldbank.org/v2"
TIMEOUT = 30.0
CACHE_TTL_SECONDS = 86400  # 24 hours


class WGIMetric(str, Enum):
    percentile_rank = "percentile_rank"
    estimate = "estimate"


class GovernanceDimension(str, Enum):
    voice_accountability = "voice_accountability"
    political_stability = "political_stability"
    government_effectiveness = "government_effectiveness"
    regulatory_quality = "regulatory_quality"
    rule_of_law = "rule_of_law"
    control_of_corruption = "control_of_corruption"


DIMENSION_LABELS: dict[GovernanceDimension, str] = {
    GovernanceDimension.voice_accountability: "Voice & Accountability",
    GovernanceDimension.political_stability: "Political Stability & Absence of Violence",
    GovernanceDimension.government_effectiveness: "Government Effectiveness",
    GovernanceDimension.regulatory_quality: "Regulatory Quality",
    GovernanceDimension.rule_of_law: "Rule of Law",
    GovernanceDimension.control_of_corruption: "Control of Corruption",
}

DIMENSION_CONFIG: dict[GovernanceDimension, dict[WGIMetric, str]] = {
    GovernanceDimension.voice_accountability: {
        WGIMetric.percentile_rank: "VA.PER.RNK",
        WGIMetric.estimate: "VA.EST",
    },
    GovernanceDimension.political_stability: {
        WGIMetric.percentile_rank: "PV.PER.RNK",
        WGIMetric.estimate: "PV.EST",
    },
    GovernanceDimension.government_effectiveness: {
        WGIMetric.percentile_rank: "GE.PER.RNK",
        WGIMetric.estimate: "GE.EST",
    },
    GovernanceDimension.regulatory_quality: {
        WGIMetric.percentile_rank: "RQ.PER.RNK",
        WGIMetric.estimate: "RQ.EST",
    },
    GovernanceDimension.rule_of_law: {
        WGIMetric.percentile_rank: "RL.PER.RNK",
        WGIMetric.estimate: "RL.EST",
    },
    GovernanceDimension.control_of_corruption: {
        WGIMetric.percentile_rank: "CC.PER.RNK",
        WGIMetric.estimate: "CC.EST",
    },
}

# ---- TTL cache ----

_country_cache: dict | None = None
_country_cache_ts: float = 0.0

_indicator_cache: dict[str, dict] = {}
_indicator_cache_ts: dict[str, float] = {}


def _cache_valid(timestamp: float) -> bool:
    return timestamp > 0 and (time.monotonic() - timestamp) < CACHE_TTL_SECONDS


# ---- Country helpers ----

_SPECIAL_ALIASES: dict[str, set[str]] = {
    "united states": {"usa", "us", "united states of america"},
    "united kingdom": {"uk", "great britain", "britain"},
    "russian federation": {"russia"},
    "egypt, arab rep.": {"egypt"},
    "iran, islamic rep.": {"iran"},
    "korea, rep.": {"south korea", "republic of korea"},
    "korea, dem. people's rep.": {"north korea", "dprk"},
    "slovak republic": {"slovakia"},
    "czechia": {"czech republic"},
    "turkiye": {"turkey"},
    "venezuela, rb": {"venezuela"},
    "yemen, rep.": {"yemen"},
    "bahamas, the": {"bahamas"},
    "gambia, the": {"gambia"},
    "congo, dem. rep.": {"democratic republic of the congo", "dr congo", "drc"},
    "congo, rep.": {"republic of the congo", "congo republic"},
}


def _normalize_country_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _country_aliases(country: dict) -> set[str]:
    name_norm = _normalize_country_name(country["name"])
    aliases = {
        name_norm,
        country["iso2_code"].lower(),
        country["iso3_code"].lower(),
    }
    aliases.update(_SPECIAL_ALIASES.get(name_norm, set()))
    return aliases


async def _get_country_index() -> dict[str, dict]:
    global _country_cache, _country_cache_ts

    if _country_cache is not None and _cache_valid(_country_cache_ts):
        return _country_cache

    logger.info("Fetching World Bank country list")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{BASE_URL}/country",
            params={"format": "json", "per_page": 400},
        )
        response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Unexpected response while loading World Bank country metadata")

    countries = payload[1]
    index: dict[str, dict] = {}
    for item in countries:
        if not isinstance(item, dict):
            continue
        if item.get("region", {}).get("value") == "Aggregates":
            continue

        country = {
            "name": item.get("name"),
            "iso2_code": item.get("iso2Code"),
            "iso3_code": item.get("id"),
        }
        if not country["name"] or not country["iso2_code"] or not country["iso3_code"]:
            continue

        for alias in _country_aliases(country):
            index[alias] = country

    _country_cache = index
    _country_cache_ts = time.monotonic()
    logger.info("Cached %d country alias entries", len(index))
    return index


async def resolve_countries(countries: list[str]) -> tuple[list[dict], list[str]]:
    """Resolve country names/codes to World Bank country records.

    Returns (resolved, unresolved) -- does not crash on partial failures.
    """
    index = await _get_country_index()
    resolved: list[dict] = []
    unresolved: list[str] = []
    seen: set[str] = set()

    for requested in countries:
        normalized = _normalize_country_name(requested)
        country = index.get(normalized)
        if country is None:
            logger.warning("Could not resolve country: %s", requested)
            unresolved.append(requested)
            continue

        iso3_code = country["iso3_code"]
        if iso3_code in seen:
            continue
        seen.add(iso3_code)

        resolved.append(
            {
                "requested": requested,
                "name": country["name"],
                "iso2_code": country["iso2_code"],
                "iso3_code": iso3_code,
            }
        )

    return resolved, unresolved


# ---- Indicator data ----

async def fetch_indicator_data(
    country_codes: list[str],
    indicator: str,
) -> tuple[str, dict[str, dict[int, float]]]:
    """Fetch indicator data for a set of country codes.

    Returns (indicator_name, data) where data maps
    iso3_code -> {year: value, ...} with ALL available years.
    """
    dataset = await _get_indicator_dataset(indicator)
    requested_codes = {code.upper() for code in country_codes}
    result: dict[str, dict[int, float]] = {}

    for iso3_code in sorted(requested_codes):
        row = dataset["rows"].get(iso3_code)
        if row is None:
            logger.debug("No data for country %s / indicator %s", iso3_code, indicator)
            continue
        result[iso3_code] = dict(row["values"])

    return dataset["indicator_name"], result


async def _get_indicator_dataset(indicator: str) -> dict:
    cached = _indicator_cache.get(indicator)
    if cached is not None and _cache_valid(_indicator_cache_ts.get(indicator, 0)):
        return cached

    logger.info("Downloading indicator dataset: %s", indicator)
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(
            f"{BASE_URL}/en/indicator/{indicator}",
            params={"downloadformat": "csv"},
        )
        response.raise_for_status()

    dataset = _parse_indicator_zip(indicator, response.content)
    _indicator_cache[indicator] = dataset
    _indicator_cache_ts[indicator] = time.monotonic()
    return dataset


def _parse_indicator_zip(indicator: str, content: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        data_filenames = [
            name
            for name in archive.namelist()
            if name.startswith("API_") and name.endswith(".csv")
        ]
        if not data_filenames:
            raise ValueError(f"No CSV data file found for indicator {indicator}")

        data_filename = data_filenames[0]
        with archive.open(data_filename) as file_handle:
            text_handle = io.TextIOWrapper(file_handle, encoding="utf-8-sig")
            reader = csv.reader(text_handle)
            rows = list(reader)

    header_index = next(
        (idx for idx, row in enumerate(rows) if row and row[0] == "Country Name"),
        None,
    )
    if header_index is None:
        raise ValueError(f"Unexpected CSV structure for indicator {indicator}")

    header = rows[header_index]
    year_columns = {
        index: int(column)
        for index, column in enumerate(header)
        if column.isdigit() and len(column) == 4
    }

    indicator_name = indicator
    parsed_rows: dict[str, dict] = {}
    for row in rows[header_index + 1:]:
        if len(row) < 4:
            continue

        country_name = row[0].strip()
        country_code = row[1].strip().upper()
        row_indicator_name = row[2].strip()
        row_indicator_code = row[3].strip()

        if not country_name or not country_code:
            continue
        if row_indicator_code and row_indicator_code != indicator:
            continue

        values: dict[int, float] = {}
        for column_index, year in year_columns.items():
            if column_index >= len(row):
                continue
            raw_value = row[column_index].strip()
            if not raw_value:
                continue
            values[year] = _normalize_indicator_value(indicator, float(raw_value))

        if not values:
            continue

        indicator_name = row_indicator_name or indicator_name
        parsed_rows[country_code] = {
            "country_name": country_name,
            "values": values,
        }

    return {"indicator_name": indicator_name, "rows": parsed_rows}


def _normalize_indicator_value(indicator: str, value: float) -> float:
    # Percentile rank values should be 0-100.  Some World Bank CSV exports
    # contain values scaled to 0-1000 (likely an encoding artifact).  When a
    # percentile-rank value exceeds 100, divide by 10 to bring it back into
    # the expected 0-100 range.
    if indicator.endswith(".PER.RNK") and value > 100:
        return value / 10.0
    return value
