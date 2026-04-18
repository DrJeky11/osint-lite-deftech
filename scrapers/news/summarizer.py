import os
from typing import Optional

from groq import Groq

client = Groq()

async def summarize(
    articles: list[dict],
    request_description: str,
    question: Optional[str] = None,
) -> str:
    if not articles:
        return "No articles found for the given query."

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

    completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"{prompt}"
        }
    ]
    )
    #print(completion.choices[0].message.content)
    return completion.choices[0].message.content

