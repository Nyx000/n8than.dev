#!/usr/bin/env python3
"""
refresh.py — Keep the multi-source catalog current in one command.

For each source in sources.SOURCES:
  1. Scrape it (WooCommerce or Shopify adapter) into catalog_<slug>.json
     ({source, fetched_utc, records:[...]}).
  2. Smart-load that file into pgvector — re-embed only changed/new records,
     cheaply refresh price/stock on the rest, and mark vanished products
     discontinued — all scoped to that one source.

One source failing is logged and skipped; the others still refresh.
Use --only <slug> to refresh a single source. Safe to re-run; idempotent.

Run:  python refresh.py [--only <slug>]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import sources
from sdseed_catalog import scrape_woocommerce
from shopify_catalog import scrape_shopify

HERE = Path(__file__).resolve().parent


def scrape_source(source: dict) -> list[dict]:
    """Dispatch a source to the right adapter; return normalized records."""
    if source["type"] == "woocommerce":
        return scrape_woocommerce(source)
    if source["type"] == "shopify":
        return scrape_shopify(source)
    raise ValueError(f"unknown source type: {source['type']!r} for {source['slug']}")


def build_catalog_doc(source_slug: str, records: list[dict], fetched_utc: str) -> dict:
    """The per-source catalog file contents the loader consumes."""
    return {"source": source_slug, "fetched_utc": fetched_utc, "records": records}


def load_file(path: Path) -> None:
    """Run the loader over one source file (smart change-detection + discontinued)."""
    result = subprocess.run(
        [sys.executable, "load_pgvector.py", "--json", str(path), "--mark-discontinued"],
        cwd=HERE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"loader failed for {path.name} (exit {result.returncode})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="refresh only this source slug")
    args = ap.parse_args()

    fetched_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    selected = [s for s in sources.SOURCES if not args.only or s["slug"] == args.only]
    if not selected:
        print(f"!! no source matches --only {args.only!r}", file=sys.stderr)
        return 1

    failures = []
    for source in selected:
        slug = source["slug"]
        print(f"\n=== {source['name']} ({slug}, {source['type']}) ===", flush=True)
        try:
            records = scrape_source(source)
            print(f"  scraped {len(records)} records")
            path = HERE / f"catalog_{slug}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(build_catalog_doc(slug, records, fetched_utc), f,
                          ensure_ascii=False, indent=2)
            load_file(path)
        except Exception as exc:  # one source failing must not abort the rest
            print(f"!! source '{slug}' failed: {exc}", file=sys.stderr)
            failures.append(slug)

    if failures:
        print(f"\nRefresh finished with {len(failures)} failed source(s): "
              f"{', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nRefresh complete (all sources).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
