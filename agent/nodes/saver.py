"""
PostSaver node.

Saves the best-scoring post to a dated .md file in the output directory.
Filename: YYYY-MM-DD-slug.md  (appends -N if the name already exists)
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from rich.console import Console

from agent.config import AppConfig
from agent.hooks import run_hook
from agent.state import PostState

console = Console()


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:60]


def post_saver(state: PostState, app_config: AppConfig) -> PostState:
    run_hook("pre_save_post", app_config.hooks.pre_save_post)

    # Always save the best version seen across retries
    content = state.get("best_post") or state.get("current_post", "")
    topic = state.get("post_topic", "post")

    today = date.today().isoformat()
    filename = f"{today}-{_slugify(topic)}.{app_config.post.output_format}"

    output_dir = Path(app_config.paths.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    save_path = output_dir / filename
    counter = 1
    while save_path.exists():
        save_path = output_dir / f"{today}-{_slugify(topic)}-{counter}.{app_config.post.output_format}"
        counter += 1

    save_path.write_text(content, encoding="utf-8")
    console.print(f"[green]PostSaver[/green] saved: [bold]{save_path.name}[/bold]")

    run_hook("post_save_post", app_config.hooks.post_save_post, stdin_content=content)

    return {"saved_path": str(save_path.resolve())}
