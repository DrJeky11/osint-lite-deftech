from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class NewsRequest(BaseModel):
    topics: list[str] = Field(..., min_length=1, description="Topics/keywords to search")
    question: Optional[str] = Field(
        None,
        description="Plain-language question to guide the summary, e.g. 'How are allies responding?'"
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = Field(None, description="Free-text location, e.g. 'Ukraine' or 'San Francisco'")
    country: str = Field("US", description="Google News country code, e.g. 'US', 'GB', 'DE'")
    language: str = Field("en", description="Google News language code")
    max_articles: int = Field(20, ge=1, le=100)

class Article(BaseModel):
    title: str
    link: str
    published: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None

class ArticlesResponse(BaseModel):
    query: str
    article_count: int
    articles: list[Article]

class NewsResponse(BaseModel):
    query: str
    article_count: int
    articles: list[Article]
    summary: str


class ScheduleConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = 60  # 15, 30, 60, 120, 360, 720, 1440