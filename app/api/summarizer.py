"""LLM summarizer — uses configurable OpenAI-compatible endpoint.

Defaults to Groq (llama-3.3-70b-versatile) but can be pointed at any
OpenAI-compatible API via the /config/llm endpoint or env vars.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger("summarizer")

LLM_CONFIG_PATH = Path(__file__).parent / "llm_config.json"


def _get_llm_config() -> dict:
    """Read LLM config, falling back to env vars."""
    import os
    defaults = {
        "endpoint": os.environ.get("LLM_ENDPOINT", "https://api.groq.com/openai/v1"),
        "apiKey": os.environ.get("GROQ_API_KEY", ""),
        "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
        "temperature": 0.3,
        "maxTokens": 4096,
    }
    if LLM_CONFIG_PATH.exists():
        try:
            stored = json.loads(LLM_CONFIG_PATH.read_text())
            return {**defaults, **stored}
        except Exception:
            pass
    return defaults


async def summarize(
    articles: list[dict],
    request_description: str,
    question: Optional[str] = None,
) -> str:
    if not articles:
        return "No articles found for the given query."

    cfg = _get_llm_config()
    endpoint = cfg["endpoint"].rstrip("/")
    api_key = cfg["apiKey"]
    model = cfg["model"]

    if not api_key:
        return "LLM API key not configured. Set it via Admin > AI / LLM or the GROQ_API_KEY env var."

    formatted = "\n\n".join(
        f"[{i+1}] {a['title']}\n"
        f"Source: {a.get('source') or 'Unknown'} | Date: {a.get('published') or 'Unknown'}\n"
        f"{a.get('description') or ''}"
        for i, a in enumerate(articles)
    )

    question_block = (
        f"The user's specific question is:\n{question}\n\n"
        f"Focus your summary on answering this question using the articles below. "
        f"If the articles don't address it, say so plainly.\n\n"
        if question else ""
    )

    prompt = (
        f"The user requested news on: {request_description}\n\n"
        f"{question_block}"
        f"Below are {len(articles)} article headlines and snippets. "
        f"Write a concise, factual summary of the key events, organized by theme "
        f"or chronology, and call out notable trends or disagreements between sources. "
        f"Do not invent facts beyond what's in the snippets.\n\n"
        f"ARTICLES:\n{formatted}"
    )

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": cfg.get("temperature", 0.3),
                    "max_tokens": cfg.get("maxTokens", 4096),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return f"LLM summarization failed: {e}"
