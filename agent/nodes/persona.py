"""
PersonaLoader node.

Reads persona.md and uses the LLM to distill it into a concise summary:
expertise areas, writing style, tone, and topic preferences.
This summary is carried in state and injected into every subsequent prompt.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from pathlib import Path

from langchain_openai import ChatOpenAI
from rich.console import Console

from agent.config import AppConfig
from agent.state import PostState

console = Console()

_SUMMARY_PROMPT = """\
You are analyzing a software engineer's portfolio and writing guidelines document.

Extract a concise summary (max 300 words) covering:
1. Core technical expertise areas (top 5–7 domains)
2. Writing style rules (tone, sentence length, vocabulary to avoid)
3. Topics the engineer is known for and comfortable writing about
4. First-person voice characteristics

Return ONLY the summary. No preamble, no metadata.

---
{persona_text}
"""

CACHE_FILE = Path(".persona_cache.json")


def _get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def persona_loader(state: PostState, app_config: AppConfig, llm: ChatOpenAI) -> PostState:
    persona_path = Path(app_config.paths.persona_file)
    if not persona_path.exists():
        # Try relative to the project root (two levels up from this file)
        persona_path = Path(__file__).parent.parent.parent / app_config.paths.persona_file

    console.print(f"[blue]PersonaLoader[/blue] reading {persona_path.name}")
    persona_raw = persona_path.read_text(encoding="utf-8")
    current_hash = _get_hash(persona_raw)

    # Check cache
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if cache.get("hash") == current_hash and cache.get("model") == llm.model_name:
                console.print("[green]PersonaLoader[/green] using cached persona summary")
                return {
                    "persona_raw": persona_raw,
                    "persona_summary": cache.get("summary"),
                }
        except Exception:
            pass

    # persona.md is ~72KB. We combine a head slice (projects/expertise)
    # with a tail slice (writing guidelines) to stay within context limits.
    head = persona_raw[:3000]
    tail = persona_raw[-4000:]
    excerpt = head + "\n\n[...middle truncated...]\n\n" + tail

    response = llm.invoke(_SUMMARY_PROMPT.format(persona_text=excerpt))
    summary = response.content.strip()

    # Save cache
    with contextlib.suppress(Exception):
        CACHE_FILE.write_text(
            json.dumps({
                "hash": current_hash,
                "summary": summary,
                "model": llm.model_name
            }, indent=2),
            encoding="utf-8"
        )

    console.print(f"[green]PersonaLoader[/green] persona summary ready ({len(summary)} chars)")

    return {
        "persona_raw": persona_raw,
        "persona_summary": summary,
    }

