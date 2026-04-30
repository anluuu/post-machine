"""Tests for agent/nodes/saver.py — file saving and slug generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from agent.config import AppConfig, PathsConfig, PostConfig
from agent.nodes.saver import _slugify, post_saver


def test_slugify_basic():
    assert _slugify("RAG Best Practices 2026") == "rag-best-practices-2026"


def test_slugify_special_chars():
    assert _slugify("AI/ML: The Future!") == "aiml-the-future"


def test_slugify_extra_hyphens():
    assert _slugify("  --hello   world--  ") == "hello-world"


def test_slugify_truncates_long_titles():
    long = "a" * 100
    assert len(_slugify(long)) <= 60


def _make_config(output_dir: str) -> AppConfig:
    return AppConfig(
        paths=PathsConfig(output_dir=output_dir),
        post=PostConfig(output_format="md"),
    )


def test_post_saver_creates_file(tmp_path):
    cfg = _make_config(str(tmp_path))
    state = {
        "best_post": "# Test Post\n\nContent here.\n\n#AI",
        "current_post": "# Test Post\n\nContent here.\n\n#AI",
        "post_topic": "Test Post",
    }
    result = post_saver(state, cfg)
    saved = Path(result["saved_path"])
    assert saved.exists()
    assert saved.read_text() == "# Test Post\n\nContent here.\n\n#AI"


def test_post_saver_uses_today_prefix(tmp_path):
    cfg = _make_config(str(tmp_path))
    state = {
        "best_post": "# My Post\n\n#tag",
        "post_topic": "My Post",
    }
    result = post_saver(state, cfg)
    filename = Path(result["saved_path"]).name
    assert filename.startswith(date.today().isoformat())


def test_post_saver_avoids_overwrite(tmp_path):
    cfg = _make_config(str(tmp_path))
    state = {"best_post": "content", "post_topic": "Dupe Topic"}
    r1 = post_saver(state, cfg)
    r2 = post_saver(state, cfg)
    assert r1["saved_path"] != r2["saved_path"]
    assert Path(r1["saved_path"]).exists()
    assert Path(r2["saved_path"]).exists()


def test_post_saver_falls_back_to_current_post(tmp_path):
    cfg = _make_config(str(tmp_path))
    state = {
        "current_post": "# Fallback\n\n#tag",
        "post_topic": "Fallback",
        # best_post deliberately absent
    }
    result = post_saver(state, cfg)
    assert Path(result["saved_path"]).read_text() == "# Fallback\n\n#tag"
