import csv
import io
import zipfile

import httpx

try:
    from ..models import GovernanceDimension, WGIMetric
except ImportError:
    from models import GovernanceDimension, WGIMetric

BASE_URL = "https://api.worldbank.org/v2"
TIMEOUT = 30.0

DIMENSION_CONFIG = {
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

_country_cache: dict[str, dict] | None = None
_indicator_cache: dict[str, dict] = {}


def _normalize_country_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _country_aliases(country: dict) -> set[str]:
    aliases = {
        _normalize_country_name(country["name"]),
        country["iso2_code"].lower(),
        country["iso3_code"].lower(),
    }

    special_cases = {
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

    aliases.update(special_cases.get(_normalize_country_name(country["name"]), set()))
    return aliases


async def _get_country_index() -> dict[str, dict]:
    global _country_cache
    if _country_cache is not None:
        return _country_cache

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
    return index


async def resolve_countries(countries: list[str]) -> list[dict]:
    index = await _get_country_index()
    resolved: list[dict] = []
    unresolved: list[str] = []
    seen: set[str] = set()

    for requested in countries:
        normalized = _normalize_country_name(requested)
        country = index.get(normalized)
        if country is None:
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

    if unresolved:
        raise ValueError(f"Unrecognized countries: {', '.join(unresolved)}")
    if not resolved:
        raise ValueError("At least one valid country is required")

    return resolved


async def fetch_indicator_data(
    country_codes: list[str],
    indicator: str,
) -> tuple[str, list[dict]]:
    dataset = await _get_indicator_dataset(indicator)
    requested_codes = {code.upper() for code in country_codes}
    observations: list[dict] = []

    for iso3_code in sorted(requested_codes):
        row = dataset["rows"].get(iso3_code)
        if row is None:
            continue

        year, value = max(row["values"].items(), key=lambda item: item[0])
        observations.append(
            {
                "iso3_code": iso3_code,
                "year": year,
                "value": value,
            }
        )

    observations.sort(key=lambda item: (item["iso3_code"], -item["year"]))
    return dataset["indicator_name"], observations


async def _get_indicator_dataset(indicator: str) -> dict:
    cached = _indicator_cache.get(indicator)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(
            f"{BASE_URL}/en/indicator/{indicator}",
            params={"downloadformat": "csv"},
        )
        response.raise_for_status()

    dataset = _parse_indicator_zip(indicator, response.content)
    _indicator_cache[indicator] = dataset
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
    for row in rows[header_index + 1 :]:
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
    if indicator.endswith(".PER.RNK") and value > 100:
        return value / 10.0
    return value
