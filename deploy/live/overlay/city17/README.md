# Stream overlay: City 17 / Overwatch (WARDOGS)

The theme of the OBS scene **WARDOGS**. OBS's automatic scene switcher picks that scene when the WARDOGS window has focus; Deadlock gets the Black Mesa theme in `../black-mesa/`. Pages are OBS Browser Sources (local file) on a 1920x1080 canvas: self-contained, inline CSS and JS, system fonts only, transparent background.

## Placement (WARDOGS scene)

| Page | Size (w x h) | Canvas position (x, y) | Shown |
|---|---|---|---|
| `stage.html` | 1920 x 1080 | 0, 0 | Always (the incident log draws at 24, 8, 512 x 76) |
| `webcam-frame.html` | 512 x 340 page, shown at 75% (384 x 255) | 304, 815 | Webcam on |
| Webcam source | 336 x 189 | 328, 848 | Webcam on, **below** the frame in the source list |
| `mic-badge.html` | 512 x 48 | not placed | Retired 2026-09-29 (the mic stays live); kept for reuse |

Webcam hole in page coordinates: (32, 44), 448 x 252, 16:9. At 75% that is the 336 x 189 webcam box above.

The layout avoids WARDOGS' HUD at 1080p: money top-right, compass top-center, in-game chat top-left from about y 30 when it is open, killfeed on the left from y ~495, body diagram, damage log and squad list down the right, minimap and faction scores in the bottom-left corner (to about x 290). The webcam sits on the bottom edge directly right of the minimap (moved there 2026-09-30 from the top-left, checked against a live match). The log overlaps the game's menu tabs while in menus; in a match the band it covers is empty.

## Marks

Every mark is inline SVG drawn for this overlay after Half-Life 2's Combine iconography (fan art; no file from the game or a wiki is used). No asset files.

| Mark | Where |
|---|---|
| Combine claw | Log header, in place of a status dot (blinks while the feed is live); webcam frame, left of the name |
| City 17 ring | Faint watermark behind the right end of the log |
| Overwatch Elite sigil (one orange eye in place of the skull) | Webcam frame, bottom-right (replaced the lambda 2026-09-30) |
| CMB wordmark | Webcam frame footer |
| Breencast screen | Webcam frame header, beside the "BREENCAST" label and timecode |
| Spark | Log header, beside the Claude Code session ticks; hidden with them |

## Incident log

`stage.html` polls `http://127.0.0.1:47800/wardogs.json` every 3 s: the live session feed served by `wardogs-ocr/live.py` on the streamer's machine (OCR of OBS screenshots of the WARDOGS capture; it never touches the game process, which runs the Elytra anti-cheat). It shows session kills and deaths as tallies, net cash, the match number in the header ("MATCH 02"), and the latest incidents. Every other turn of the bottom line carries session context instead: `SECTOR` (which faction leads and by how much, and whether the control zone is contested; left out until a score is on the board) and `LEDGER` (balance, plus the game's own profit or loss figure for the deployment). When the feed is down or idle it falls back to dispatch flavor lines.

## Viewer count

The eye and number in the log header are `readers.length` from `https://n8than.dev/api/live/status`, polled every 30 s (a public endpoint: never lower it). They are hidden whenever the stream is not online or the request fails twice. `?mock=1` previews scripted data (placeholder names only). Feed text is set with `textContent` and clipped.

## Unit telemetry (Claude Code activity)

`stage.html` also polls `http://127.0.0.1:47801/agents.json` every 3 s: the activity feed served by `../../agentfeed/agentfeed.py` (metadata only; privacy rules and schema in `../../agentfeed/README.md`). It adds two things inside the incident log panel, so the 512 x 76 footprint at (24, 8) is unchanged (re-measured on magenta 2026-09-30):

| Piece | Shows | When the feed is down or lists no session |
|---|---|---|
| Ticks beside the spark | One 3 x 9 px tick per active session, up to eight: dim for standing by, lit for thinking, pulsing while a tool runs | No spark and no ticks |
| `UNITS` line | Every fourth turn of the bottom line (it takes precedence over the context lines), in both the live and the dispatch face: one session by project name or "Classified" and what it is doing ("n8than.dev: Editing stage.html"), working sessions in turn with tool-running ones first, then a head count ("4 units online, 2 agents dispatched"). A new incident still interrupts and holds as before | The line leaves the rotation, and is replaced at once if it is on screen |

Two failed polls in a row count as down, the same rule as the WARDOGS feed; the two feeds fail independently. `?mock=1` scripts four sessions whose actions change every 9 s. Feed text is set with `textContent`, stripped of control and bidirectional characters, and clipped (alias 16 characters, action 30).

## OBS Browser Source settings

| Page | Width | Height | FPS |
|---|---|---|---|
| `stage.html` | 1920 | 1080 | 30 |
| `webcam-frame.html` | 512 | 340 | 30 |

Tick **Local file**. Motion is transform/opacity only; `prefers-reduced-motion` stops blinks, tick pulses and sweeps.
