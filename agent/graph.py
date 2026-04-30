"""
LangGraph StateGraph assembly.

Pipeline:
  START
    → persona_loader
    → topic_researcher
    → post_writer
    → qa_reviewer
    ↙ score >= threshold OR retries exhausted → post_saver → END
    ↘ score < threshold AND retries remaining  → post_refiner → qa_reviewer (loop)
"""

from __future__ import annotations

from functools import partial
from typing import Literal

from langgraph.graph import END, START, StateGraph

from agent.config import AppConfig, Secrets, load_config, load_secrets
from agent.llm import make_llm
from agent.nodes.persona import persona_loader
from agent.nodes.qa import qa_reviewer
from agent.nodes.refiner import post_refiner
from agent.nodes.researcher import topic_researcher
from agent.nodes.saver import post_saver
from agent.nodes.writer import post_writer
from agent.state import PostState


def _route_qa(state: PostState, app_config: AppConfig) -> Literal["post_refiner", "post_saver"]:
    score = state.get("qa_score", 0)
    retries = state.get("retry_count", 0)
    if score >= app_config.quality.threshold or retries >= app_config.quality.max_retries:
        return "post_saver"
    return "post_refiner"


def build_graph(config: AppConfig | None = None, secrets: Secrets | None = None):
    if config is None:
        config = load_config()
    if secrets is None:
        secrets = load_secrets()

    llm = make_llm(config, secrets)

    builder = StateGraph(PostState)

    builder.add_node("persona_loader",   partial(persona_loader,   app_config=config, llm=llm))
    builder.add_node("topic_researcher", partial(topic_researcher, app_config=config, llm=llm))
    builder.add_node("post_writer",      partial(post_writer,      app_config=config, llm=llm))
    builder.add_node("qa_reviewer",      partial(qa_reviewer,      app_config=config, llm=llm))
    builder.add_node("post_refiner",     partial(post_refiner,     app_config=config, llm=llm))
    builder.add_node("post_saver",       partial(post_saver,       app_config=config))

    builder.add_edge(START,              "persona_loader")
    builder.add_edge("persona_loader",   "topic_researcher")
    builder.add_edge("topic_researcher", "post_writer")
    builder.add_edge("post_writer",      "qa_reviewer")
    builder.add_edge("post_refiner",     "qa_reviewer")
    builder.add_edge("post_saver",       END)

    builder.add_conditional_edges(
        "qa_reviewer",
        partial(_route_qa, app_config=config),
        {"post_refiner": "post_refiner", "post_saver": "post_saver"},
    )

    return builder.compile()
