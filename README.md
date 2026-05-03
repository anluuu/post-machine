# post-machine

A LangGraph agent that drafts LinkedIn-style posts in your voice. Researches a topic, writes a draft, scores it, refines until it passes a quality gate, then saves to a dated Markdown file.

Local-first: runs against any OpenAI-compatible endpoint (defaults to [LM Studio](https://lmstudio.ai/) on `localhost:1234`). Optional [Langfuse](https://langfuse.com/) tracing.

## Pipeline

```
persona_loader → topic_researcher → post_writer → qa_reviewer
                                                      ↓ score >= threshold OR retries exhausted
                                                  post_refiner ←─────────────────────────────
                                                      ↓ (loops back to qa_reviewer)
                                                  post_saver → END
```

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the diagram and per-node details.

## Setup

1. Create a `persona.md` at the repo root describing your voice, expertise, and style. The agent caches a summary of it in `.persona_cache.json`.
2. Start an OpenAI-compatible LLM server. Default config points at LM Studio:
   ```yaml
   model:
     base_url: "http://localhost:1234/v1"
     name: "google/gemma-4-e4b"
   ```
3. Install deps:
   ```bash
   uv sync
   cd ui && npm install
   ```

## Run

```bash
# CLI: generate one post
uv run post-agent run

# CLI: hourly loop
uv run post-agent loop
uv run post-agent loop -i 1800   # custom interval (seconds)

# Validate config.yaml
uv run post-agent config-check

# API + UI together (via mise)
mise run dev
# → API on :8000, UI on :5173
```

Generated posts land at `paths.output_dir` (default: repo root) as `YYYY-MM-DD-slug.md`. They're gitignored.

## Configuration

All knobs live in [`config.yaml`](./config.yaml):

| Section    | What you tune                                              |
|------------|------------------------------------------------------------|
| `model`    | Endpoint, model name, temperature, max tokens              |
| `research` | Candidate queries, recency window, results per query       |
| `post`     | Tone, style rules, word range, output format               |
| `quality`  | Score threshold (1–10) and max refinement retries          |
| `paths`    | Persona file, output directory                             |
| `loop`     | Loop interval in seconds                                   |
| `hooks`    | Optional shell commands at each pipeline stage             |

## Tests & lint

```bash
uv run pytest
uv run ruff check agent/ tests/
uv run ruff format agent/ tests/
```

44 unit tests, no real LLM or network calls.

## Deploy (Kubernetes)

```bash
mise run build              # build Docker images
mise run deploy:langfuse    # install Langfuse via Helm
mise run deploy:app         # apply API + UI manifests
mise run deploy             # all three in sequence
mise run logs               # stream API pod logs
```

Manifests in [`k8s/`](./k8s/). The API and UI mount the repo root via a hostPath PV at `/data` so generated posts persist outside the pod.

When deploying, change `model.base_url` in `config.yaml` to `http://host.docker.internal:1234/v1` so pods can reach LM Studio on the host (Docker Desktop on macOS/Windows).

## Observability

Set the following to enable Langfuse tracing — the agent attaches a `CallbackHandler` automatically when `LANGFUSE_PUBLIC_KEY` is present:

```bash
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=http://localhost:30100
```

Local Langfuse UI: `http://localhost:30100` after `mise run deploy:langfuse`.

## Layout

```
agent/        LangGraph nodes, FastAPI app, config, hooks
ui/           Vite + React 19 frontend
k8s/          Namespace, volumes, secrets, API + UI manifests
tests/        Unit tests (mocked LLM)
config.yaml   Single source of truth
persona.md    Your voice (gitignored)
```
