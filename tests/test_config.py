"""Tests for agent/config.py — config loading and validation."""

from __future__ import annotations

import pytest
import yaml

from agent.config import AppConfig, ModelConfig, QualityConfig, ResearchConfig, load_config


def test_load_config_from_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        yaml.dump(
            {
                "model": {"name": "z-ai/glm4.7", "temperature": 0.5},
                "quality": {"threshold": 8, "max_retries": 2},
                "research": {"queries": ["AI trends 2026"], "max_results_per_query": 3},
            }
        )
    )
    cfg = load_config(str(cfg_file))
    assert cfg.model.name == "z-ai/glm4.7"
    assert cfg.model.temperature == 0.5
    assert cfg.quality.threshold == 8
    assert cfg.quality.max_retries == 2
    assert cfg.research.queries == ["AI trends 2026"]


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="config.yaml not found"):
        load_config(str(tmp_path / "missing.yaml"))


def test_load_config_empty_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("")
    cfg = load_config(str(cfg_file))
    # Should fall back to all defaults
    assert isinstance(cfg, AppConfig)
    assert cfg.model.name == "z-ai/glm4.7"
    assert cfg.quality.threshold == 7


def test_model_config_defaults():
    m = ModelConfig()
    assert m.base_url == "https://integrate.api.nvidia.com/v1"
    assert m.max_tokens == 4096
    assert 0 < m.temperature < 1


def test_quality_config_defaults():
    q = QualityConfig()
    assert q.threshold == 7
    assert q.max_retries == 3


def test_research_config_defaults():
    r = ResearchConfig()
    assert isinstance(r.queries, list)
    assert r.max_results_per_query == 5


def test_full_config_yaml_loads():
    """Smoke-test that the real config.yaml in the project root is valid."""
    cfg = load_config("config.yaml")
    assert len(cfg.research.queries) > 0
    assert cfg.model.name
    assert cfg.quality.threshold > 0
