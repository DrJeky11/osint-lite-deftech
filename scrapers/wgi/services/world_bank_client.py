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
WGI_BULK_CSV_URL = "https://databank.worldbank.org/data/download/WGI_CSV.zip"

DIMENSION_CONFIG = {
    GovernanceDimension.voice_accountability: {
        WGIMetric.percentile_rank: "GOV_WGI_VA.SC",
        WGIMetric.estimate: "GOV_WGI_VA.EST",
    },
    GovernanceDimension.political_stability: {
        WGIMetric.percentile_rank: "GOV_WGI_PV.SC",
        WGIMetric.estimate: "GOV_WGI_PV.EST",
    },
    GovernanceDimension.government_effectiveness: {
        WGIMetric.percentile_rank: "GOV_WGI_GE.SC",
        WGIMetric.estimate: "GOV_WGI_GE.EST",
    },
    GovernanceDimension.regulatory_quality: {
        WGIMetric.percentile_rank: "GOV_WGI_RQ.SC",
        WGIMetric.estimate: "GOV_WGI_RQ.EST",
    },
    GovernanceDimension.rule_of_law: {
        WGIMetric.percentile_rank: "GOV_WGI_RL.SC",
        WGIMetric.estimate: "GOV_WGI_RL.EST",
    },
    GovernanceDimension.control_of_corruption: {
        WGIMetric.percentile_rank: "GOV_WGI_CC.SC",
        WGIMetric.estimate: "GOV_WGI_CC.EST",
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
        response = await client.get(WGI_BULK_CSV_URL)
        response.raise_for_status()

    datasets = _parse_wgi_bulk_zip(response.content)
    _indicator_cache.update(datasets)
    dataset = _indicator_cache.get(indicator)
    if dataset is None:
        raise ValueError(f"Indicator {indicator} was not found in the WGI bulk dataset")
    return dataset


def _parse_wgi_bulk_zip(content: bytes) -> dict[str, dict]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if "WGICSV.csv" not in archive.namelist():
            raise ValueError("WGICSV.csv was not found in the World Bank WGI download")

        with archive.open("WGICSV.csv") as file_handle:
            text_handle = io.TextIOWrapper(file_handle, encoding="utf-8-sig")
            reader = csv.reader(text_handle)
            rows = list(reader)

    header_index = next((idx for idx, row in enumerate(rows) if row and row[0] == "Country Name"), None)
    if header_index is None:
        raise ValueError("Unexpected CSV structure for the World Bank WGI bulk dataset")

    header = rows[header_index]
    year_columns = {
        index: int(column)
        for index, column in enumerate(header)
        if column.isdigit() and len(column) == 4
    }

    parsed_datasets: dict[str, dict] = {}
    for row in rows[header_index + 1 :]:
        if len(row) < 4:
            continue

        country_name = row[0].strip()
        country_code = row[1].strip().upper()
        row_indicator_name = row[2].strip()
        row_indicator_code = row[3].strip()

        if not country_name or not country_code or not row_indicator_code:
            continue

        values: dict[int, float] = {}
        for column_index, year in year_columns.items():
            if column_index >= len(row):
                continue
            raw_value = row[column_index].strip()
            if not raw_value:
                continue
            values[year] = float(raw_value)

        if not values:
            continue

        dataset = parsed_datasets.setdefault(
            row_indicator_code,
            {
                "indicator_name": row_indicator_name or row_indicator_code,
                "rows": {},
            },
        )
        dataset["rows"][country_code] = {
            "country_name": country_name,
            "values": values,
        }

    return parsed_datasets
