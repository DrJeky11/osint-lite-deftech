from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, HTTPException
import httpx

from models import NewsRequest, NewsResponse, ArticlesResponse, Article
from news_fetcher import build_query, fetch_news
from summarizer import summarize

app = FastAPI(title="News Summary API", version="0.1.0")

def _build_description(req: NewsRequest) -> str:
    bits = [f"topics={req.topics}"]
    if req.location:
        bits.append(f"location={req.location}")
    if req.start_date or req.end_date:
        bits.append(f"dates={req.start_date}..{req.end_date}")
    return ", ".join(bits)

async def _fetch(req: NewsRequest) -> tuple[str, list[dict]]:
    query = build_query(req.topics, req.start_date, req.end_date, req.location)
    try:
        articles = await fetch_news(
            query,
            country=req.country,
            language=req.language,
            max_articles=req.max_articles,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"News fetch failed: {e}")
    return query, articles

@app.post("/articles", response_model=ArticlesResponse)
async def get_articles(req: NewsRequest):
    """Fetch and return articles only — no LLM summary."""
    query, articles = await _fetch(req)
    return ArticlesResponse(
        query=query,
        article_count=len(articles),
        articles=[Article(**a) for a in articles],
    )

@app.post("/summarize", response_model=NewsResponse)
async def summarize_news(req: NewsRequest):
    """Fetch articles and return them alongside an LLM summary."""
    query, articles = await _fetch(req)
    summary = await summarize(
        articles,
        request_description=_build_description(req),
        question=req.question,
    )
    return NewsResponse(
        query=query,
        article_count=len(articles),
        articles=[Article(**a) for a in articles],
        summary=summary,
    )

@app.get("/health")
async def health():
    return {"status": "ok"}