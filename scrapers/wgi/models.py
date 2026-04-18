from enum import Enum
from pydantic import BaseModel, Field, field_validator


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


class WGIRequest(BaseModel):
    countries: list[str] = Field(
        ...,
        min_length=1,
        description="Country names or ISO country codes",
        examples=[["United States", "Canada", "DEU"]],
    )
    metric: WGIMetric = Field(
        WGIMetric.percentile_rank,
        description="Whether to return percentile ranks or estimates",
        examples=["percentile_rank"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "countries": ["United States", "Canada", "DEU"],
                "metric": "percentile_rank",
            }
        }
    }

    @field_validator("countries", mode="before")
    @classmethod
    def normalize_countries(cls, value):
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []

        if not isinstance(value, list):
            return value

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if cleaned:
                normalized.append(cleaned)

        return normalized

class WGICountry(BaseModel):
    requested: str
    name: str
    iso2_code: str
    iso3_code: str


class WGIObservation(BaseModel):
    country: WGICountry
    year: int
    value: float


class WGIResponse(BaseModel):
    dimension: GovernanceDimension
    metric: WGIMetric
    indicator: str
    indicator_name: str
    result_count: int
    results: list[WGIObservation]
