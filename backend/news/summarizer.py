import os
import anthropic

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. Create a .env file in the project root "
        "with ANTHROPIC_API_KEY=your-key, or set it in your environment."
    )

_client = anthropic.AsyncAnthropic(api_key=_api_key)

async def summarize(articles: list[dict], request_description: str) -> str:
    if not articles:
        return "No articles found for the given query."

    formatted = "\n\n".join(
        f"[{i+1}] {a['title']}\n"
        f"Source: {a.get('source') or 'Unknown'} | Date: {a.get('published') or 'Unknown'}\n"
        f"{a.get('description') or ''}"
        for i, a in enumerate(articles)
    )

    prompt = (
        f"The user requested news on: {request_description}\n\n"
        f"Below are {len(articles)} article headlines and snippets. "
        f"Write a concise, factual summary of the key events, organized by theme "
        f"or chronology, and call out notable trends or disagreements between sources. "
        f"Do not invent facts beyond what's in the snippets.\n\n"
        f"ARTICLES:\n{formatted}"
    )

    msg = await _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text