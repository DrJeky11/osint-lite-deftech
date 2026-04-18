from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class XRequest(BaseModel):
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
    start_date: Optional[date] = Field(
        None,
        description="Oldest date to include. X recent search only covers roughly the last 7 days.",
        examples=["2026-04-17"],
    )
    end_date: Optional[date] = Field(
        None,
        description="Newest date to include. X recent search only covers roughly the last 7 days.",
        examples=["2026-04-18"],
    )
    language: Optional[str] = Field(None, description="Language code, e.g. 'en'", examples=["en"])
    author: Optional[str] = Field(
        None,
        description="Optional X username to filter by, without the @",
        examples=["nytimes"],
    )
    mention: Optional[str] = Field(
        None,
        description="Optional username that must be mentioned, without the @",
        examples=["POTUS"],
    )
    domain: Optional[str] = Field(
        None,
        description="Optional linked domain filter",
        examples=["reuters.com"],
    )
    url: Optional[str] = Field(
        None,
        description="Optional linked URL filter",
        examples=["https://www.reuters.com/world/middle-east/"],
    )
    sort: str = Field("recency", pattern="^(recency|relevancy)$", examples=["recency"])
    max_posts: int = Field(20, ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "keywords": ["Iran", "US", "Trump"],
                "question": "What is happening with Iran?",
                "start_date": "2026-04-17",
                "end_date": "2026-04-18",
                "language": "en",
                "author": "nytimes",
                "sort": "recency",
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
        return cleaned.lstrip("@") if cleaned.startswith("@") else cleaned


class XAuthor(BaseModel):
    id: str
    username: str
    name: Optional[str] = None
    description: Optional[str] = None
    profile_image_url: Optional[str] = None


class XPost(BaseModel):
    id: str
    text: str
    url: str
    created_at: Optional[str] = None
    language: Optional[str] = None
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    quotes: int = 0
    bookmarks: int = 0
    impressions: Optional[int] = None
    author: XAuthor
    referenced_tweets: list[dict] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)


class XPostsResponse(BaseModel):
    query: str
    post_count: int
    posts: list[XPost]


class XSummaryResponse(BaseModel):
    query: str
    post_count: int
    posts: list[XPost]
    summary: str

