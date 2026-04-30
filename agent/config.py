"""Pydantic config loader — reads config.yaml; secrets from .env."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ─── Sub-models ───────────────────────────────────────────────────────────────

class ModelConfig(BaseModel):
    name: str = "z-ai/glm4.7"
    base_url: str = "https://integrate.api.nvidia.com/v1"
    temperature: float = 0.75
    max_tokens: int = 4096


class ResearchConfig(BaseModel):
    queries: list[str] = Field(default_factory=list)
    max_results_per_query: int = 5
    region: str = "wt-wt"
    timelimit: str | None = "w"


class PostConfig(BaseModel):
    min_words: int = 150
    max_words: int = 350
    tone: str = "direct, honest, technical, calm"
    style: str = ""
    output_format: str = "md"


class QualityConfig(BaseModel):
    threshold: int = 7
    max_retries: int = 3


class PathsConfig(BaseModel):
    persona_file: str = "persona.md"
    output_dir: str = "."


class LoopConfig(BaseModel):
    interval_seconds: int = 3600


class HooksConfig(BaseModel):
    pre_research: str | None = None
    post_research: str | None = None
    pre_write_post: str | None = None
    post_write_post: str | None = None
    pre_save_post: str | None = None
    post_save_post: str | None = None


class AppConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    post: PostConfig = Field(default_factory=PostConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    loop: LoopConfig = Field(default_factory=LoopConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)


# ─── Secrets (from .env or env vars) ─────────────────────────────────────────

class Secrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    nvidia_api_key: str = ""


# ─── Loaders ─────────────────────────────────────────────────────────────────

def load_config(config_path: str = "config.yaml") -> AppConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"config.yaml not found at {path.resolve()}")
    with open(path) as f:
        raw = yaml.safe_load(f)
    return AppConfig.model_validate(raw or {})


def load_secrets() -> Secrets:
    return Secrets()
