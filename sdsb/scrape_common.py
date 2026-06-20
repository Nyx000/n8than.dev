"""scrape_common.py — shared HTTP + HTML helpers for the catalog scrapers.

Lifted out of sdseed_catalog.py so the WooCommerce and Shopify adapters share
one polite HTTP session, retry/backoff, an HTML→text cleaner, and the
minor-units price helper. No behavior change from the original definitions.
"""

from __future__ import annotations

import html
import html.parser
import re
import sys
import time

import requests

PER_PAGE = 100
SLEEP_BETWEEN = 0.5          # politeness: seconds between page requests
MAX_RETRIES = 5
RETRYABLE = {429, 500, 502, 503, 504}
TIMEOUT = 30
USER_AGENT = (
    "sdseed-catalog-scraper/1.0 "
    "(+https://n8than.dev; public store APIs; contact husenathan@gmail.com)"
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})


def fetch(url: str, params: dict | None = None, *, expect_json: bool = True):
    """GET with exponential backoff on transient errors. Returns the Response."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = SESSION.get(url, params=params, timeout=TIMEOUT)
        except requests.RequestException as exc:
            last_exc = exc
            wait = min(2 ** attempt, 30)
            print(f"  ! request error ({exc}); retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue

        if resp.status_code in RETRYABLE:
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    wait = min(2 ** attempt, 30)
            else:
                wait = min(2 ** attempt, 30)
            print(
                f"  ! HTTP {resp.status_code} on {resp.url}; retry in {wait:.0f}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue

        return resp

    raise RuntimeError(f"Gave up on {url} after {MAX_RETRIES} retries ({last_exc})")


class _HTMLToText(html.parser.HTMLParser):
    """Strip tags, keep paragraph/list/heading structure as light markdown."""

    BLOCK = {"p", "div", "section", "article", "br", "tr"}
    HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0  # depth inside script/style

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in self.HEADINGS:
            self.parts.append("\n\n**")
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag in self.HEADINGS:
            self.parts.append("**\n")
        elif tag in ("p", "div", "li", "ul", "ol", "tr"):
            self.parts.append("\n")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")

    def handle_data(self, data):
        if self._skip:
            return
        self.parts.append(data)


def html_to_text(raw: str | None) -> str:
    """Convert an HTML fragment to clean plain text / light markdown."""
    if not raw:
        return ""
    parser = _HTMLToText()
    parser.feed(raw)
    text = "".join(parser.parts)
    text = html.unescape(text)
    # Collapse empty emphasis runs left by adjacent/split <b>/<i> tags in source.
    text = re.sub(r"\*{4,}", "", text)
    text = re.sub(r"\*\*(\s*)\*\*", r"\1", text)
    # Normalize whitespace: trim trailing spaces, collapse runs of blank lines.
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    out: list[str] = []
    blank = False
    for ln in lines:
        if ln:
            out.append(ln)
            blank = False
        elif not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def to_dollars(minor: str | None, exponent: int) -> float | None:
    """WooCommerce prices arrive as minor units (e.g. cents) + an exponent."""
    if minor is None or minor == "":
        return None
    try:
        return int(minor) / (10 ** exponent)
    except (ValueError, TypeError):
        return None


# Multi-word phrases are matched as substrings; single words are matched on
# WORD BOUNDARIES so real plant names that merely contain a term survive
# (e.g. "Mugwort", "Hatiora", "Bookleaf"). "hat" is intentionally omitted —
# even as a whole word it collides with real names like "Hat Cactus".
# "greeting card"/"note card" catch seed-paper stationery; "top dressing"
# catches pumice/pebble soil supplies — both ride in on plant-nursery feeds.
NON_PLANT_PHRASES = ("gift card", "e-gift", "greeting card", "note card", "top dressing")
NON_PLANT_WORDS = frozenset({
    "shipping", "deposit", "sticker", "mug", "tote", "book", "books", "merch", "pottery",
})

# Seed inventory carried by a plant-kind source is detected two ways:
#  1. an EXACT product_type match (Shopify stores tag seeds cleanly, e.g. "Seed"
#     or "Seeds & Seed Kits"). Compared whole — never substring — so an SEO-stuffed
#     breadcrumb product_type like "...> creeping thyme seeds >..." on a live plant
#     does not match.
#  2. the whole word "seed"/"seeds" in the NAME (backstop for loose seed a nursery
#     mis-typed, e.g. "Foothill Clover Annual 1tsp. Seed"). Word-boundary matching
#     is the point: "seedless" (grape), "seedling" (young tree), "hopseed"/"dotseed"
#     (plant names) tokenize to a single word that is NOT "seed"/"seeds", so those
#     stay correctly classified as live plants.
SEED_WORDS = frozenset({"seed", "seeds"})
SEED_TYPES = frozenset({
    "seed", "seeds", "seed kit", "seed kits", "seeds & seed kits",
    "seed pack", "seed packs", "seed packet", "seed packets",
})


def is_listable_plant(rec: dict) -> bool:
    """True if a record is a priced, real live plant (not merch/services/$0).

    Applied ONLY to plant-kind sources, whose catalogs mix in gift cards,
    shipping placeholders, and $0 browse-only/wholesale rows. Single-word merch
    terms match on word boundaries so plant names containing them aren't dropped.
    """
    if (rec.get("price") or 0) <= 0:
        return False
    haystack = f"{rec.get('name') or ''} {rec.get('type') or ''}".lower()
    if any(phrase in haystack for phrase in NON_PLANT_PHRASES):
        return False
    words = set(re.findall(r"[a-z]+", haystack))
    return words.isdisjoint(NON_PLANT_WORDS)


def looks_like_seed(rec: dict) -> bool:
    """True if a record is seed inventory rather than a live plant.

    An exact seed product_type (e.g. "Seeds & Seed Kits", "Seed"), or the whole
    word "seed"/"seeds" in the name (e.g. "Serrano Hot Pepper Seed Pack", "Chia -
    Seed"). Run AFTER is_listable_plant so merch that merely mentions seeds (e.g.
    "Seed Paper Greeting Card") is already dropped.
    """
    if (rec.get("type") or "").strip().lower() in SEED_TYPES:
        return True
    name_words = set(re.findall(r"[a-z]+", (rec.get("name") or "").lower()))
    return not name_words.isdisjoint(SEED_WORDS)


def resolve_kind(rec: dict, source_kind: str) -> str:
    """Per-product kind. Defaults to the source's kind, but reclassifies a
    plant-source product to "seed" when it is actually seed inventory — so a
    nursery's seed packs land in the Seeds section instead of polluting Plants.
    Seed-kind sources are returned unchanged (their rows are all seeds already).
    """
    if source_kind == "plant" and looks_like_seed(rec):
        return "seed"
    return source_kind
