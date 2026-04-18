from datetime import date
from typing import Optional

from pydantic import field_validator
from pydantic import BaseModel, Field


class BlueskyRequest(BaseModel):
    keywords: list[str] = Field(
        ...,
        min_length=1,
        description="Keywords to search for",
        examples=[["Iran", "US", "Trump"]],
    )
    question: Optional[str] = Field(
        None,
        description="Plain-language question to guide the summary",
        examples=["What is happening with Iran?"],
    )
    start_date: Optional[date] = Field(None, examples=["2026-04-17"])
    end_date: Optional[date] = Field(None, examples=["2026-04-18"])
    language: Optional[str] = Field(None, description="Language code, e.g. 'en'", examples=["en"])
    author: Optional[str] = Field(
        None,
        description="Optional Bluesky handle to filter by",
        examples=["nytimes.com"],
    )
    mention: Optional[str] = Field(
        None,
        description="Optional handle that must be mentioned",
        examples=["potus.bsky.social"],
    )
    domain: Optional[str] = Field(
        None,
        description="Optional linked domain filter",
        examples=["reuters.com"],
    )
    url: Optional[str] = Field(
        None,
        description="Optional exact linked URL filter",
        examples=["https://www.reuters.com/world/middle-east/"],
    )
    sort: str = Field("latest", pattern="^(latest|top)$", examples=["latest"])
    max_posts: int = Field(20, ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "keywords": ["Iran", "US", "Trump"],
                "question": "What is happening with Iran?",
                "start_date": "2026-04-17",
                "end_date": "2026-04-18",
                "language": "en",
                "sort": "latest",
                "max_posts": 20,
            }
        }
    }

    @field_validator("keywords", mode="before")
    @classmethod
    def normalize_keywords(cls, value):
        if not isinstance(value, list):
            return value

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            parts = [part.strip() for part in item.split(",")]
            normalized.extend(part for part in parts if part)

        return normalized

    @field_validator("language", "author", "mention", "domain", "url", mode="before")
    @classmethod
    def normalize_optional_filters(cls, value):
        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned or cleaned.lower() == "string":
            return None
        return cleaned


class BlueskyAuthor(BaseModel):
    handle: str
    display_name: Optional[str] = None
    did: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None


class BlueskyPost(BaseModel):
    uri: str
    cid: str
    url: Optional[str] = None
    text: str
    indexed_at: Optional[str] = None
    created_at: Optional[str] = None
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    quotes: int = 0
    languages: list[str] = Field(default_factory=list)
    author: BlueskyAuthor
    embed: Optional[dict] = None


class BlueskyPostsResponse(BaseModel):
    query: str
    post_count: int
    posts: list[BlueskyPost]


class BlueskySummaryResponse(BaseModel):
    query: str
    post_count: int
    posts: list[BlueskyPost]
    summary: str
