from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RSSRequest(BaseModel):
    feed_url: HttpUrl = Field(
        ...,
        description="The RSS or Atom feed URL to fetch",
        examples=["https://feeds.bbci.co.uk/news/world/rss.xml"],
    )
    question: Optional[str] = Field(
        None,
        description="Plain-language question to guide the summary",
        examples=["What are the main themes in this feed right now?"],
    )
    max_entries: int = Field(20, ge=1, le=100, description="Maximum number of feed entries to return")

    model_config = {
        "json_schema_extra": {
            "example": {
                "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
                "question": "What are the main themes in this feed right now?",
                "max_entries": 10,
            }
        }
    }

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value):
        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        return cleaned or None


class RSSFeedMetadata(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None


class RSSEntry(BaseModel):
    id: str
    title: str
    link: Optional[str] = None
    published: Optional[str] = None
    updated: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    categories: list[str] = Field(default_factory=list)


class RSSEntriesResponse(BaseModel):
    feed_url: str
    feed: RSSFeedMetadata
    entry_count: int
    entries: list[RSSEntry]


class RSSSummaryResponse(BaseModel):
    feed_url: str
    feed: RSSFeedMetadata
    entry_count: int
    entries: list[RSSEntry]
    summary: str

