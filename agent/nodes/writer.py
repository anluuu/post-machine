"""
PostWriter node.

Synthesises persona summary + research brief into a LinkedIn post
matching Wagner's established voice and format conventions.
"""

from __future__ import annotations

import re

from langchain_openai import ChatOpenAI
from rich.console import Console

from agent.config import AppConfig
from agent.hooks import run_hook
from agent.state import PostState

console = Console()

_WRITER_PROMPT = """\
You are writing a LinkedIn post for a software engineer named Wagner.

PERSONA SUMMARY (writing style, voice, expertise):
{persona_summary}

RESEARCH BRIEF (the topic and key facts to use):
{research_summary}

POST REQUIREMENTS:
- Tone: {tone}
- Length: {min_words}–{max_words} words
- Style rules:
{style}

Write the complete LinkedIn post in Markdown.
Start with the H1 title (# Title Here).
End with 2–4 hashtags on the last line.
Do not include any preamble, metadata, or explanation — just the post.
"""


def _extract_topic(content: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown Topic"


def post_writer(state: PostState, app_config: AppConfig, llm: ChatOpenAI) -> PostState:
    run_hook("pre_write_post", app_config.hooks.pre_write_post)

    response = llm.invoke(
        _WRITER_PROMPT.format(
            persona_summary=state.get("persona_summary", ""),
            research_summary=state.get("research_summary", ""),
            tone=app_config.post.tone,
            min_words=app_config.post.min_words,
            max_words=app_config.post.max_words,
            style=app_config.post.style,
        )
    )
    post_content = response.content.strip()
    topic = _extract_topic(post_content)

    console.print(f"[green]PostWriter[/green] draft: [bold]{topic}[/bold]")

    run_hook("post_write_post", app_config.hooks.post_write_post, stdin_content=post_content)

    return {
        "current_post": post_content,
        "post_topic": topic,
        "retry_count": 0,
        "best_score": 0,
        "best_post": post_content,
    }
