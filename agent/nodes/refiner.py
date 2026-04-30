"""
PostRefiner node.

Takes QA feedback and the current draft, produces an improved version.
Increments retry_count.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from rich.console import Console

from agent.config import AppConfig
from agent.state import PostState

console = Console()

_REFINER_PROMPT = """\
You are improving a LinkedIn post based on reviewer feedback.

PERSONA (writing style to match):
{persona_summary}

CURRENT POST DRAFT:
{current_post}

REVIEWER FEEDBACK (fix exactly these issues):
{qa_feedback}

REQUIREMENTS:
- Tone: {tone}
- Length: {min_words}–{max_words} words
- Style rules:
{style}

Write the improved post. Keep what works. Fix only what the feedback identifies.
Start with the H1 title (# Title Here). End with 2–4 hashtags. Return only the post.
"""


def post_refiner(state: PostState, app_config: AppConfig, llm: ChatOpenAI) -> PostState:
    response = llm.invoke(
        _REFINER_PROMPT.format(
            persona_summary=state.get("persona_summary", ""),
            current_post=state.get("current_post", ""),
            qa_feedback=state.get("qa_feedback", ""),
            tone=app_config.post.tone,
            min_words=app_config.post.min_words,
            max_words=app_config.post.max_words,
            style=app_config.post.style,
        )
    )
    refined = response.content.strip()
    new_retry = state.get("retry_count", 0) + 1

    console.print(
        f"[yellow]PostRefiner[/yellow] refined "
        f"(attempt {new_retry}/{app_config.quality.max_retries})"
    )

    return {
        "current_post": refined,
        "retry_count": new_retry,
    }
