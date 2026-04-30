"""NVIDIA NIM LLM factory via LangChain ChatOpenAI with custom base_url."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from agent.config import AppConfig, Secrets


def make_llm(config: AppConfig, secrets: Secrets) -> ChatOpenAI:
    """
    Returns a ChatOpenAI instance pointed at NVIDIA NIM.

    NVIDIA NIM exposes an OpenAI-compatible REST API, so ChatOpenAI works
    without any custom provider — just override base_url and api_key.
    streaming=False is required for with_structured_output to parse JSON reliably.
    """
    return ChatOpenAI(
        model=config.model.name,
        base_url=config.model.base_url,
        api_key=secrets.nvidia_api_key or "local-no-key",
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens,
        streaming=False,
    )
