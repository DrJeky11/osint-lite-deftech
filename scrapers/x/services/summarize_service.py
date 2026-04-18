from typing import Optional

from groq import Groq


async def summarize_posts(
    posts: list[dict],
    request_description: str,
    question: Optional[str] = None,
) -> str:
    if not posts:
        return "No X posts found for the given query."

    formatted = "\n\n".join(
        f"[{i + 1}] @{post['author']['username']}\n"
        f"Date: {post.get('created_at') or 'Unknown'}\n"
        f"Likes: {post.get('likes', 0)} | Reposts: {post.get('reposts', 0)} | Replies: {post.get('replies', 0)} | Quotes: {post.get('quotes', 0)}\n"
        f"{post.get('text') or ''}"
        for i, post in enumerate(posts)
    )

    question_block = (
        f"The user's specific question is:\n{question}\n\n"
        f"Focus your summary on answering this question using only the posts below. "
        f"If the posts do not answer it, say so plainly.\n\n"
        if question
        else ""
    )

    prompt = (
        f"The user requested X posts on: {request_description}\n\n"
        f"{question_block}"
        f"Below are {len(posts)} X posts that matched the search. "
        f"Write a concise, factual summary of what these posts are saying, grouping by recurring themes, "
        f"claims, or notable differences in perspective. Do not invent facts beyond the provided posts.\n\n"
        f"POSTS:\n{formatted}"
    )

    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content
