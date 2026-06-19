"""
sdseed_common.py — shared helpers for the pgvector loader and MCP server.

Provides:
  * load_env()        — read .env into os.environ (no external dep)
  * ssh_tunnel()      — context manager: SSH local-forward to the Hetzner Postgres
  * connect()         — psycopg connection using env settings
  * embed_documents() / embed_query() — Voyage AI embeddings
  * EMBED_MODEL / EMBED_DIM

The Hetzner Postgres listens only on localhost:5432. We never expose it; instead
we open an SSH local port-forward (localhost:PGPORT -> remote localhost:5432)
using the user's existing key-based 'hetzner' host in ~/.ssh/config.
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import time
from pathlib import Path

EMBED_MODEL = "voyage-3.5"
EMBED_DIM = 1024  # voyage-3.5 default output dimension
EMBED_INPUT_DOC = "document"
EMBED_INPUT_QUERY = "query"
RERANK_MODEL = "rerank-2.5"

_ENV_LOADED = False


def load_env(path: str | os.PathLike = ".env") -> None:
    """Minimal .env loader (KEY=VALUE lines). Does not overwrite existing env."""
    global _ENV_LOADED
    p = Path(path)
    if not p.exists():
        # also try alongside this file
        p = Path(__file__).resolve().parent / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            os.environ.setdefault(key, val)
    _ENV_LOADED = True


def _env(key: str, default: str | None = None) -> str:
    if not _ENV_LOADED:
        load_env()
    val = os.environ.get(key, default)
    if val is None:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def _no_tunnel() -> bool:
    """When running co-located with Postgres (e.g. on the Hetzner box), skip SSH."""
    return os.environ.get("SDSEED_NO_TUNNEL", "").lower() in ("1", "true", "yes")


@contextlib.contextmanager
def ssh_tunnel(local_port: int | None = None):
    """
    Open an SSH local-forward to the remote Postgres for the duration of the block.
    Yields the local port to connect to. If something is already listening on the
    target local port (e.g. a manually-opened tunnel), reuse it without spawning.

    If SDSEED_NO_TUNNEL is set, this is a no-op that just yields PGPORT — used when
    the process already runs on the same host as Postgres.
    """
    if not _ENV_LOADED:
        load_env()
    if _no_tunnel():
        yield int(_env("PGPORT", "5432"))
        return
    local_port = local_port or int(_env("PGPORT", "6543"))
    ssh_host = _env("SDSEED_SSH_HOST", "hetzner")
    remote_port = int(_env("SDSEED_REMOTE_PG_PORT", "5432"))

    if _port_open("127.0.0.1", local_port):
        # Tunnel (or local pg) already present — use it, don't manage lifecycle.
        yield local_port
        return

    cmd = [
        "ssh", "-N",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-L", f"{local_port}:localhost:{remote_port}",
        ssh_host,
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        # Wait for the forward to come up.
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if _port_open("127.0.0.1", local_port):
                break
            if proc.poll() is not None:
                err = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
                raise RuntimeError(f"SSH tunnel failed to start: {err.strip()}")
            time.sleep(0.3)
        else:
            raise RuntimeError(
                f"SSH tunnel to {ssh_host} did not open localhost:{local_port} in time"
            )
        yield local_port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def connect(local_port: int | None = None):
    """psycopg connection to the tunneled Postgres. Caller manages the tunnel."""
    import psycopg

    local_port = local_port or int(_env("PGPORT", "6543"))
    return psycopg.connect(
        host="127.0.0.1",
        port=local_port,
        dbname=_env("PGDATABASE", "sdseed"),
        user=_env("PGUSER", "sdseed"),
        password=_env("PGPASSWORD"),
        connect_timeout=10,
    )


_VOYAGE_CLIENT = None


def _voyage():
    global _VOYAGE_CLIENT
    if _VOYAGE_CLIENT is None:
        import voyageai

        _VOYAGE_CLIENT = voyageai.Client(api_key=_env("VOYAGE_API_KEY"))
    return _VOYAGE_CLIENT


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document texts. Caller should keep batches reasonable."""
    resp = _voyage().embed(texts, model=EMBED_MODEL, input_type=EMBED_INPUT_DOC)
    return resp.embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    resp = _voyage().embed([text], model=EMBED_MODEL, input_type=EMBED_INPUT_QUERY)
    return resp.embeddings[0]


def rerank(query: str, documents: list[str], top_k: int | None = None):
    """
    Rerank candidate documents against the query with Voyage rerank-2.5.
    Returns a list of (original_index, relevance_score) sorted best-first.
    """
    if not documents:
        return []
    resp = _voyage().rerank(
        query, documents, model=RERANK_MODEL, top_k=top_k, truncation=True
    )
    return [(r.index, r.relevance_score) for r in resp.results]
