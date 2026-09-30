# Stream overlay: City 17 / Overwatch (WARDOGS)

The theme of the OBS scene **WARDOGS**. OBS's automatic scene switcher picks that scene when the WARDOGS window has focus; Deadlock gets the Black Mesa theme in `../black-mesa/`. Pages are OBS Browser Sources (local file) on a 1920x1080 canvas: self-contained, inline CSS and JS, system fonts only, transparent background.

## Placement (WARDOGS scene)

| Page | Size (w x h) | Canvas position (x, y) | Shown |
|---|---|---|---|
| `stage.html` | 1920 x 1080 | 0, 0 | Always (the incident log draws at 24, 8, 512 x 76) |
| `webcam-frame.html` | 512 x 340 | 24, 90 | Webcam on |
| `mic-badge.html` | 512 x 48 | not placed | Retired 2026-09-29 (the mic stays live); kept for reuse |

Webcam hole: page (32, 44), canvas (56, 134), 448 x 252, 16:9. Place the webcam source there, **below** the frame in the source list.

The layout avoids WARDOGS' HUD at 1080p: money and rewards top-right, compass top-center (to about x 662), killfeed on the left from y ~495, body diagram, damage log and squad list down the right, minimap and faction scores bottom-left. The top-left band above the killfeed is the free space, so the log and webcam stack there.

## Incident log

`stage.html` polls `http://127.0.0.1:47800/wardogs.json` every 3 s: the live session feed served by `wardogs-ocr/live.py` on the streamer's machine (OCR of OBS screenshots of the WARDOGS capture; it never touches the game process, which runs the Elytra anti-cheat). It shows session kills and deaths as tallies, net cash, and the latest incidents. When the feed is down or idle it falls back to dispatch flavor lines. `?mock=1` previews scripted data (placeholder names only). Feed text is set with `textContent` and clipped.

## OBS Browser Source settings

| Page | Width | Height | FPS |
|---|---|---|---|
| `stage.html` | 1920 | 1080 | 30 |
| `webcam-frame.html` | 512 | 340 | 30 |

Tick **Local file**. Motion is transform/opacity only; `prefers-reduced-motion` stops blinks and sweeps.
