from dotenv import load_dotenv
load_dotenv()  # must come before importing summarizer

from fastapi import FastAPI, HTTPException
import httpx

from models import NewsRequest, NewsResponse, Article
from news_fetcher import build_query, fetch_news
from summarizer import summarize

app = FastAPI(title="News Summary API", version="0.1.0")

@app.post("/summarize", response_model=NewsResponse)
async def summarize_news(req: NewsRequest):
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

    description_bits = [f"topics={req.topics}"]
    if req.location:
        description_bits.append(f"location={req.location}")
    if req.start_date or req.end_date:
        description_bits.append(f"dates={req.start_date}..{req.end_date}")
    request_description = ", ".join(description_bits)

    summary = await summarize(articles, request_description)

    return NewsResponse(
        query=query,
        article_count=len(articles),
        articles=[Article(**a) for a in articles],
        summary=summary,
    )

@app.get("/health")
async def health():
    return {"status": "ok"}