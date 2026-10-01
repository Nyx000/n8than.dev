"""Claude Code activity feed for the stream overlay, served as JSON on 127.0.0.1.

Tails the session transcripts Claude Code writes under ~/.claude/projects and serves metadata
only: which sessions are active, what kind of tool each is running, and a few counters. Prompt
text, assistant text, tool inputs and outputs, commands, URLs and paths are never emitted, logged
or kept: each transcript line is parsed, a handful of fields are read, and the line is dropped.

    pythonw agentfeed.py                 # settings from config.json beside this file, if present
    python agentfeed.py --once           # print one snapshot and exit (no server)

Serves http://127.0.0.1:47801/agents.json. Schema and privacy rules: README.md.
"""
import argparse
import hashlib
import json
import logging
import ntpath
import os
import re
import socket
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
log = logging.getLogger("agentfeed")

SCHEMA = 1
DEFAULTS = {
    "port": 47801,
    "idle_s": 600,                    # a session silent this long drops out of the feed
    "classified_label": "Classified", # alias of every session outside the allowlist
    "projects": [],                   # the allowlist: [{"path": ..., "name": ..., "exclude": [...]}]
    "deny": [],                       # extra strings that must never be served (the OS user name is always denied)
}
POLL_S = 1.0
DISCOVER_S = 5.0          # how often the transcript folders are listed for new or resumed files
RECENT_MAIN_S = 6 * 3600  # sessions whose main transcript moved this recently get their subagent folders listed
THINK_STALE_S = 180       # "thinking" with no transcript writes for this long reads as idle (interrupted, or waiting on the user)
SUBAGENT_LIVE_S = 90      # a subagent transcript written this recently counts as running
MAX_SESSIONS = 12
MAX_TEXT = 48

# ---------------------------------------------------------------- vocabulary (the only words the feed can say)

PHRASE = {
    "edit": "Editing",
    "read": "Reading",
    "search": "Searching",
    "command": "Running a command",
    "git": "Using git",
    "tests": "Running tests",
    "build": "Building",
    "agent": "Dispatching an agent",
    "research": "Researching",
    "browser": "Driving a browser",
    "work": "Working",
    "think": "Thinking",
    "idle": "Standing by",
}
TOOL_KIND = {
    "Edit": "edit", "Write": "edit", "MultiEdit": "edit", "NotebookEdit": "edit",
    "Read": "read",
    "Grep": "search", "Glob": "search",
    "Bash": "command", "PowerShell": "command",
    "Agent": "agent", "Task": "agent",
    "WebSearch": "research", "WebFetch": "research",
}
FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_BROWSER = re.compile(r"chrome|browser|playwright|puppeteer", re.I)

# a command is classified by its first word (and one following word) against this map; nothing of it is kept
_CMD = re.compile(r"\s*([A-Za-z0-9_.\-]+)(?:\s+(?:-m\s+)?([A-Za-z0-9_.\-]+))?")
_TEST_RUNNERS = {"pytest", "vitest", "jest"}
_PYTHON = {"python", "python3", "py"}
_BUILDERS = {"bun", "bunx", "npm", "npx", "pnpm", "yarn", "cargo", "tsc", "vite", "astro", "make"}


def command_kind(command) -> str:
    if not isinstance(command, str):
        return "command"
    m = _CMD.match(command[:200])
    if not m:
        return "command"
    first = m.group(1).lower().removesuffix(".exe")
    second = (m.group(2) or "").lower()
    if first == "git":
        return "git"
    if first in _TEST_RUNNERS or (first in _PYTHON and second == "pytest") or (first in _BUILDERS and second == "test"):
        return "tests"
    if first in _BUILDERS:
        return "build"
    return "command"


def tool_kind(name) -> str:
    if not isinstance(name, str):
        return "work"
    if name in TOOL_KIND:
        return TOOL_KIND[name]
    if name.startswith("mcp__") and _BROWSER.search(name):
        return "browser"
    return "work"


# ---------------------------------------------------------------- scrubbing

_CTRL = re.compile(r"[\u0000-\u001f\u007f-\u009f​-‏‪-‮⁠-⁩﻿]+")
_FORBIDDEN = re.compile(r"[\\/@:<>|\"*?]")
_BASENAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\- ]{0,63}")


def clean(value, limit: int = MAX_TEXT) -> str:
    """Control and bidirectional characters out, whitespace collapsed, length capped."""
    s = " ".join(_CTRL.sub(" ", str(value)).split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


class Scrubber:
    """Last gate before a string is served: anything path-like, address-like or denied is refused."""

    def __init__(self, deny=()):
        terms = {str(t).lower() for t in deny if isinstance(t, str) and len(t) >= 3}
        for t in (os.environ.get("USERNAME"), os.environ.get("USER"), Path.home().name):
            if t and len(t) >= 3:
                terms.add(t.lower())
        self.terms = tuple(sorted(terms))

    def ok(self, s: str) -> bool:
        low = s.lower()
        return bool(s) and not _FORBIDDEN.search(s) and not any(t in low for t in self.terms)

    def text(self, value, limit: int = MAX_TEXT):
        """The cleaned string, or None if it must not be served."""
        s = clean(value, limit)
        return s if self.ok(s) else None


def norm_path(p, cwd: str | None = None) -> str | None:
    """Windows path, case-folded, backslashes; accepts forward slashes and /c/... forms. None if unusable."""
    if not isinstance(p, str) or not p or len(p) > 1024 or "\x00" in p:
        return None
    p = p.replace("/", "\\")
    m = re.match(r"^\\([A-Za-z])\\", p)
    if m:
        p = m.group(1) + ":" + p[2:]
    if not ntpath.isabs(p):
        if not cwd:
            return None
        p = ntpath.join(cwd, p)
    return ntpath.normcase(ntpath.normpath(p)).rstrip("\\")


def inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "\\")


class Project:
    def __init__(self, name: str, root: str, exclude):
        self.name, self.root = name, root
        self.exclude = tuple(x for x in (norm_rel(e) for e in exclude) if x)


def norm_rel(p) -> str | None:
    if not isinstance(p, str):
        return None
    return ntpath.normcase(p.replace("/", "\\")).strip("\\") or None


class Allowlist:
    """Maps a working directory to a public project name, and decides whether a file name may be shown."""

    def __init__(self, cfg: dict, scrub: Scrubber):
        self.scrub = scrub
        self.label = scrub.text(cfg.get("classified_label") or "") or DEFAULTS["classified_label"]
        self.projects: list[Project] = []
        for item in cfg.get("projects") or []:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                continue
            root = norm_path(os.path.expandvars(os.path.expanduser(item["path"])))
            if not root:
                continue
            name = scrub.text(item.get("name") or ntpath.basename(root), 24)
            if name:
                self.projects.append(Project(name, root, item.get("exclude") or []))
        self.projects.sort(key=lambda p: -len(p.root))  # the deepest matching root wins

    def project(self, cwd) -> Project | None:
        path = norm_path(cwd)
        if path:
            for p in self.projects:
                if inside(path, p.root):
                    return p
        return None

    def filename(self, project: Project | None, file_path, cwd) -> str | None:
        """Basename of file_path, only if it lies inside `project`, outside its excluded and dot folders."""
        if project is None:
            return None
        path = norm_path(file_path, norm_path(cwd))
        if not path or not inside(path, project.root) or path == project.root:
            return None
        rel = path[len(project.root) + 1:]
        parts = rel.split("\\")
        if any(part.startswith(".") or part == "node_modules" for part in parts):
            return None
        if any(inside(rel, ex) for ex in project.exclude):
            return None
        # the display name keeps the case as written; normalisation above was only for matching
        base = ntpath.basename(str(file_path).replace("/", "\\"))
        if not _BASENAME.fullmatch(base):
            return None
        return self.scrub.text(base, 32)


# ---------------------------------------------------------------- transcripts

def parse_ts(v) -> float | None:
    if not isinstance(v, str):
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


_SETTLED = (None, "tool_use", "pause_turn")  # stop reasons that do not end the turn


class Stream:
    """One transcript file, read incrementally. Holds counters and the current state, never content."""

    def __init__(self, path: str, is_sub: bool):
        self.path, self.is_sub = path, is_sub
        self.offset = 0
        self.size = -1
        self.mtime = 0.0
        self.cwd: str | None = None
        self.started: float | None = None
        self.last: float | None = None      # timestamp of the last assistant/user/turn-end entry
        self.state = "idle"
        self.kind = "idle"
        self.file_path: str | None = None   # path of the file being edited; turned into a name (or nothing) at render time
        self.pending: set[str] = set()      # tool_use ids without a result yet
        self.tool_calls = 0
        self.tokens = 0
        self._msg_id = None
        self._msg_out = 0

    def read(self) -> bool:
        """Consume complete new lines. A line without its newline yet is left for the next poll."""
        st = os.stat(self.path)
        if st.st_size == self.size and st.st_mtime == self.mtime:
            return False
        if st.st_size < self.offset:  # truncated or replaced: start over
            self.__init__(self.path, self.is_sub)
        self.size, self.mtime = st.st_size, st.st_mtime
        if st.st_size == self.offset:
            return False
        with open(self.path, "rb") as f:
            f.seek(self.offset)
            for line in f:
                if not line.endswith(b"\n"):
                    break
                self.offset += len(line)
                self._line(line)
        return True

    def _line(self, line: bytes):
        try:
            e = json.loads(line)
        except ValueError:
            return  # a torn or foreign line carries nothing we can use
        if isinstance(e, dict):
            self._entry(e)

    def _entry(self, e: dict):
        kind = e.get("type")
        if kind not in ("assistant", "user", "system"):
            return
        ts = parse_ts(e.get("timestamp"))
        if kind == "system":
            if e.get("subtype") in ("turn_duration", "stop_hook_summary"):
                self._idle(ts)
            return
        if isinstance(e.get("cwd"), str):
            self.cwd = e["cwd"]
        if ts is not None:
            self.started = ts if self.started is None else min(self.started, ts)
            self.last = ts if self.last is None else max(self.last, ts)
        msg = e.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
        if kind == "user":
            if e.get("isMeta") is True:
                return  # injected context, not a prompt: it says nothing about what is running
            results = [b for b in blocks if b.get("type") == "tool_result"]
            for b in results:
                self.pending.discard(b.get("tool_use_id"))
            if not results:
                self.pending.clear()  # a new prompt: nothing from the turn before is still running
            if not self.pending:
                self.state, self.kind, self.file_path = "thinking", "think", None
            return
        self._usage(msg)
        for b in blocks:
            if b.get("type") == "tool_use" and isinstance(b.get("id"), str) and b["id"] not in self.pending:
                self.pending.add(b["id"])
                self.tool_calls += 1
                self._tool(b.get("name"), b.get("input"))
            elif b.get("type") in ("thinking", "text") and not self.pending:
                self.state, self.kind, self.file_path = "thinking", "think", None
        if msg.get("stop_reason") not in _SETTLED:
            self._idle(ts)

    def _tool(self, name, inp):
        inp = inp if isinstance(inp, dict) else {}
        self.state, self.kind, self.file_path = "tool", tool_kind(name), None
        if self.kind == "command":
            self.kind = command_kind(inp.get("command"))
        elif name in FILE_TOOLS:
            path = inp.get("file_path") or inp.get("notebook_path")
            self.file_path = path if isinstance(path, str) else None

    def _idle(self, ts):
        self.state, self.kind, self.file_path = "idle", "idle", None
        self.pending.clear()
        if ts is not None:
            self.last = ts if self.last is None else max(self.last, ts)

    def _usage(self, msg: dict):
        usage = msg.get("usage")
        out = usage.get("output_tokens") if isinstance(usage, dict) else None
        if not isinstance(out, int) or isinstance(out, bool) or out < 0:
            return
        # one API message is written as several entries that repeat its usage: count each message once
        if msg.get("id") is not None and msg.get("id") == self._msg_id:
            self.tokens += out - self._msg_out
        else:
            self.tokens += out
        self._msg_id, self._msg_out = msg.get("id"), out


class Session:
    def __init__(self, sid: str):
        self.sid = sid
        self.main: Stream | None = None
        self.subs: dict[str, Stream] = {}

    def streams(self):
        return ([self.main] if self.main else []) + list(self.subs.values())


class Tracker:
    """Finds recently written transcripts under `root`, tails them, and renders the feed document."""

    def __init__(self, root, cfg: dict | None = None):
        self.cfg = {**DEFAULTS, **(cfg or {})}
        self.root = str(root)
        self.idle_s = float(self.cfg["idle_s"])
        self.scrub = Scrubber(self.cfg.get("deny") or ())
        self.allow = Allowlist(self.cfg, self.scrub)
        self.sessions: dict[str, Session] = {}
        self.salt = os.urandom(8)
        self.read_errors = 0
        self._next_discover = 0.0

    # ---- discovery

    def _fresh(self, path: str, now: float) -> bool:
        try:
            return now - os.stat(path).st_mtime <= self.idle_s
        except OSError:
            return False  # gone between the listing and the stat

    def discover(self, now: float):
        try:
            projects = [d.path for d in os.scandir(self.root) if d.is_dir()]
        except OSError:
            return  # no transcript folder (yet): an empty feed is the right answer
        for proj in projects:
            try:
                entries = list(os.scandir(proj))
            except OSError:
                continue
            for e in entries:
                if not e.name.endswith(".jsonl") or not e.is_file():
                    continue
                # the listing's timestamps can lag for a file that is being appended to: stat anything from the last day
                if now - e.stat().st_mtime > 86400:
                    continue
                try:
                    mtime = os.stat(e.path).st_mtime
                except OSError:
                    continue
                sid = e.name[:-6]
                key = proj + "|" + sid
                if now - mtime <= self.idle_s:
                    s = self.sessions.setdefault(key, Session(sid))
                    if s.main is None:
                        s.main = Stream(e.path, False)
                if now - mtime <= RECENT_MAIN_S:
                    self._discover_subs(key, sid, os.path.join(proj, sid), now)

    def _discover_subs(self, key: str, sid: str, folder: str, now: float):
        if not os.path.isdir(folder):
            return
        for base, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d != "tool-results"]
            for name in files:
                path = os.path.join(base, name)
                s = self.sessions.get(key)
                if not name.endswith(".jsonl") or (s and path in s.subs) or not self._fresh(path, now):
                    continue
                s = self.sessions.setdefault(key, Session(sid))
                s.subs[path] = Stream(path, True)

    # ---- polling

    def poll(self, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        if now >= self._next_discover:
            self._next_discover = now + DISCOVER_S
            self.discover(now)
        for key in list(self.sessions):
            s = self.sessions[key]
            for st in s.streams():
                try:
                    st.read()
                except OSError:
                    self.read_errors += 1  # locked or deleted mid-read: the next poll retries from the same offset
            if all(now - st.mtime > self.idle_s for st in s.streams()):
                del self.sessions[key]
        return self.render(now)

    # ---- rendering

    def _view(self, s: Session, now: float) -> dict | None:
        streams = [st for st in s.streams() if st.last is not None]
        if not streams:
            return None
        last = min(now, max(st.last for st in streams))
        if now - last > self.idle_s:
            return None
        running = [st for st in s.subs.values()
                   if st.last is not None and st.state != "idle" and now - st.last <= SUBAGENT_LIVE_S]
        main = s.main if s.main and s.main.last is not None else None
        lead = main or max(streams, key=lambda st: st.last)
        state, kind, src = lead.state, lead.kind, lead
        if running and (state == "idle" or kind == "agent"):
            src = max(running, key=lambda st: st.last)   # the session is waiting on its agents: show what one is doing
            state, kind = "tool", src.kind if src.state == "tool" else "agent"
        elif state == "thinking" and now - last > THINK_STALE_S:
            state, kind = "idle", "idle"
        if state == "idle":
            kind = "idle"

        project = self.allow.project(lead.cwd)
        fname = self.allow.filename(project, src.file_path, src.cwd) if kind == "edit" and src.file_path else None
        phrase = PHRASE.get(kind, PHRASE["work"])
        action = self.scrub.text(f"{phrase} {fname}" if fname else phrase) or PHRASE["work"]
        started = min(st.started for st in streams if st.started is not None)
        return {
            "id": hashlib.sha256(self.salt + s.sid.encode("utf-8", "replace")).hexdigest()[:6],
            "alias": project.name if project else self.allow.label,
            "public": project is not None,
            "state": state,
            "kind": kind,
            "action": action,
            "file": fname,
            "tool_calls": sum(st.tool_calls for st in s.streams()),
            "tokens_out": sum(st.tokens for st in s.streams()),
            "subagents": len(running),
            "started": int(started),
            "age_s": max(0, int(now - started)),
            "last_activity": int(last),
            "idle_s": max(0, int(now - last)),
        }

    def render(self, now: float) -> dict:
        views = [v for v in (self._view(s, now) for s in self.sessions.values()) if v]
        views.sort(key=lambda v: (-v["last_activity"], v["id"]))
        views = views[:MAX_SESSIONS]
        return {
            "schema": SCHEMA,
            "updated": int(now),
            "window_s": int(self.idle_s),
            "totals": {
                "sessions": len(views),
                "working": sum(v["state"] != "idle" for v in views),
                "subagents": sum(v["subagents"] for v in views),
                "tool_calls": sum(v["tool_calls"] for v in views),
                "tokens_out": sum(v["tokens_out"] for v in views),
            },
            "sessions": views,
        }


def encode(doc: dict) -> bytes:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------- HTTP

class FeedServer(ThreadingHTTPServer):
    allow_reuse_address = False  # HTTPServer sets it, and on Windows it lets a second instance share the port
    daemon_threads = True
    body = encode({"schema": SCHEMA, "updated": 0, "window_s": 0, "sessions": [],
                   "totals": {"sessions": 0, "working": 0, "subagents": 0, "tool_calls": 0, "tokens_out": 0}})

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    def _headers(self, code: int, length: int = 0):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(length))

    def do_GET(self):
        if self.path.split("?", 1)[0] != "/agents.json":
            self._headers(404)
            self.end_headers()
            return
        body = self.server.body  # finished bytes, swapped whole by the poll loop
        self._headers(200, len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # CORS / private-network preflight, in case a page sends one
        self._headers(204)
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def log_message(self, *args):
        pass  # no per-request lines


# ---------------------------------------------------------------- main

def load_config(path: Path) -> dict:
    cfg = dict(DEFAULTS)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("config must be a JSON object")
        cfg.update(data)
    return cfg


def setup_logging(log_file: Path):
    handlers: list[logging.Handler] = [RotatingFileHandler(log_file, maxBytes=500_000, backupCount=1, encoding="utf-8")]
    if sys.stderr is not None:  # None under pythonw
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)


def serve(tracker: Tracker, server: FeedServer, stop: threading.Event):
    failures, summary = 0, None
    while not stop.is_set():
        try:
            doc = tracker.poll()
            server.body = encode(doc)
            failures = 0
            now = (doc["totals"]["sessions"], doc["totals"]["working"])
            if now != summary:  # counts only: nothing from a transcript is ever logged
                summary = now
                log.info("sessions=%d working=%d", *now)
        except Exception as e:
            # one bad poll must not end the overlay feed mid-stream; a persistent fault still does.
            # Only the exception's type is logged: its message could quote a path or a transcript line.
            failures += 1
            log.error("poll failed (%s), %d in a row", type(e).__name__, failures)
            if failures >= 20:
                raise
        stop.wait(POLL_S)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=HERE / "config.json", help="settings file (default config.json)")
    ap.add_argument("--root", type=Path, default=Path.home() / ".claude" / "projects", help="transcript folder")
    ap.add_argument("--port", type=int, help="HTTP port (default 47801)")
    ap.add_argument("--log", type=Path, default=HERE / "agentfeed.log", help="log file")
    ap.add_argument("--once", action="store_true", help="print one snapshot and exit")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    if a.port is not None:
        cfg["port"] = a.port
    if a.once:
        sys.stdout.write(encode(Tracker(a.root, cfg).poll()).decode("utf-8") + "\n")
        return 0
    setup_logging(a.log)
    if sys.platform == "win32":  # yield to the game and OBS
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL
    try:
        server = FeedServer(("127.0.0.1", cfg["port"]), Handler)
    except OSError:
        log.error("port %s is taken; another instance is probably running. Exiting.", cfg["port"])
        return 3
    tracker = Tracker(a.root, cfg)
    stop = threading.Event()
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()
    log.info("serving http://127.0.0.1:%s/agents.json, %d allowlisted projects", cfg["port"], len(tracker.allow.projects))
    try:
        serve(tracker, server, stop)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
