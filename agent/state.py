"""LangGraph shared state TypedDict — populated incrementally by pipeline nodes."""

from __future__ import annotations

from typing_extensions import TypedDict


class PostState(TypedDict, total=False):
    # Persona stage
    persona_raw: str
    persona_summary: str

    # Research stage
    existing_topics: list[str]
    chosen_query: str
    research_results: list[dict]
    research_summary: str

    # Writing stage
    current_post: str
    post_topic: str

    # QA / refine loop
    qa_score: int
    qa_feedback: str
    retry_count: int
    best_score: int
    best_post: str

    # Save stage
    saved_path: str
