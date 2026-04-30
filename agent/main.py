"""
CLI entrypoint for the LinkedIn Post Agent.

Commands:
  run          — generate one post now
  loop         — generate posts on a configurable interval
  config-check — validate config.yaml and print a summary
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.config import load_config, load_secrets

app = typer.Typer(
    name="post-agent",
    help="LinkedIn post agent — LangGraph + NVIDIA NIM (GLM-4.7) + DuckDuckGo",
    rich_markup_mode="rich",
)
console = Console()


def _langfuse_handler():
    import os
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return None
    try:
        from langfuse.langchain import CallbackHandler
        return CallbackHandler()
    except Exception:
        return None


def _run_once(config_path: str) -> None:
    from agent.graph import build_graph

    config = load_config(config_path)
    secrets = load_secrets()
    graph = build_graph(config, secrets)

    handler = _langfuse_handler()
    if handler:
        graph = graph.with_config({"callbacks": [handler]})
        console.print("[dim]Langfuse tracing enabled[/dim]")

    console.print(Panel("[bold blue]LinkedIn Post Agent — starting run[/bold blue]"))
    result = graph.invoke({})

    saved = result.get("saved_path", "(not saved)")
    score = result.get("best_score") or result.get("qa_score", "?")
    topic = result.get("post_topic", "unknown")

    console.print(
        Panel(
            f"[green]Done![/green]\n"
            f"Topic:  {topic}\n"
            f"Score:  {score}/10\n"
            f"File:   {saved}",
            title="Post Generated",
        )
    )


@app.command()
def run(
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config.yaml"),
    ] = "config.yaml",
) -> None:
    """Generate [bold green]one[/bold green] LinkedIn post and save it."""
    _run_once(config)


@app.command()
def loop(
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config.yaml"),
    ] = "config.yaml",
    interval: Annotated[
        int | None,
        typer.Option("--interval", "-i", help="Override loop interval in seconds"),
    ] = None,
) -> None:
    """
    Generate posts on a [bold yellow]recurring interval[/bold yellow].

    Runs until interrupted with Ctrl+C. Errors in a run are logged but do not
    stop the loop — the next iteration starts at the normal interval.
    """
    cfg = load_config(config)
    wait = interval if interval is not None else cfg.loop.interval_seconds

    console.print(
        Panel(
            f"[bold]Loop mode[/bold] — interval: {wait}s\n"
            "Press [red]Ctrl+C[/red] to stop.",
            title="Post Agent Loop",
        )
    )

    iteration = 0
    while True:
        iteration += 1
        console.print(f"\n[bold cyan]─── Iteration {iteration} ───[/bold cyan]")
        try:
            _run_once(config)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            console.print(f"[red]Error in iteration {iteration}:[/red] {exc}")
            console.print("[yellow]Continuing — next run in {wait}s...[/yellow]")

        console.print(f"[dim]Next run in {wait}s...[/dim]")
        try:
            time.sleep(wait)
        except KeyboardInterrupt:
            console.print("\n[yellow]Loop stopped.[/yellow]")
            raise typer.Exit() from None


@app.command(name="config-check")
def config_check(
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config.yaml"),
    ] = "config.yaml",
) -> None:
    """Validate [bold]config.yaml[/bold] and print a summary."""
    try:
        cfg = load_config(config)
        secrets = load_secrets()
    except Exception as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(1) from exc

    table = Table(title="Config Summary", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Model",           cfg.model.name)
    table.add_row("Base URL",        cfg.model.base_url)
    table.add_row("Temperature",     str(cfg.model.temperature))
    table.add_row("QA Threshold",    str(cfg.quality.threshold))
    table.add_row("Max Retries",     str(cfg.quality.max_retries))
    table.add_row("Post Length",     f"{cfg.post.min_words}–{cfg.post.max_words} words")
    table.add_row("Loop Interval",   f"{cfg.loop.interval_seconds}s")
    table.add_row("Output Dir",      cfg.paths.output_dir)
    table.add_row("Persona File",    cfg.paths.persona_file)
    table.add_row("Research Queries", str(len(cfg.research.queries)))
    table.add_row(
        "API Key",
        "[green]set[/green]" if secrets.nvidia_api_key else "[red]NOT SET[/red]",
    )

    console.print(table)

    persona_path = Path(cfg.paths.persona_file)
    if persona_path.exists():
        console.print(f"[green]✓[/green] persona.md found ({persona_path.stat().st_size // 1024}KB)")
    else:
        console.print(f"[red]✗[/red] persona.md not found at {persona_path.resolve()}")

    console.print("\n[green]Config valid.[/green]")


if __name__ == "__main__":
    app()
