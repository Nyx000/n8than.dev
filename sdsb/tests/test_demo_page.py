"""Static structural checks for demo_page.html — the seed/plant kind-selector contract.

String/parse-level only (no browser): pins the DOM contract of the toggle and
guards regressions like smart-quotes in attributes (which silently null a
querySelector and locked the search button). Behavioral correctness
(cache/lazy/sticky) is verified in the browser per the spec.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HTML = (Path(__file__).resolve().parents[1] / "demo_page.html").read_text(encoding="utf-8")
SCRIPT = re.search(r"<script>(.*)</script>", HTML, re.S).group(1)


def test_single_results_grid_and_kind_tabs():
    assert 'id="grid"' in HTML
    assert 'role="tablist"' in HTML
    assert 'data-kind="seed"' in HTML and 'data-kind="plant"' in HTML


def test_two_section_layout_removed():
    for dead in ("plantsSection", "seedsSection", "plantsGrid", "seedsGrid",
                 "plantsCount", "seedsCount", 'id="meta"'):
        assert dead not in HTML, f"dead two-section handle still present: {dead}"


def test_requests_twelve_of_the_selected_kind():
    assert re.search(r"k:\s*['\"]12['\"]\s*,\s*kind", SCRIPT), "fetch must send k=12 and a kind param"


def test_kind_persisted_in_url():
    assert "&kind=" in SCRIPT, "selected kind must be written to the URL"


def test_counts_default_to_dash_until_loaded():
    assert re.search(r'id="countSeed"[^>]*>\s*—', HTML)
    assert re.search(r'id="countPlant"[^>]*>\s*—', HTML)


def test_note_uses_straight_quotes_and_no_curly_attrs():
    assert '<p class="note" id="note">' in HTML
    assert not re.search(r'=[“”]', HTML), "curly quote used as an attribute delimiter"


def test_search_button_reenabled_in_finally():
    assert re.search(r"finally\s*\{[^}]*disabled\s*=\s*false", SCRIPT), \
        "the Search button must be re-enabled in a finally block"


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_inline_script_parses():
    proc = subprocess.run(
        ["node", "-e", "new Function(require('fs').readFileSync(0,'utf8'))"],
        input=SCRIPT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
