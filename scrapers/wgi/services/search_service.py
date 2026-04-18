try:
    from ..models import GovernanceDimension, WGICountry, WGIObservation, WGIRequest, WGIResponse
    from .world_bank_client import DIMENSION_CONFIG, fetch_indicator_data, resolve_countries
except ImportError:
    from models import GovernanceDimension, WGICountry, WGIObservation, WGIRequest, WGIResponse
    from services.world_bank_client import DIMENSION_CONFIG, fetch_indicator_data, resolve_countries


async def fetch_dimension_results(req: WGIRequest, dimension: GovernanceDimension) -> WGIResponse:
    indicator = DIMENSION_CONFIG[dimension][req.metric]
    resolved_countries = await resolve_countries(req.countries)
    country_lookup = {country["iso3_code"]: country for country in resolved_countries}

    indicator_name, observations = await fetch_indicator_data(
        country_codes=[country["iso3_code"] for country in resolved_countries],
        indicator=indicator,
    )

    results = [
        WGIObservation(
            country=WGICountry(
                requested=country_lookup[item["iso3_code"]]["requested"],
                name=country_lookup[item["iso3_code"]]["name"],
                iso2_code=country_lookup[item["iso3_code"]]["iso2_code"],
                iso3_code=country_lookup[item["iso3_code"]]["iso3_code"],
            ),
            year=item["year"],
            value=item["value"],
        )
        for item in observations
        if item["iso3_code"] in country_lookup
    ]

    return WGIResponse(
        dimension=dimension,
        metric=req.metric,
        indicator=indicator,
        indicator_name=indicator_name,
        result_count=len(results),
        results=results,
    )
