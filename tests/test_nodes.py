"""Tests for pipeline nodes — all LLM/network calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.config import AppConfig, PathsConfig, PostConfig
from agent.nodes.persona import persona_loader
from agent.nodes.qa import QAResult, qa_reviewer
from agent.nodes.refiner import post_refiner
from agent.nodes.researcher import _existing_topics
from agent.nodes.writer import _extract_topic, post_writer

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mock_llm(content: str) -> MagicMock:
    llm = MagicMock()
    response = MagicMock()
    response.content = content
    llm.invoke.return_value = response
    return llm


def _base_config(**overrides) -> AppConfig:
    return AppConfig(**overrides)


# ─── _extract_topic ───────────────────────────────────────────────────────────

def test_extract_topic_from_h1():
    post = "# AI Engineering in 2026\n\nSome content."
    assert _extract_topic(post) == "AI Engineering in 2026"


def test_extract_topic_fallback():
    assert _extract_topic("no heading here") == "Unknown Topic"


def test_extract_topic_ignores_h2():
    post = "## Subtitle\n\n# Real Title\n\nContent."
    assert _extract_topic(post) == "Real Title"


# ─── PersonaLoader ────────────────────────────────────────────────────────────

def test_persona_loader_reads_file_and_summarises(tmp_path):
    persona_file = tmp_path / "persona.md"
    persona_file.write_text("# Wagner\n\nExpert in Cloud and AI.\n")

    llm = _mock_llm("Cloud & AI expert. Direct writing style.")

    cfg = AppConfig(paths=PathsConfig(persona_file=str(persona_file)))
    result = persona_loader({}, cfg, llm)

    assert "persona_summary" in result
    assert result["persona_summary"] == "Cloud & AI expert. Direct writing style."
    assert "persona_raw" in result
    llm.invoke.assert_called_once()


def test_persona_loader_truncates_large_file(tmp_path):
    persona_file = tmp_path / "persona.md"
    persona_file.write_text("x" * 100_000)  # 100KB file

    llm = _mock_llm("summary")
    cfg = AppConfig(paths=PathsConfig(persona_file=str(persona_file)))
    persona_loader({}, cfg, llm)

    prompt_sent = llm.invoke.call_args[0][0]
    # The prompt should be much shorter than 100KB
    assert len(prompt_sent) < 20_000


# ─── PostWriter ───────────────────────────────────────────────────────────────

def test_post_writer_returns_post_and_topic():
    llm = _mock_llm("# Cloud Cost Optimisation\n\nContent.\n\n#Cloud #GCP")
    cfg = _base_config()
    state = {"persona_summary": "expert", "research_summary": "cloud news"}

    result = post_writer(state, cfg, llm)

    assert result["current_post"] == "# Cloud Cost Optimisation\n\nContent.\n\n#Cloud #GCP"
    assert result["post_topic"] == "Cloud Cost Optimisation"
    assert result["retry_count"] == 0
    assert result["best_score"] == 0
    assert result["best_post"] == result["current_post"]


def test_post_writer_includes_config_in_prompt():
    llm = _mock_llm("# Post\n\ncontent\n\n#tag")
    cfg = AppConfig(post=PostConfig(tone="very formal", min_words=200, max_words=400))
    state = {"persona_summary": "", "research_summary": ""}

    post_writer(state, cfg, llm)

    prompt = llm.invoke.call_args[0][0]
    assert "very formal" in prompt
    assert "200" in prompt
    assert "400" in prompt


# ─── QAReviewer ───────────────────────────────────────────────────────────────

def test_qa_reviewer_tracks_best_score():
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = QAResult(score=8, feedback="Good post.", passes=True)
    llm.with_structured_output.return_value = structured

    cfg = _base_config()
    state = {"current_post": "# Post\n\nContent\n\n#tag", "persona_summary": "", "best_score": 5, "best_post": "old", "retry_count": 0}

    result = qa_reviewer(state, cfg, llm)

    assert result["qa_score"] == 8
    assert result["best_score"] == 8
    assert result["best_post"] == "# Post\n\nContent\n\n#tag"


def test_qa_reviewer_keeps_existing_best_when_score_lower():
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = QAResult(score=4, feedback="Needs work.", passes=False)
    llm.with_structured_output.return_value = structured

    cfg = _base_config()
    state = {
        "current_post": "# New\n\nContent\n\n#tag",
        "persona_summary": "",
        "best_score": 9,
        "best_post": "# Best Ever\n\nContent\n\n#tag",
        "retry_count": 1,
    }

    result = qa_reviewer(state, cfg, llm)

    assert result["best_score"] == 9
    assert result["best_post"] == "# Best Ever\n\nContent\n\n#tag"


# ─── PostRefiner ──────────────────────────────────────────────────────────────

def test_post_refiner_increments_retry_count():
    llm = _mock_llm("# Improved Post\n\nBetter content.\n\n#AI")
    cfg = _base_config()
    state = {
        "current_post": "# Draft\n\nContent\n\n#tag",
        "qa_feedback": "Too short.",
        "persona_summary": "",
        "retry_count": 1,
    }

    result = post_refiner(state, cfg, llm)

    assert result["retry_count"] == 2
    assert result["current_post"] == "# Improved Post\n\nBetter content.\n\n#AI"


def test_post_refiner_includes_feedback_in_prompt():
    llm = _mock_llm("# Refined\n\ncontent\n\n#tag")
    cfg = _base_config()
    state = {
        "current_post": "draft",
        "qa_feedback": "Needs more data points.",
        "persona_summary": "",
        "retry_count": 0,
    }

    post_refiner(state, cfg, llm)

    prompt = llm.invoke.call_args[0][0]
    assert "Needs more data points." in prompt


# ─── _existing_topics ─────────────────────────────────────────────────────────

def test_existing_topics_extracts_h1_titles(tmp_path):
    (tmp_path / "2026-04-01-ai.md").write_text("# AI Trends\n\nContent.\n\n#AI #ML")
    (tmp_path / "2026-04-02-cloud.md").write_text("# Cloud Cost\n\nContent.\n\n#Cloud")
    (tmp_path / "persona.md").write_text("# Persona\n\nShould be ignored.")
    (tmp_path / "CLAUDE.md").write_text("# Config\n\nShould be ignored.")

    topics = _existing_topics(tmp_path)

    assert "AI Trends" in topics
    assert "Cloud Cost" in topics
    assert "Persona" not in topics
    assert "Config" not in topics


def test_existing_topics_includes_hashtags(tmp_path):
    (tmp_path / "post.md").write_text("# A Post\n\nContent.\n\n#LangGraph #NVIDIA")

    topics = _existing_topics(tmp_path)

    assert "LangGraph" in topics
    assert "NVIDIA" in topics


def test_existing_topics_empty_dir(tmp_path):
    assert _existing_topics(tmp_path) == []


# ─── QAReviewer fallback ──────────────────────────────────────────────────────

def test_qa_reviewer_falls_back_on_length_error():
    """When structured output raises, plain-text fallback is used."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.side_effect = Exception("LengthFinishReasonError")
    llm.with_structured_output.return_value = structured

    response = MagicMock()
    response.content = "SCORE: 7\nFEEDBACK: Good structure.\nPASSES: yes"
    llm.invoke.return_value = response

    cfg = _base_config()
    state = {"current_post": "# Post\n\nContent\n\n#tag", "persona_summary": "", "best_score": 0, "best_post": "", "retry_count": 0}

    result = qa_reviewer(state, cfg, llm)

    assert result["qa_score"] == 7
    assert result["qa_feedback"] == "Good structure."
    assert result["best_score"] == 7


def test_qa_reviewer_fallback_clamps_score():
    """Fallback parser clamps scores outside 1–10."""
    from agent.nodes.qa import _parse_text_qa

    r = _parse_text_qa("SCORE: 99\nFEEDBACK: ok\nPASSES: yes", threshold=7)
    assert r.score == 10

    r = _parse_text_qa("SCORE: 0\nFEEDBACK: bad\nPASSES: no", threshold=7)
    assert r.score == 1


def test_qa_reviewer_fallback_defaults_on_unparseable():
    """Fallback returns score=5 and passes based on threshold when response is garbage."""
    from agent.nodes.qa import _parse_text_qa

    r = _parse_text_qa("I don't know what to say", threshold=7)
    assert r.score == 5
    assert r.passes is False  # 5 < 7
