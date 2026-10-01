# agentfeed: Claude Code activity for the stream overlay

`agentfeed.py` watches the session transcripts Claude Code writes on the streamer's machine and serves a small JSON document at `http://127.0.0.1:47801/agents.json`. Both overlay themes (`../overlay/black-mesa/stage.html` and `../overlay/city17/stage.html`) poll it to show a row of per-session status lamps and one line naming what a session is doing. Python 3.14, standard library only.

## Privacy rules

The transcripts hold prompts, replies, commands, file contents, paths and credentials. The feed is built so that none of that can reach the JSON or the log.

| Rule | How it is enforced |
|---|---|
| Metadata only | Only `assistant`, `user` and `system` entries are read. From each the daemon takes the timestamp, the working directory, the stop reason, the output token count, and per content block its type, tool name and tool-use id. Every other entry type and field (titles, slugs, branch names, queued prompts, attachments, tool results) is ignored. |
| Nothing is kept | A line is parsed, those fields are read into counters and a state, and the parsed line is discarded. The only strings a tracked session holds are the transcript file's own path, its working directory and the path of the file being edited right now; the last two are used for the allowlist check and none of the three is served. |
| Fixed vocabulary | The action text is chosen from a fixed list keyed by tool name (table below). Tool inputs are never copied into it. |
| Commands | A shell command is matched against a small map by its first word (plus one following word, to tell `bun test` from `bun run`). The result is one of four fixed phrases. A command behind `cd x &&`, an environment prefix or a full path to an executable is always "Running a command". |
| Project names | A session shows a project name only when its working directory is inside a folder listed in `config.json`. Every other session, including any in the home directory, is `Classified`. Matching is case-insensitive, accepts `\`, `/` and `/c/...` forms, and requires a path separator after the folder name, so `project-private` does not match `project`. |
| File names | A file's base name is shown only for an edit, only in an allowlisted project, and only when the file is inside that project's folder, outside its `exclude` folders, outside any folder or file whose name starts with a dot, and outside `node_modules`. The name must consist of letters, digits, `_`, `.`, `-` and spaces. |
| Last gate | Every served string is stripped of control and bidirectional characters, truncated (48 characters; file names 32), and refused if it contains `\ / @ : < > | " * ?`, the OS user name, or any string in the config's `deny` list. A refused file name is dropped; a refused project name becomes `Classified`. |
| Session ids | The served `id` is the first 6 hex digits of a SHA-256 over the session id and a random salt drawn at each daemon start. Folder names under the transcript root are never served. |
| Log | `agentfeed.log` records the start line and session counts. A failed poll logs the exception's type only, never its message. |

Without a `config.json` the allowlist is empty: every session is `Classified` and no file name is ever shown.

## Run

```
C:\Python314\pythonw.exe "<repo>\deploy\live\agentfeed\agentfeed.py"
```

The daemon binds 127.0.0.1 only, answers with `Access-Control-Allow-Origin: *` and `Cache-Control: no-store`, and logs to `agentfeed.log` beside the script. A second instance finds the port taken, logs that, and exits with code 3. It runs at below-normal priority.

| Option | Default | Meaning |
|---|---|---|
| `--config` | `config.json` beside the script | Settings file |
| `--root` | `~/.claude/projects` | Transcript folder |
| `--port` | `47801` | HTTP port |
| `--log` | `agentfeed.log` beside the script | Log file |
| `--once` | off | Print one snapshot to stdout and exit, without serving |

## Settings: `config.json` (gitignored)

Copy `config.example.json` to `config.json` and list the projects that may be named on stream. The file is gitignored because it names folders on the streamer's machine.

| Key | Default | Meaning |
|---|---|---|
| `projects` | `[]` | The allowlist. Each item has `path` (`~` and environment variables are expanded), an optional display `name` (default: the folder name, at most 24 characters) and an optional `exclude` list of subfolders, relative to `path`, whose file names are never shown. |
| `classified_label` | `Classified` | Alias for every session outside the allowlist |
| `deny` | `[]` | Extra strings (3 characters or longer, case-insensitive) that must never be served. The OS user name is always denied. |
| `idle_s` | `600` | A session with no activity for this long drops out |
| `port` | `47801` | HTTP port |

## JSON schema (`schema: 1`)

| Field | Type | Meaning |
|---|---|---|
| `schema` | int | `1` |
| `updated` | epoch seconds | When this document was built (once a second) |
| `window_s` | int | The idle window, `idle_s` |
| `totals` | `{sessions, working, subagents, tool_calls, tokens_out}` | Sums over the sessions listed; `working` counts those not `idle` |
| `sessions` | array, most recently active first, at most 12 | One object per active session, fields below |

| Session field | Type | Meaning |
|---|---|---|
| `id` | 6 hex characters | Stable while the daemon runs; changes on restart |
| `alias` | string | Allowlisted project name, or the classified label |
| `public` | bool | `true` when `alias` is an allowlisted project |
| `state` | `thinking` \| `tool` \| `idle` | See the state rules below |
| `kind` | string | Vocabulary key of the action (table below) |
| `action` | string | Ready-made phrase, for example `Editing stage.html` or `Running tests` |
| `file` | string \| null | The file name inside `action`, when one may be shown |
| `tool_calls` | int | Tool calls in the main transcript plus the subagent transcripts the daemon is tracking |
| `tokens_out` | int | Output tokens over the same transcripts; each API message is counted once |
| `subagents` | int | Subagents running now |
| `started`, `age_s` | epoch s, int | First entry of the session and seconds since |
| `last_activity`, `idle_s` | epoch s, int | Last assistant, user or turn-end entry and seconds since |

| `kind` | `action` | Chosen when |
|---|---|---|
| `edit` | `Editing` or `Editing <file>` | Edit, Write, MultiEdit, NotebookEdit |
| `read` | `Reading` | Read |
| `search` | `Searching` | Grep, Glob |
| `command` | `Running a command` | Bash or PowerShell, anything not matched below |
| `git` | `Using git` | The command's first word is `git` |
| `tests` | `Running tests` | `pytest`, `vitest`, `jest`, `python -m pytest`, or a package runner followed by `test` |
| `build` | `Building` | `bun`, `bunx`, `npm`, `npx`, `pnpm`, `yarn`, `cargo`, `tsc`, `vite`, `astro`, `make` |
| `agent` | `Dispatching an agent` | Agent, Task |
| `research` | `Researching` | WebSearch, WebFetch |
| `browser` | `Driving a browser` | An MCP tool whose name contains `chrome`, `browser`, `playwright` or `puppeteer` |
| `work` | `Working` | Any other tool |
| `think` | `Thinking` | No tool is running and the turn has not ended |
| `idle` | `Standing by` | The turn has ended |

## State rules

| State | Rule |
|---|---|
| `tool` | An assistant entry carried a `tool_use` block whose id has no `tool_result` yet. With parallel tool calls the state holds until the last result arrives. |
| `thinking` | A prompt or the last pending tool result arrived, or the assistant wrote a thinking or text block, and the turn has not ended. After 180 s without a transcript write it reads as `idle` (an interrupted turn or a permission prompt leaves no end marker). |
| `idle` | An assistant entry with a final `stop_reason` (anything but `tool_use` or `pause_turn`), or a `turn_duration` or `stop_hook_summary` system entry. |
| Subagents | Transcripts under `<session id>/subagents/` and `<session id>/workflows/` belong to their session and never appear as sessions of their own. One counts as running when its last entry is under 90 s old and its turn has not ended. While a session is idle or dispatching and has running subagents, its action is the most recently active subagent's. |
| Dropout | A session whose last activity is older than `idle_s` (10 minutes) is removed and forgotten. |

## How it reads the transcripts

Every 5 s the daemon lists the project folders under the root and picks up `.jsonl` files modified within the idle window, plus the subagent folders of sessions whose main transcript moved in the last 6 hours. Once a second it stats each tracked file and, only if size or modification time changed, reads from its remembered offset to the end. A last line without its newline is left for the next poll, so nothing is buffered between polls. A file that shrank is read again from the start. A new file is read once in full (line by line, so memory stays flat), which gives exact counters for the main transcript. Subagent transcripts that finished more than `idle_s` before the daemon started are not read, so after a restart `tool_calls` and `tokens_out` can be lower than before it.

Measured 2026-09-30 on this machine (Ryzen 7 9800X3D) with two live sessions, one of them 17 MB: startup including the full first read took 0.23 s of CPU, then 1.77 s of CPU over 581 s (0.3% of one core) at 32 MB of memory.

## Tests

```
C:\Python314\python.exe -m pytest test_agentfeed.py
```

63 tests, about 3 s. The fixtures are synthetic transcripts soaked in invented secrets (a name, a home path with a user name, an email address, an API key inside a command, a client-style folder name, a prompt, a URL, a search query), placed in every field a real transcript has, including the prompt-derived ones (`slug`, `aiTitle`, `lastPrompt`, `gitBranch`, queue and attachment entries). The tests assert that none of those strings, and no `\`, `/` or `@`, appear in the served bytes or the log; that the allowlist holds in both directions (19 path cases); the command map; state transitions and token de-duplication; subagent folding; dropout; a torn last line; incremental reads; second-instance exit; and that the tracker's state holds no transcript text.
