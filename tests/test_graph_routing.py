"""Tests for agent/graph.py — conditional routing logic."""

from __future__ import annotations

from agent.config import AppConfig, QualityConfig
from agent.graph import _route_qa


def _cfg(threshold: int = 7, max_retries: int = 3) -> AppConfig:
    return AppConfig(quality=QualityConfig(threshold=threshold, max_retries=max_retries))


def test_routes_to_saver_when_score_meets_threshold():
    assert _route_qa({"qa_score": 7, "retry_count": 0}, _cfg()) == "post_saver"


def test_routes_to_saver_when_score_exceeds_threshold():
    assert _route_qa({"qa_score": 10, "retry_count": 0}, _cfg()) == "post_saver"


def test_routes_to_refiner_when_below_threshold():
    assert _route_qa({"qa_score": 5, "retry_count": 0}, _cfg()) == "post_refiner"


def test_routes_to_saver_when_retries_exhausted():
    assert _route_qa({"qa_score": 3, "retry_count": 3}, _cfg()) == "post_saver"


def test_routes_to_refiner_on_last_retry_not_yet_exhausted():
    assert _route_qa({"qa_score": 4, "retry_count": 2}, _cfg(max_retries=3)) == "post_refiner"


def test_routes_to_saver_just_at_retry_limit():
    assert _route_qa({"qa_score": 1, "retry_count": 3}, _cfg(max_retries=3)) == "post_saver"


def test_default_state_values():
    # State keys absent — defaults to 0 score and 0 retries
    assert _route_qa({}, _cfg()) == "post_refiner"
