"""High-level interface for fetching WGI governance data."""

import logging

from .client import (
    DIMENSION_CONFIG,
    DIMENSION_LABELS,
    GovernanceDimension,
    WGIMetric,
    fetch_indicator_data,
    resolve_countries,
)

logger = logging.getLogger(__name__)

ALL_DIMENSIONS = list(GovernanceDimension)


async def fetch_wgi_data(
    countries: list[str],
    dimensions: list[str] | None = None,
    metric: str = "percentile_rank",
) -> list[dict]:
    """Fetch WGI governance data for given countries.

    Args:
        countries: Country names or ISO codes to look up.
        dimensions: Subset of governance dimensions to fetch (None = all 6).
        metric: "percentile_rank" or "estimate".

    Returns:
        List of dicts, each with:
        {
            "country": str,
            "country_code": str,
            "dimension": str,
            "dimension_label": str,
            "metric": str,
            "value": float,
            "year": int,
        }
    """
    wgi_metric = WGIMetric(metric)

    # Resolve which dimensions to query
    if dimensions is not None:
        selected = []
        for d in dimensions:
            try:
                selected.append(GovernanceDimension(d))
            except ValueError:
                logger.warning("Unknown dimension '%s', skipping", d)
        if not selected:
            logger.error("No valid dimensions provided")
            return []
    else:
        selected = ALL_DIMENSIONS

    # Resolve countries (partial failures are tolerated)
    resolved, unresolved = await resolve_countries(countries)
    if unresolved:
        logger.warning("Could not resolve countries: %s", ", ".join(unresolved))
    if not resolved:
        logger.error("No countries could be resolved from: %s", countries)
        return []

    country_lookup = {c["iso3_code"]: c for c in resolved}
    country_codes = list(country_lookup.keys())

    results: list[dict] = []

    for dimension in selected:
        indicator = DIMENSION_CONFIG[dimension][wgi_metric]
        try:
            indicator_name, data = await fetch_indicator_data(country_codes, indicator)
        except Exception:
            logger.exception(
                "Failed to fetch indicator %s for dimension %s, skipping",
                indicator,
                dimension.value,
            )
            continue

        for iso3_code, year_values in data.items():
            if not year_values:
                continue

            country_info = country_lookup.get(iso3_code)
            if country_info is None:
                continue

            # Use the latest available year
            latest_year = max(year_values.keys())
            value = year_values[latest_year]

            results.append(
                {
                    "country": country_info["name"],
                    "country_code": iso3_code,
                    "dimension": dimension.value,
                    "dimension_label": DIMENSION_LABELS[dimension],
                    "metric": wgi_metric.value,
                    "value": value,
                    "year": latest_year,
                }
            )

    return results
