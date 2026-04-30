"""
QAReviewer node.

Evaluates the current draft with structured output (Pydantic).
Returns score 1–10 and actionable feedback.
Tracks the best version across retries.
"""

from __future__ import annotations

import re

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from rich.console import Console

from agent.config import AppConfig
from agent.state import PostState

console = Console()


class QAResult(BaseModel):
    score: int = Field(..., ge=1, le=10, description="Quality score 1–10.")
    feedback: str = Field(..., description="Specific, actionable improvement notes.")
    passes: bool = Field(..., description="True if score meets publication threshold.")


_QA_PROMPT = """\
You are a senior LinkedIn content reviewer evaluating a post written by a software engineer.

PERSONA (voice/style the post should match):
{persona_summary}

POST TO REVIEW:
{post_content}

REVIEW CRITERIA (score 1–10 overall):
1. Voice match — sounds like a senior engineer, not a marketer (no buzzwords/hype)
2. Technical accuracy — claims are credible and grounded
3. Structure — clear flow, appropriate use of lists/headers
4. Engagement — would a technical professional stop scrolling for this?
5. Length — within {min_words}–{max_words} words
6. Hashtags — 2–4 relevant hashtags at the end

Score the post 1–10. Provide specific, actionable feedback (concise, max 100 words).
Set passes=true only if score >= {threshold}.
"""

_QA_FALLBACK_PROMPT = """\
Review this LinkedIn post. Reply with EXACTLY this format, nothing else:
SCORE: <integer 1-10>
FEEDBACK: <one concise sentence>
PASSES: <yes or no>

POST:
{post_content}

Pass threshold: {threshold}/10.
"""


def _parse_text_qa(text: str, threshold: int) -> QAResult:
    score_m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    feedback_m = re.search(r"FEEDBACK:\s*(.+)", text, re.IGNORECASE)
    passes_m = re.search(r"PASSES:\s*(yes|no)", text, re.IGNORECASE)

    score = max(1, min(10, int(score_m.group(1)))) if score_m else 5
    feedback = feedback_m.group(1).strip() if feedback_m else "Could not parse detailed feedback."
    passes = (passes_m.group(1).lower() == "yes") if passes_m else (score >= threshold)

    return QAResult(score=score, feedback=feedback, passes=passes)


def qa_reviewer(state: PostState, app_config: AppConfig, llm: ChatOpenAI) -> PostState:
    post_content = state.get("current_post", "")
    persona_summary = state.get("persona_summary", "")

    prompt = _QA_PROMPT.format(
        persona_summary=persona_summary,
        post_content=post_content,
        min_words=app_config.post.min_words,
        max_words=app_config.post.max_words,
        threshold=app_config.quality.threshold,
    )

    try:
        structured_llm = llm.with_structured_output(QAResult)
        result: QAResult = structured_llm.invoke(prompt)
    except Exception as exc:
        # LengthFinishReasonError: model hit max_tokens before completing JSON.
        # Fall back to a minimal text format the model can fit in fewer tokens.
        console.print(f"[yellow]QAReviewer[/yellow] structured output failed ({type(exc).__name__}), using text fallback")
        fallback_prompt = _QA_FALLBACK_PROMPT.format(
            post_content=post_content,
            threshold=app_config.quality.threshold,
        )
        raw = llm.invoke(fallback_prompt).content
        result = _parse_text_qa(raw, app_config.quality.threshold)

    score = result.score
    current_post = post_content
    best_score = state.get("best_score", 0)
    best_post = state.get("best_post", current_post)

    if score > best_score:
        best_score = score
        best_post = current_post

    console.print(
        f"[blue]QAReviewer[/blue] score: [bold]{score}/10[/bold] "
        f"(threshold: {app_config.quality.threshold}, "
        f"retry: {state.get('retry_count', 0)}/{app_config.quality.max_retries})"
    )
    if score < app_config.quality.threshold:
        console.print(f"[yellow]  Feedback:[/yellow] {result.feedback[:200]}")

    return {
        "qa_score": score,
        "qa_feedback": result.feedback,
        "best_score": best_score,
        "best_post": best_post,
    }
