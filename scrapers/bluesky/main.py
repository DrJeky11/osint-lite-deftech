from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

try:
    from .routers.search import router as search_router
except ImportError:
    from routers.search import router as search_router

app = FastAPI(title="Bluesky Search API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
