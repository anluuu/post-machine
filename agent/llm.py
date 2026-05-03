"""LLM factory via LangChain ChatOpenAI with custom base_url."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from agent.config import AppConfig, Secrets


def make_llm(config: AppConfig, secrets: Secrets) -> ChatOpenAI:
    """
    Returns a ChatOpenAI instance against any OpenAI-compatible endpoint.

    The LM_STUDIO_URL env var overrides config.model.base_url so the same
    config.yaml works for both local dev (localhost:1234) and k8s
    (host.docker.internal:1234), where the pod can't reach the host on
    "localhost".
    streaming=False is required for with_structured_output to parse JSON reliably.
    """
    return ChatOpenAI(
        model=config.model.name,
        base_url=os.environ.get("LM_STUDIO_URL") or config.model.base_url,
        api_key=secrets.nvidia_api_key or "local-no-key",
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens,
        streaming=False,
    )
