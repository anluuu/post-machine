"""FastAPI backend — lists posts and streams agent runs via SSE."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

POSTS_DIR = Path(os.environ.get("POSTS_DIR", str(Path(__file__).parent.parent)))
IGNORED = {"persona.md", "CLAUDE.md", "ARCHITECTURE.md"}

app = FastAPI(title="Posts Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ANSI_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _post_meta(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else path.stem
    return {
        "slug": path.stem,
        "title": title,
        "date": path.stem[:10] if len(path.stem) >= 10 else "",
        "size": path.stat().st_size,
    }


@app.get("/api/posts")
def list_posts() -> list[dict]:
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        if f.name not in IGNORED:
            posts.append(_post_meta(f))
    return posts


@app.get("/api/posts/{slug}")
def get_post(slug: str) -> dict:
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists() or path.name in IGNORED:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"slug": slug, "content": path.read_text(encoding="utf-8")}


@app.post("/api/run")
async def run_agent() -> StreamingResponse:
    async def generate():
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "agent.main", "run",
            "--config", str(POSTS_DIR / "config.yaml"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(POSTS_DIR),
        )
        async for line in proc.stdout:
            text = _strip_ansi(line.decode().rstrip())
            if text:
                yield f"data: {json.dumps({'line': text})}\n\n"
        await proc.wait()
        yield f"data: {json.dumps({'done': True, 'code': proc.returncode})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
