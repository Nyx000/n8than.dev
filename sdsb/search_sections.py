"""search_sections.py — pure result-partitioning for the two-section search.

Dependency-free (no FastAPI/DB imports) so it is unit-testable under the lean
local venv, which does not install the service runtime deps. Imported by
search_service.py.
"""

from __future__ import annotations


def partition_sections(rows: list[dict], k: int) -> dict:
    """Split reranked rows into {'plant': [...], 'seed': [...]}, each capped at k, order preserved."""
    out: dict = {"plant": [], "seed": []}
    for r in rows:
        bucket = out.get(r.get("kind"))
        if bucket is not None and len(bucket) < k:
            bucket.append(r)
    return out
