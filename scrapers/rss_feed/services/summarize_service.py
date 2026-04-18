from typing import Optional

from groq import Groq


async def summarize_entries(
    entries: list[dict],
    request_description: str,
    question: Optional[str] = None,
) -> str:
    if not entries:
        return "No RSS entries found for the given feed."

    formatted = "\n\n".join(
        f"[{i + 1}] {entry.get('title') or 'Untitled'}\n"
        f"Date: {entry.get('published') or entry.get('updated') or 'Unknown'}\n"
        f"Author: {entry.get('author') or 'Unknown'}\n"
        f"Link: {entry.get('link') or 'N/A'}\n"
        f"Categories: {', '.join(entry.get('categories', [])) or 'None'}\n"
        f"{entry.get('summary') or ''}"
        for i, entry in enumerate(entries)
    )

    question_block = (
        f"The user's specific question is:\n{question}\n\n"
        f"Focus your summary on answering this question using only the feed entries below. "
        f"If the entries do not answer it, say so plainly.\n\n"
        if question
        else ""
    )

    prompt = (
        f"The user requested RSS feed entries on: {request_description}\n\n"
        f"{question_block}"
        f"Below are {len(entries)} feed entries that matched the request. "
        f"Write a concise, factual summary of the feed content, grouping by recurring themes, "
        f"developments, or notable differences in emphasis. Do not invent facts beyond the provided entries.\n\n"
        f"ENTRIES:\n{formatted}"
    )

    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content
