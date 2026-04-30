"""
Shell-command hook runner.

Hooks are optional shell commands from config.yaml.
Post content is piped via stdin when provided.
Non-zero exit raises RuntimeError to stop the pipeline.
"""

from __future__ import annotations

import subprocess

from rich.console import Console

console = Console()


def run_hook(name: str, command: str | None, stdin_content: str | None = None) -> None:
    if not command:
        return

    console.print(f"[dim]  hook [{name}]: {command}[/dim]")

    result = subprocess.run(
        command,
        shell=True,  # intentional: hooks are operator-authored commands, not user input
        input=stdin_content.encode("utf-8") if stdin_content else None,
        capture_output=False,
        text=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Hook '{name}' exited {result.returncode}: {command}")
