"""Tests for agent/hooks.py — shell-command hook runner."""

from __future__ import annotations

import pytest

from agent.hooks import run_hook


def test_run_hook_skips_none():
    run_hook("test", None)  # must not raise


def test_run_hook_skips_empty_string():
    run_hook("test", "")  # empty string is falsy — must not raise


def test_run_hook_executes_command():
    run_hook("echo", "echo hello")  # should succeed silently


def test_run_hook_passes_stdin(tmp_path):
    out = tmp_path / "out.txt"
    run_hook("write-stdin", f"cat > {out}", stdin_content="hello from hook")
    assert out.read_text() == "hello from hook"


def test_run_hook_raises_on_nonzero_exit():
    with pytest.raises(RuntimeError, match="exited 1"):
        run_hook("fail", "exit 1")
