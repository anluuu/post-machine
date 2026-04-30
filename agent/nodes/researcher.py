"""
TopicResearcher node.

1. Scans the output directory to build a list of already-covered topics.
2. Uses the LLM to pick the research query least represented in existing posts.
3. Runs a DuckDuckGo search.
4. Summarises results into a research brief via the LLM.
"""

from __future__ import annotations

import re
from pathlib import Path

from ddgs import DDGS
from langchain_openai import ChatOpenAI
from rich.console import Console

from agent.config import AppConfig
from agent.hooks import run_hook
from agent.state import PostState

console = Console()

_QUERY_SELECTOR_PROMPT = """\
You are selecting the best LinkedIn post topic for a software engineer.

Available research queries (each is a potential topic):
{queries}

Topics already covered in existing posts (avoid semantic overlap):
{existing_topics}

Persona context:
{persona_summary}

Return ONLY the single best query from the list above that is:
1. Not already covered or semantically close to an existing topic
2. Most relevant and timely for a technical LinkedIn audience in 2026
3. Aligned with the persona's expertise

Return the exact query string. Nothing else.
"""

_RESEARCH_SUMMARY_PROMPT = """\
Summarise the following web search results into a focused research brief (max 250 words).
Highlight: key facts, recent data points, trends, and anything a technical engineer
writing a LinkedIn post would find useful and credible.

Search query: {query}

Results:
{results_text}

Return ONLY the brief. No preamble.
"""


def _existing_topics(output_dir: Path) -> list[str]:
    topics: list[str] = []
    for md_file in sorted(output_dir.glob("*.md")):
        if md_file.name in ("persona.md", "CLAUDE.md"):
            continue
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            topics.append(match.group(1).strip())
        topics.extend(re.findall(r"#(\w+)", text))
    return list(set(topics))


def topic_researcher(state: PostState, app_config: AppConfig, llm: ChatOpenAI) -> PostState:
    run_hook("pre_research", app_config.hooks.pre_research)

    output_dir = Path(app_config.paths.output_dir)
    existing = _existing_topics(output_dir)
    console.print(f"[blue]TopicResearcher[/blue] {len(existing)} existing topic signals found")

    queries_text = "\n".join(f"- {q}" for q in app_config.research.queries)
    existing_text = "\n".join(f"- {t}" for t in existing[:50])

    chosen_query = llm.invoke(
        _QUERY_SELECTOR_PROMPT.format(
            queries=queries_text,
            existing_topics=existing_text or "(none yet)",
            persona_summary=state.get("persona_summary", ""),
        )
    ).content.strip()

    # Fallback if LLM returns something not in the list
    if chosen_query not in app_config.research.queries:
        chosen_query = app_config.research.queries[0]

    console.print(f"[blue]TopicResearcher[/blue] query: [bold]{chosen_query}[/bold]")

    raw_results = DDGS().text(
        chosen_query,
        region=app_config.research.region,
        safesearch="moderate",
        timelimit=app_config.research.timelimit,
        max_results=app_config.research.max_results_per_query,
    )

    results_text = "\n\n".join(
        f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
        for r in (raw_results or [])
    )

    research_summary = llm.invoke(
        _RESEARCH_SUMMARY_PROMPT.format(
            query=chosen_query,
            results_text=results_text or "(no results found)",
        )
    ).content.strip()

    console.print(f"[green]TopicResearcher[/green] research brief ready ({len(research_summary)} chars)")

    run_hook("post_research", app_config.hooks.post_research)

    return {
        "existing_topics": existing,
        "chosen_query": chosen_query,
        "research_results": raw_results or [],
        "research_summary": research_summary,
    }
