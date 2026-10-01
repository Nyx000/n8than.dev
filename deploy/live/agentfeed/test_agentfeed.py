"""Tests for agentfeed.py. Run: python -m pytest test_agentfeed.py

Every fixture transcript is synthetic. The planted "secrets" below are invented strings that stand in
for the kinds of private material real transcripts hold; the core assertion is that none of them, in
any casing, ever reaches the served JSON or the log.
"""
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

import agentfeed
from agentfeed import FeedServer, Handler, Tracker, command_kind, encode

HERE = Path(__file__).resolve().parent

# ---- planted secrets (all invented)
NAME = "Mortimer Quillfeather"
USER = "mquill"
EMAIL = "mortimer.quillfeather@example.test"
API_KEY = "sk-test-PLANTED9f8e7d6c5b4a"
CLIENT = "AcmeDentalGroup"
PROMPT = "please rotate the vault passphrase tangerine-otter-42"
URL = "https://intranet.example.test/payroll?token=zzPLANTEDzz"
QUERY = "quillfeather unpaid invoice dispute"
SECRETS = [NAME, "Mortimer", "Quillfeather", USER, EMAIL, "example.test", API_KEY, "PLANTED", CLIENT,
           "tangerine", "payroll", "invoice", "intranet", "passphrase"]

HOME = rf"C:\Users\{USER}"
PUB = rf"{HOME}\Documents\Projects\pubproj"          # the one allowlisted project
CLIENT_DIR = rf"{HOME}\Documents\Projects\work\{CLIENT}"
CFG = {"projects": [{"path": PUB, "exclude": ["career", "notes/drafts"]}], "deny": [USER]}


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Transcript:
    """Writes entries shaped like Claude Code's, including the prompt-derived fields the feed must ignore."""

    def __init__(self, root: Path, slug: str, sid: str, cwd: str, sub: str | None = None):
        folder = root / slug
        self.path = folder / f"{sid}.jsonl" if sub is None else folder / sid / "subagents" / f"agent-{sub}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()
        self.sid, self.cwd, self.sub, self.n = sid, cwd, sub, 0

    def raw(self, data: bytes):
        with open(self.path, "ab") as f:
            f.write(data)

    def _base(self, kind: str, t: float) -> dict:
        self.n += 1
        e = {"parentUuid": None, "isSidechain": self.sub is not None, "type": kind, "uuid": f"u{self.n}",
             "timestamp": iso(t), "cwd": self.cwd, "sessionId": self.sid, "version": "9.9.9",
             "gitBranch": f"feature/{CLIENT}-billing", "slug": f"rotate-{NAME.split()[1].lower()}-passphrase",
             "userType": "external", "entrypoint": "cli"}
        if self.sub:
            e["agentId"] = self.sub
        return e

    def write(self, e: dict):
        self.raw(json.dumps(e, separators=(",", ":")).encode() + b"\n")

    def prompt(self, t: float, text: str = PROMPT):
        self.write({**self._base("user", t), "message": {"role": "user", "content": text}})

    def assistant(self, t: float, blocks: list, stop=None, mid="msg1", out=10) -> dict:
        e = {**self._base("assistant", t), "message": {
            "id": mid, "type": "message", "role": "assistant", "model": "x", "content": blocks, "stop_reason": stop,
            "usage": {"input_tokens": 3, "output_tokens": out, "cache_read_input_tokens": 100}}}
        self.write(e)
        return e

    def tool(self, t: float, name: str, inp: dict, tid: str, mid: str | None = None, out=10):
        self.assistant(t, [{"type": "tool_use", "id": tid, "name": name, "input": inp}], "tool_use", mid or "m" + tid, out)

    def result(self, t: float, tid: str, content: str = f"ok {API_KEY} {EMAIL}"):
        self.write({**self._base("user", t), "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "content": content}]},
            "toolUseResult": {"stdout": content, "stderr": HOME, "filePath": rf"{CLIENT_DIR}\ledger.xlsx"}})

    def text(self, t: float, text: str, stop=None, mid="mt", out=10):
        self.assistant(t, [{"type": "text", "text": text}], stop, mid, out)

    def noise(self, t: float):
        """Entry types that carry prompt text under other names."""
        self.write({"type": "ai-title", "aiTitle": f"{CLIENT} invoice dispute for {NAME}", "sessionId": self.sid})
        self.write({"type": "last-prompt", "lastPrompt": PROMPT, "leafUuid": "x", "sessionId": self.sid})
        self.write({"type": "queue-operation", "operation": "enqueue", "timestamp": iso(t), "content": PROMPT, "sessionId": self.sid})
        self.write({**self._base("attachment", t), "attachment": {"type": "file", "path": rf"{HOME}\notes.txt"}, "rendered": EMAIL})
        self.write({**self._base("system", t), "subtype": "local_command", "content": f"curl {URL}"})


@pytest.fixture
def root(tmp_path):
    return tmp_path / "projects"


def serve(tracker: Tracker):
    server = FeedServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def fetch(url: str):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, dict(r.headers), r.read()


def by_alias(doc: dict, alias: str) -> dict:
    hits = [s for s in doc["sessions"] if s["alias"] == alias]
    assert len(hits) == 1, [s["alias"] for s in doc["sessions"]]
    return hits[0]


def assert_clean(blob: bytes, extra=()):
    text = blob.decode("utf-8")
    low = text.lower()
    for s in [*SECRETS, *extra]:
        assert s.lower() not in low, f"leaked {s!r}"
    assert "\\" not in text and "@" not in text and "/" not in text


def busy_fixture(root: Path, now: float) -> None:
    """A classified client session, a home-directory session and a public one, each soaked in secrets."""
    c = Transcript(root, f"C--Users-{USER}-Documents-Projects-work-{CLIENT}", "11111111-aaaa", CLIENT_DIR)
    c.noise(now - 60)
    c.prompt(now - 50)
    c.assistant(now - 49, [{"type": "thinking", "thinking": f"{NAME} wants the passphrase rotated"}])
    c.text(now - 48, f"Sure {NAME}, I will email {EMAIL}")
    c.tool(now - 47, "Read", {"file_path": rf"{CLIENT_DIR}\payroll-{USER}.csv"}, "c1")
    c.result(now - 46, "c1")
    c.tool(now - 45, "WebFetch", {"url": URL, "prompt": QUERY}, "c2")
    c.result(now - 44, "c2")
    c.tool(now - 43, "Grep", {"pattern": QUERY, "path": HOME}, "c3")
    c.result(now - 42, "c3")
    c.tool(now - 41, "Bash", {"command": f"curl -H 'Authorization: Bearer {API_KEY}' {URL}", "description": f"call {CLIENT} api"}, "c4")
    c.result(now - 40, "c4")
    c.tool(now - 39, "mcp__gmail__send_message", {"to": EMAIL, "body": PROMPT}, "c5")
    c.result(now - 38, "c5")
    c.tool(now - 37, "Edit", {"file_path": rf"{CLIENT_DIR}\{CLIENT}-invoice.md", "old_string": NAME, "new_string": EMAIL}, "c6")

    h = Transcript(root, f"C--Users-{USER}", "22222222-bbbb", HOME)
    h.prompt(now - 30)
    h.tool(now - 29, "Write", {"file_path": rf"{HOME}\{NAME}.txt", "content": API_KEY}, "h1")
    h.result(now - 28, "h1")
    h.tool(now - 27, "Agent", {"description": f"audit {CLIENT}", "prompt": PROMPT, "subagent_type": "Explore"}, "h2")
    sub = Transcript(root, f"C--Users-{USER}", "22222222-bbbb", HOME, sub="a1b2c3")
    sub.prompt(now - 26)
    sub.tool(now - 25, "PowerShell", {"command": f"Get-Content {HOME}\\.ssh\\id_ed25519 # {API_KEY}"}, "s1")

    p = Transcript(root, f"C--Users-{USER}-Documents-Projects-pubproj", "33333333-cccc", PUB)
    p.noise(now - 20)
    p.prompt(now - 19)
    p.tool(now - 18, "Edit", {"file_path": rf"{PUB}\src\stage.html", "old_string": EMAIL, "new_string": API_KEY}, "p1")


# ---------------------------------------------------------------- privacy

def test_served_json_and_log_never_contain_planted_secrets(root, tmp_path, caplog):
    now = time.time()
    busy_fixture(root, now)
    tracker = Tracker(root, CFG)
    server, base = serve(tracker)
    stop = threading.Event()
    with caplog.at_level("INFO", logger="agentfeed"):
        loop = threading.Thread(target=agentfeed.serve, args=(tracker, server, stop), daemon=True)
        loop.start()
        try:
            deadline = time.time() + 10
            while True:
                status, headers, body = fetch(base + "/agents.json")
                doc = json.loads(body)
                if doc["sessions"] or time.time() > deadline:
                    break
                time.sleep(0.05)
        finally:
            stop.set()
            loop.join(5)
            server.shutdown()
            server.server_close()
    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Cache-Control"] == "no-store"
    assert doc["schema"] == 1 and len(doc["sessions"]) == 3
    assert_clean(body)
    assert_clean(caplog.text.replace("\\", "").replace("/", "").replace("@", "").encode())  # log: secrets only
    assert "sessions=3" in caplog.text
    # the fixture really exercised the interesting paths
    assert sorted(s["alias"] for s in doc["sessions"]) == ["Classified", "Classified", "pubproj"]
    assert by_alias(doc, "pubproj")["action"] == "Editing stage.html"
    assert {s["action"] for s in doc["sessions"] if not s["public"]} == {"Editing", "Running a command"}


def test_tracker_keeps_no_transcript_text(root):
    now = time.time()
    busy_fixture(root, now)
    tracker = Tracker(root, {"projects": []})   # no allowlist: nothing may be kept for display
    tracker.poll(now)
    seen = []

    def walk(o, depth=0):
        if isinstance(o, (str, bytes)):
            seen.append(o if isinstance(o, str) else o.decode("latin1"))
        elif isinstance(o, dict):
            [walk(v, depth + 1) for v in o.values()]
        elif isinstance(o, (list, tuple, set)):
            [walk(v, depth + 1) for v in o]
        elif hasattr(o, "__dict__") and depth < 6:
            walk(vars(o), depth + 1)

    for s in tracker.sessions.values():
        for st in s.streams():
            held = {k: v for k, v in vars(st).items() if k not in ("path", "cwd", "file_path")}
            walk(held)
    blob = "\n".join(seen).lower()
    for s in (PROMPT, API_KEY, EMAIL, URL, QUERY, NAME):
        assert s.lower() not in blob


def test_not_found_and_preflight(root):
    server, base = serve(Tracker(root))
    try:
        with pytest.raises(urllib.error.HTTPError) as e:
            fetch(base + "/other")
        assert e.value.code == 404
        req = urllib.request.Request(base + "/agents.json", method="OPTIONS")
        with urllib.request.urlopen(req, timeout=5) as r:
            assert r.status == 204 and r.headers["Access-Control-Allow-Origin"] == "*"
        status, _, body = fetch(base + "/agents.json?x=1")
        assert status == 200 and json.loads(body)["sessions"] == []
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------- allowlist

def test_without_config_everything_is_classified(root):
    now = time.time()
    busy_fixture(root, now)
    doc = Tracker(root).poll(now)
    assert len(doc["sessions"]) == 3
    assert all(s["alias"] == "Classified" and not s["public"] and s["file"] is None for s in doc["sessions"])
    assert {s["action"] for s in doc["sessions"]} == {"Editing", "Running a command"}
    assert_clean(encode(doc), extra=["pubproj", "stage.html"])


def edit_in(root, cwd, file_path, cfg=CFG, tool="Edit"):
    now = time.time()
    t = Transcript(root, "slug", "44444444-dddd", cwd)
    t.prompt(now - 5)
    t.tool(now - 4, tool, {"file_path": file_path}, "t1")
    return Tracker(root, cfg).poll(now)["sessions"][0]


@pytest.mark.parametrize("cwd, file_path, alias, action", [
    (PUB, rf"{PUB}\src\stage.html", "pubproj", "Editing stage.html"),
    (PUB, f"{PUB}/src/stage.html".replace("\\", "/"), "pubproj", "Editing stage.html"),         # forward slashes
    (PUB.upper(), rf"{PUB.lower()}\README.md", "pubproj", "Editing README.md"),                  # case-insensitive
    (rf"{PUB}\src", r"deep\widget.ts", "pubproj", "Editing widget.ts"),                           # relative to cwd
    (PUB, f"/c/Users/{USER}/Documents/Projects/pubproj/a.py", "pubproj", "Editing a.py"),         # msys form
    (PUB, rf"{CLIENT_DIR}\{CLIENT}.md", "pubproj", "Editing"),                                    # file outside the project
    (PUB, rf"{PUB}\..\work\{CLIENT}\x.md", "pubproj", "Editing"),                                 # .. escape
    (PUB, rf"{PUB}\career\{CLIENT}-offer.md", "pubproj", "Editing"),                              # excluded folder
    (PUB, rf"{PUB}\notes\drafts\x.md", "pubproj", "Editing"),                                     # excluded nested folder
    (PUB, rf"{PUB}\notes\public.md", "pubproj", "Editing public.md"),                             # sibling of an exclusion
    (PUB, rf"{PUB}\.env", "pubproj", "Editing"),                                                  # dot file
    (PUB, rf"{PUB}\.claude\settings.json", "pubproj", "Editing"),                                 # dot folder
    (PUB, rf"{PUB}\src\{USER}-notes.md", "pubproj", "Editing"),                                   # denied term in the name
    (PUB, rf"{PUB}\src\a" + "\u202e" + "gnp.exe", "pubproj", "Editing"),                               # bidi override
    (PUB, rf"{PUB}\src\a@b.txt", "pubproj", "Editing"),                                           # address-like
    (PUB + "-private", rf"{PUB}-private\secret.md", "Classified", "Editing"),                     # prefix lookalike
    (CLIENT_DIR, rf"{CLIENT_DIR}\plan.md", "Classified", "Editing"),
    (CLIENT_DIR, rf"{PUB}\src\stage.html", "Classified", "Editing"),                              # classified session, public file
    (HOME, rf"{HOME}\notes.md", "Classified", "Editing"),
])
def test_allowlist(root, cwd, file_path, alias, action):
    s = edit_in(root, cwd, file_path)
    assert (s["alias"], s["action"]) == (alias, action)
    assert s["public"] == (alias != "Classified")


def test_read_never_names_the_file(root):
    assert edit_in(root, PUB, rf"{PUB}\src\stage.html", tool="Read")["action"] == "Reading"


def test_long_names_are_truncated(root):
    s = edit_in(root, PUB, rf"{PUB}\{'x' * 60}.md")
    assert s["file"].endswith("\u2026") and len(s["file"]) == 32 and len(s["action"]) <= agentfeed.MAX_TEXT


def test_denied_project_name_falls_back_to_classified(root):
    cfg = {"projects": [{"path": HOME, "name": f"{USER} home"}], "deny": [USER]}
    assert edit_in(root, HOME, rf"{HOME}\a.md", cfg)["alias"] == "Classified"


# ---------------------------------------------------------------- vocabulary

@pytest.mark.parametrize("command, kind", [
    ("git status", "git"), ("  git.exe push origin main", "git"),
    ("pytest -q", "tests"), ("python -m pytest test_x.py", "tests"), ("bun test", "tests"), ("npm test -- --run", "tests"),
    ("bun run build", "build"), ("npm install", "build"), ("npx astro check", "build"),
    (f"curl -H 'Bearer {API_KEY}' {URL}", "command"), ("cd repo && git push", "command"),
    (rf"{HOME}\bin\git.exe status", "command"), ("FOO=1 git push", "command"), ("", "command"), (None, "command"),
])
def test_command_kind(command, kind):
    assert command_kind(command) == kind


@pytest.mark.parametrize("name, inp, action", [
    ("Grep", {"pattern": QUERY}, "Searching"), ("Glob", {"pattern": "**/*"}, "Searching"),
    ("Bash", {"command": f"echo {API_KEY}"}, "Running a command"), ("PowerShell", {"command": "git log"}, "Using git"),
    ("Bash", {"command": "python -m pytest"}, "Running tests"), ("Bash", {"command": "bun run build"}, "Building"),
    ("Agent", {"prompt": PROMPT}, "Dispatching an agent"), ("WebSearch", {"query": QUERY}, "Researching"),
    ("WebFetch", {"url": URL}, "Researching"), ("mcp__claude-in-chrome__navigate", {"url": URL}, "Driving a browser"),
    ("mcp__plugin_chrome-devtools-mcp_chrome-devtools__click", {}, "Driving a browser"),
    (f"mcp__{CLIENT}__lookup", {"q": QUERY}, "Working"), ("SomethingNew", {}, "Working"), (None, None, "Working"),
])
def test_action_vocabulary(root, name, inp, action):
    now = time.time()
    t = Transcript(root, "slug", "55555555-eeee", PUB)
    t.tool(now - 1, name, inp, "t1")
    s = Tracker(root, CFG).poll(now)["sessions"][0]
    assert s["action"] == action and s["state"] == "tool"


# ---------------------------------------------------------------- state

def test_state_transitions_and_counters(root):
    now = time.time()
    t = Transcript(root, "slug", "66666666-ffff", PUB)
    tr = Tracker(root, CFG)

    def state():
        s = tr.poll(now)["sessions"][0]
        return s["state"], s["action"]

    t.prompt(now - 20)
    assert state() == ("thinking", "Thinking")
    t.assistant(now - 19, [{"type": "thinking", "thinking": "hm"}], None, "m1", 5)
    assert state() == ("thinking", "Thinking")
    # one API message, written as three entries with the same id and a growing usage figure
    t.assistant(now - 18, [{"type": "text", "text": "on it"}], None, "m1", 40)
    t.assistant(now - 17, [{"type": "tool_use", "id": "a", "name": "Grep", "input": {"pattern": "x"}}], "tool_use", "m1", 90)
    assert state() == ("tool", "Searching")
    t.tool(now - 16, "Bash", {"command": "git status"}, "b", mid="m1", out=90)   # parallel tool call, same message
    assert state() == ("tool", "Using git")
    t.result(now - 15, "a")
    assert state() == ("tool", "Using git")          # one of the two is still running
    t.result(now - 14, "b")
    assert state() == ("thinking", "Thinking")
    t.text(now - 13, "all done", "end_turn", "m2", 25)
    assert state() == ("idle", "Standing by")
    s = tr.poll(now)["sessions"][0]
    assert s["tool_calls"] == 2
    assert s["tokens_out"] == 90 + 25                # m1 counted once, not 5 + 40 + 90 + 90
    assert s["age_s"] == 20 and s["idle_s"] == 13 and s["subagents"] == 0
    assert tr.poll(now)["totals"] == {"sessions": 1, "working": 0, "subagents": 0, "tool_calls": 2, "tokens_out": 115}

    t.prompt(now - 5)
    t.tool(now - 4, "Read", {"file_path": "x"}, "c")
    t.write({**t._base("system", now - 3), "subtype": "turn_duration", "durationMs": 5})   # turn ended without end_turn
    assert state() == ("idle", "Standing by")


def test_thinking_goes_idle_when_the_transcript_stops_moving(root):
    now = time.time()
    t = Transcript(root, "slug", "77777777-aaaa", PUB)
    t.prompt(now)
    tr = Tracker(root, CFG)
    assert tr.poll(now + 10)["sessions"][0]["state"] == "thinking"
    assert tr.poll(now + agentfeed.THINK_STALE_S + 5)["sessions"][0]["state"] == "idle"


def test_subagents(root):
    now = time.time()
    main = Transcript(root, "slug", "88888888-bbbb", PUB)
    main.prompt(now - 30)
    main.tool(now - 29, "Agent", {"prompt": PROMPT}, "m1")
    a = Transcript(root, "slug", "88888888-bbbb", PUB, sub="aaa")
    a.prompt(now - 28)
    a.tool(now - 5, "Edit", {"file_path": rf"{PUB}\src\card.css"}, "a1", out=7)
    b = Transcript(root, "slug", "88888888-bbbb", PUB, sub="bbb")
    b.prompt(now - 28)
    b.text(now - 20, "report", "end_turn")          # finished
    (root / "slug" / "88888888-bbbb" / "tool-results").mkdir()
    (root / "slug" / "88888888-bbbb" / "tool-results" / "x.jsonl").write_text(PROMPT + "\n")
    tr = Tracker(root, CFG)
    doc = tr.poll(now)
    assert len(doc["sessions"]) == 1                 # subagents fold into their session
    s = doc["sessions"][0]
    assert (s["state"], s["subagents"], s["action"]) == ("tool", 1, "Editing card.css")
    assert s["tool_calls"] == 2 and s["tokens_out"] == 10 + 7 + 10
    assert doc["totals"]["subagents"] == 1
    # the subagent goes quiet: the session reads as dispatching again, with none running
    s = tr.poll(now + agentfeed.SUBAGENT_LIVE_S)["sessions"][0]
    assert (s["subagents"], s["action"]) == (0, "Dispatching an agent")


def test_session_drops_out_after_idle(root):
    now = time.time()
    t = Transcript(root, "slug", "99999999-cccc", PUB)
    t.prompt(now - 5)
    t.tool(now - 4, "Grep", {}, "g")
    tr = Tracker(root, CFG)
    assert len(tr.poll(now)["sessions"]) == 1
    assert len(tr.poll(now + 590)["sessions"]) == 1
    doc = tr.poll(now + 610)
    assert doc["sessions"] == [] and doc["totals"]["sessions"] == 0
    assert tr.sessions == {}                         # forgotten, not just hidden
    # a transcript whose file is fresh but whose last real entry is old is not shown either
    t.path.unlink()
    old = Transcript(root, "slug", "99999999-dddd", PUB)
    old.prompt(now - 5000)
    old.write({"type": "mode", "mode": "x", "sessionId": "s"})
    assert Tracker(root, CFG).poll(now)["sessions"] == []


def test_partial_last_line_waits_for_its_newline(root):
    now = time.time()
    t = Transcript(root, "slug", "aaaaaaaa-dddd", PUB)
    t.prompt(now - 9)
    tr = Tracker(root, CFG)
    assert tr.poll(now)["sessions"][0]["state"] == "thinking"
    line = json.dumps({**t._base("assistant", now - 3), "message": {
        "id": "m9", "content": [{"type": "tool_use", "id": "z", "name": "Grep", "input": {}}],
        "stop_reason": "tool_use", "usage": {"output_tokens": 4}}}).encode() + b"\n"
    t.raw(line[:40])
    s = tr.poll(now)["sessions"][0]
    assert (s["state"], s["tool_calls"]) == ("thinking", 0)
    t.raw(line[40:-1])                               # everything but the newline
    assert tr.poll(now)["sessions"][0]["tool_calls"] == 0
    t.raw(b"\n")
    s = tr.poll(now)["sessions"][0]
    assert (s["state"], s["action"], s["tool_calls"], s["tokens_out"]) == ("tool", "Searching", 1, 4)
    t.raw(b"{not json at all}\n\n[1,2]\n\"str\"\n")   # garbage lines are skipped, not fatal
    t.result(now - 1, "z")
    assert tr.poll(now)["sessions"][0]["state"] == "thinking"


def test_large_file_is_read_incrementally(root):
    now = time.time()
    t = Transcript(root, "slug", "bbbbbbbb-eeee", PUB)
    t.prompt(now - 9)
    t.result(now - 8, "none", "x" * 3_000_000)
    tr = Tracker(root, CFG)
    tr.poll(now)
    st = next(iter(tr.sessions.values())).main
    size = st.offset
    assert size == t.path.stat().st_size > 3_000_000
    assert st.read() is False                        # nothing new: no read at all
    t.tool(now - 1, "Glob", {}, "g")
    opened = []
    real_open = open

    def spy(path, mode="r", *a, **k):
        f = real_open(path, mode, *a, **k)
        opened.append(f)
        return f

    agentfeed.open = spy
    try:
        assert tr.poll(now)["sessions"][0]["action"] == "Searching"
    finally:
        del agentfeed.open
    assert len(opened) == 1 and st.offset == t.path.stat().st_size
    assert st.offset - size < 2000                   # only the appended entry was consumed
    t.path.write_bytes(b"")                          # truncated: counters start over instead of going stale
    t.prompt(now)
    assert tr.poll(now)["sessions"][0]["tool_calls"] == 0


# ---------------------------------------------------------------- process

def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_second_instance_exits_cleanly(root, tmp_path):
    now = time.time()
    busy_fixture(root, now)
    port = free_port()
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(CFG))
    cmd = [sys.executable, str(HERE / "agentfeed.py"), "--root", str(root), "--port", str(port), "--config", str(cfg)]
    first = subprocess.Popen([*cmd, "--log", str(tmp_path / "one.log")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        url = f"http://127.0.0.1:{port}/agents.json"
        deadline = time.time() + 15
        body = b""
        while time.time() < deadline:
            try:
                body = fetch(url)[2]
                if json.loads(body)["sessions"]:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        assert len(json.loads(body)["sessions"]) == 3
        assert_clean(body)
        second = subprocess.run([*cmd, "--log", str(tmp_path / "two.log")], capture_output=True, timeout=20)
        assert second.returncode == 3
        assert b"Traceback" not in second.stderr and b"another instance" in second.stderr
        assert first.poll() is None                  # the first one is still serving
        assert fetch(url)[0] == 200
    finally:
        first.kill()
        first.communicate(timeout=10)
    for name in ("one.log", "two.log"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        for s in SECRETS:
            assert s.lower() not in text.lower()
        assert "\\" not in text and "@" not in text


def test_once_prints_a_snapshot(root, tmp_path):
    now = time.time()
    busy_fixture(root, now)
    out = subprocess.run([sys.executable, str(HERE / "agentfeed.py"), "--root", str(root), "--once",
                          "--config", str(tmp_path / "missing.json")], capture_output=True, timeout=20)
    assert out.returncode == 0
    assert len(json.loads(out.stdout)["sessions"]) == 3
    assert_clean(out.stdout.strip())
