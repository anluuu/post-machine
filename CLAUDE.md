# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Local development (API + UI together)
mise run dev

# Agent CLI
uv run post-agent run            # generate one post
uv run post-agent loop           # hourly loop (Ctrl+C to stop)
uv run post-agent loop -i 30     # custom interval (seconds)
uv run post-agent config-check   # validate config.yaml

# API server only
uv run uvicorn agent.api:app --reload --port 8000

# Tests + lint
uv run pytest
uv run pytest tests/test_nodes.py::test_post_writer_returns_post_and_topic
uv run ruff check agent/ tests/
uv run ruff format agent/ tests/

# Kubernetes
mise run build              # build Docker images
mise run deploy:langfuse    # install Langfuse via Helm
mise run deploy:app         # apply API + UI manifests
mise run deploy             # all three in sequence
mise run logs               # stream API pod logs
```

## Model / LLM backend

Currently uses **LM Studio** running locally. `config.yaml` points to `http://localhost:1234/v1`.
In Kubernetes, change `base_url` to `http://host.docker.internal:1234/v1` (Docker Desktop on macOS/Windows).
The `api_key` falls back to `"local-no-key"` when `NVIDIA_API_KEY` is unset — fine for LM Studio.

## Architecture

### Agent pipeline

LangGraph `StateGraph`. `PostState` (TypedDict, all keys optional) flows through nodes; each node returns a partial dict merged into shared state.

```
persona_loader → topic_researcher → post_writer → qa_reviewer
                                                      ↓ score >= threshold OR retries exhausted
                                                  post_refiner ←─────────────────────────────
                                                      ↓ (loops back to qa_reviewer)
                                                  post_saver → END
```

**Key files:**
- `config.yaml` — single source of truth (model, queries, tone, quality threshold, hooks)
- `agent/config.py` — Pydantic models for YAML; `Secrets` loads `NVIDIA_API_KEY` via pydantic-settings
- `agent/graph.py` — assembles the graph; binds `app_config` + `llm` into nodes via `functools.partial`
- `agent/state.py` — `PostState` TypedDict
- `agent/llm.py` — `ChatOpenAI` pointed at any OpenAI-compatible endpoint via `base_url`
- `agent/nodes/` — one file per pipeline stage
- `agent/hooks.py` — runs optional shell commands from `config.yaml`; post content piped via stdin
- `agent/api.py` — FastAPI backend; `GET /api/posts`, `GET /api/posts/{slug}`, `POST /api/run` (SSE stream)

**LangGraph gotcha:** LangGraph reserves `config` for `RunnableConfig`. All node functions use `app_config`. The `partial()` calls in `graph.py` bind `app_config=config`.

**QA loop:** `qa_reviewer` uses `with_structured_output(QAResult)`. If the model hits `max_tokens` before completing the JSON, it falls back to a minimal text-format prompt + regex parser. `best_post`/`best_score` track the highest-scoring draft; `post_saver` always saves `best_post`.

**Persona cache:** `.persona_cache.json` is keyed by SHA-256 of `persona.md` + model name. Avoids re-summarising on every run.

### Frontend (`ui/`)

Vite + React 19 + TypeScript. `react-markdown` renders posts. Proxies `/api/*` to the API server (`:8000` in dev via `vite.config.ts`, nginx in k8s).

```bash
cd ui && npm run dev    # dev server on :5173
cd ui && npm run build  # production build
cd ui && npm run check  # biome lint
```

### Observability (Langfuse)

Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST` to enable tracing. The agent attaches a `CallbackHandler` automatically at run time if `LANGFUSE_PUBLIC_KEY` is present. In k8s, the secret `langfuse-api` in namespace `posts-agent` holds these values.

Local Langfuse UI → `http://localhost:30100` after `mise run deploy:langfuse`.
Seeded credentials: `admin@local.dev` / `changeme`.

### Kubernetes (`k8s/`)

| File | Purpose |
|------|---------|
| `00-namespace.yaml` | `posts-agent` namespace |
| `01-volumes.yaml` | hostPath PV/PVC mounting the repo root at `/data` |
| `02-secrets.yaml` | Langfuse API keys (update after seeding) |
| `03-api.yaml` | API Deployment + ClusterIP Service |
| `04-ui.yaml` | UI Deployment + NodePort Service (`:30080`) |
| `langfuse-values.yaml` | Helm values for Langfuse (Helm chart: `langfuse/langfuse`) |

## Configuration knobs (config.yaml)

| Key | Purpose |
|-----|---------|
| `model.name` | Model ID passed to the LLM backend |
| `model.base_url` | LLM endpoint (LM Studio: `http://localhost:1234/v1`) |
| `model.max_tokens` | Max tokens per completion (default 4096) |
| `research.queries` | Topic candidates; LLM picks least-covered each run |
| `research.timelimit` | DuckDuckGo recency: `d` / `w` / `m` |
| `post.style` | Writing rules injected verbatim into the writer prompt |
| `quality.threshold` | Min score (1–10) to skip refinement |
| `quality.max_retries` | Max refine loops before saving best seen |
| `hooks.*` | Shell commands at `pre/post_research`, `pre/post_write_post`, `pre/post_save_post` |

## Tests

44 unit tests, no real LLM/network calls. Nodes tested with `MagicMock` LLM. QA tests cover structured output path and the `LengthFinishReasonError` text-fallback path. `post_saver` tests use `tmp_path`. Graph routing tested via `_route_qa` directly.
