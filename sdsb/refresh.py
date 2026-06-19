#!/usr/bin/env python3
"""
refresh.py — Keep the catalog current in one command.

Steps:
  1. Re-scrape the live catalog  -> sdseed_catalog.json / .md
  2. Smart-load into pgvector     -> only (re)embeds new/changed products,
                                     cheaply refreshes price/stock on the rest,
                                     and marks vanished products discontinued.

Designed to run on a schedule (weekly is plenty for a seed catalog). Safe to
re-run anytime; it is fully idempotent.

Run:  python refresh.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(label: str, argv: list[str]) -> None:
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run([sys.executable, *argv], cwd=HERE)
    if result.returncode != 0:
        print(f"!! step failed: {label} (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> int:
    run("Scrape catalog", ["sdseed_catalog.py"])
    run("Load into pgvector (smart + discontinued)",
        ["load_pgvector.py", "--mark-discontinued"])
    print("\nRefresh complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
