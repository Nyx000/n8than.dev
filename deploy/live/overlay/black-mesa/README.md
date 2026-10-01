# Stream overlay: Black Mesa / Test Chamber C-33/a

Two OBS Browser Sources (local file) on a 1920x1080 canvas, built for the Deadlock scene. The theme is the Anomalous Materials test chamber control room: beige lab-console enamel, black CRT glass with amber phosphor readouts, hazard striping, the HEV suit's amber numerals, and one teal accent that is used only for wins. Each page is self-contained (inline CSS and JS, system fonts only: Bahnschrift, Consolas, Segoe UI), has a transparent background, and needs no assets.

It is a different composition from the City 17 theme one folder up. City 17 spreads three pieces around the frame (ticker top-left, clock top-right, a large webcam console mid-right). Black Mesa is one narrow equipment tower bolted to the top-right corner: an info console on top, the webcam window directly underneath, both 304 px wide with their right edges aligned. Everything else on the canvas is left clear.

## Placement

| Page | Size (w x h) | Canvas position (x, y) | Shown |
|---|---|---|---|
| `stage.html` | 1920 x 1080 | 0, 0 | Always |
| `webcam-frame.html` | 304 x 214 | 1604, 164 | Webcam on |
| Webcam source (your camera) | 288 x 162 | 1612, 190 | Webcam on, **below** `webcam-frame.html` in the source list |

`stage.html` paints only inside x 1603 to 1908, y 11 to 162 (measured on a magenta background, which includes the 1 px drop shadow). `webcam-frame.html` paints x 1604 to 1908, y 164 to 378. The 4 px gap between the two is deliberate, so they read as two stacked units when the webcam is on and the console stands alone in the corner when it is off.

## Webcam hole (16:9, fully transparent)

| Coordinates | x | y | w | h |
|---|---|---|---|---|
| Page (`webcam-frame.html`) | 8 | 26 | 288 | 162 |
| Canvas | 1612 | 190 | 288 | 162 |

The frame is one element clipped with an even-odd `clip-path` that cuts the hole out, so no background, glow or scanline can paint into it. Verified against a magenta background: 0 of 104,976 device pixels inside the hole were painted (432 x 243 at 1.5x device scale, all edges on whole pixels, so the same holds at 1x), and the glass starts on the adjacent pixel.

## OBS Browser Source settings

| Page | Width | Height | FPS |
|---|---|---|---|
| `stage.html` | 1920 | 1080 | 30 |
| `webcam-frame.html` | 304 | 214 | 30 |

Tick **Local file**. The default Custom CSS is harmless and can stay. 30 fps is plenty: all motion is a few blinks, a short card fade and a stepped power meter, on opacity and transform, plus once-a-second text updates. Leave "Shutdown source when not visible" off on `stage.html` so the stream uptime and polling keep running.

## What the console shows

The console is the always-on piece. Its top strip has two faces that cross-fade. The lower half is one rotating card.

| Piece | Shows | Data source | Fallback |
|---|---|---|---|
| On air tile | Time since the broadcast started, as H:MM:SS | `onlineTime` from `/api/live/status` | Whole top strip switches to the idle face |
| Watching tile | Viewer count | `readers.length` from `/api/live/status` | Same idle face |
| Session tile | Wins and losses since the broadcast started (teal wins, orange losses) plus the result of the last five games as small squares | Deadlock match history (see below) | Streamer clock (H:MM) labelled "Streamer time" |
| Idle face | Lambda, "Nyx000", "HEV suit online", wall clock | Local clock only | Always available; shown whenever status is missing, stale (over 100 s) or not online |
| Now playing card | Track and artists | `/api/spotify/now-playing` | Card is left out of the rotation when nothing is playing |
| Chat card | Name and the latest chat line, two lines max, with its age | `/api/live/chat` | Left out when there is no message, or the newest is older than 3 hours |
| Last game card | WIN or LOSS tag, hero, kills/deaths/assists, length and how long ago | Deadlock match history | Left out when off, empty, or the last game is older than 12 hours |
| Automation lamps | One small LED per active Claude Code session (up to six), set into the enamel between the "CHAMBER C-33/a" plate and the hazard strip: dim for standing by, lit for thinking, pulsing while a tool runs | Local activity feed (see below) | No lamps at all when the feed is unreachable, silent for 30 s, or lists no session |
| Automation card | One session per appearance: its project name (or "Classified"), what it is doing ("Editing stage.html", "Running tests"), its tool-call count and either its token count or how many agents it has out. Working sessions take turns, tool-running ones first; with more than one session a head count follows ("4 processes, 3 busy") | Local activity feed | Left out of the rotation, and taken down at once if it is on screen when the feed goes away |
| Log card | A test-chamber flavor line with small print | None | Added to the rotation whenever fewer than two real cards exist, so the card is never empty |

Cards rotate every 8 s in a fixed order (now playing, chat, last game, automation). A new chat line or a new track interrupts the rotation and shows for 10 s with a short tag flash. The first real data after load replaces the flavor card right away. Chat text is always set with `textContent`, stripped of control and bidirectional characters, collapsed to one paragraph and truncated.

The webcam frame carries the recording timecode (counts from when the source loads) and the anti-mass spectrometer: a power meter that spools to 105% over about 100 s, runs hot for 16 s (warn lamp, hot segments, "We can't shut it down"), then resets. That is the theme's one alarm moment.

## Data: `API_BASE` and CORS

All settings are constants at the top of the script in `stage.html`.

| Constant | Default | Meaning |
|---|---|---|
| `API_BASE` | `"https://n8than.dev"` | Origin for the three n8than.dev endpoints. Use `""` if the page is ever served from n8than.dev itself (same origin, no CORS needed). |
| `STEAM_ACCOUNT_ID` | `""` | Deadlock account. Empty turns every Deadlock piece off. |
| `DEADLOCK_API` | `"https://api.deadlock-api.com"` | Community Deadlock API. |
| `EVERY` | status 30 s, chat 15 s, now playing 30 s, match history 7 min | Poll intervals. Never lower them. |

Every request is a plain GET with no custom headers and no credentials, so there is no preflight. A failed request is silent: two failures in a row drop that piece and the widget falls back as in the table above. Nothing ever shows an error or an empty box.

**Cross-origin.** OBS serves a local file from its own origin, so the three n8than.dev endpoints (`/api/live/status`, `/api/live/chat`, `/api/spotify/now-playing`) answer `GET` with `Access-Control-Allow-Origin: *` (`deploy/Caddyfile`, since 2026-09-30; before that the console could only show its idle face). The header is on GET only: `/api/live/chat` still refuses POSTs from other origins. `api.deadlock-api.com` sends the same header itself.

## Claude Code activity feed

The lamps and the automation card read `http://127.0.0.1:47801/agents.json`, served by `../../agentfeed/agentfeed.py` on the streamer's machine (constant `AGENT_FEED`, polled every 4 s; it is a local daemon, so the "never lower" rule for the public APIs does not apply to it). The feed is metadata only: a project name for allowlisted folders and "Classified" for everything else, a phrase from a fixed vocabulary, and counters. Its privacy rules and schema are in `../../agentfeed/README.md`. The page treats the text as untrusted anyway: `textContent`, control and bidirectional characters stripped, alias cut to 16 characters and action to 27. The daemon answers with `Access-Control-Allow-Origin: *`, so the cross-origin caveat above does not apply to it.

The lamps sit inside the console (canvas x 1790 to 1840 for six lamps, y 18 to 23, plus a 4 px glow), so the footprint is unchanged: re-measured on magenta 2026-09-30 with four lamps lit, the page still paints only x 1603 to 1908, y 11 to 162.

## Deadlock data

No Valve game state integration or public match API for Deadlock turned up in research (2026-09-29), so the overlay reads match history from deadlock-api.com (community run, not endorsed by Valve). It is keyed to one Steam account.

- **What the streamer must supply:** the Steam account ID, passed as `?steam=` on the OBS browser source URL (so it stays out of this public repo; set in the local scene collection), or pasted into `STEAM_ACCOUNT_ID`, which the parameter overrides. Either the SteamID3 number (the N in `[U:1:N]`, also shown as "account ID") or the 17-digit SteamID64 works; SteamID64 is converted by subtracting 76561197960265728.
- **Endpoints used:** `GET /v1/players/{account_id}/match-history` (newest game first) and, once, `GET /v1/assets/heroes` for hero names (falls back to "Hero 7" if unreachable).
- **Session record:** games whose `start_time` is after the broadcast start, using `player_match_outcome` (1 win, 2 loss; anything else is not counted). If the broadcast start is unknown it uses local midnight.
- **Freshness:** for an account that is friends with one of deadlock-api's Steam bots, the history merges live Steam data. For any other account it is stored history only, which can lag behind the game. That is why the card says "Last game" and the overlay does not claim to be live. The API also limits bot-friend accounts to 10 requests per hour per IP, so the overlay polls every 7 minutes; a 429 answer still carries the stored history and is used.

## Preview with fake data

Add `?mock=1` to the page URL. All five sources then return realistic fake data (a 2 hour 12 minute broadcast, 3 viewers, a chat line that is long enough to clip, a track, six games with a mixed record, four Claude Code sessions whose actions change every 8 s) and the Deadlock pieces are on. Optional `&off=` takes a comma list of `status`, `chat`, `music`, `match`, `deadlock` or `agents` to see each fallback (`off=status` shows the idle face, `off=deadlock` shows the clock tile). Without `mock`, a browser that blocks the cross-origin calls shows the idle state.

To preview inside OBS, untick Local file and put the query on the URL instead: `file:///C:/.../black-mesa/stage.html?mock=1` (not tested in OBS itself; the browser-tab preview is what was verified).

## Clearance from Deadlock's HUD

Checked against three clean reference frames at 1920x1080. The tower sits right of the hero and score row, which ends at about x 1592 (the last enemy portrait and its alert mark), and above the minimap, which starts at about y 640. It avoids the compass (top-left, x up to about 85), the kill feed (left, from y about 215), pickup popups (left, y 590 to 690), the health and souls cluster and item grid (bottom-left), the ability bar (bottom-center) and the match and server text (bottom-right corner). The left and top-center of the canvas are untouched. The only other HUD-free band on the screen is the top-left corner (x 96 to 326, y 12 to 196), which is too small for a webcam.

`prefers-reduced-motion` stops the blinks, the lamp pulse, the card fade and the spool (the meter holds at 100%).
