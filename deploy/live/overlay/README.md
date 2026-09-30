# Stream overlay: City 17 / Overwatch

Three OBS Browser Sources (local file) on a 1920x1080 canvas. Each page is self-contained: inline CSS and JS, system fonts only (Bahnschrift, Segoe UI fallback), no network requests, transparent background. Toggle each source independently; positions are fixed so the pieces compose whether or not the others are visible.

## Placement

| Page | Size (w x h) | Canvas position (x, y) | Shown |
|---|---|---|---|
| `stage.html` | 1920 x 1080 | 0, 0 | Always |
| `webcam-frame.html` | 512 x 340 | 1392, 168 | Webcam on |
| `mic-badge.html` | 512 x 48 | 1392, 516 | Mic live |

## Webcam hole (16:9, fully transparent)

| Coordinates | x | y | w | h |
|---|---|---|---|---|
| Page (`webcam-frame.html`) | 32 | 44 | 448 | 252 |
| Canvas | 1424 | 212 | 448 | 252 |

Place the webcam source at 1424, 212 sized 448 x 252, **below** `webcam-frame.html` in the source list. Nothing is drawn inside the hole (verified pixel-exact against a solid background); the corner brackets and hairline sit outside it.

## OBS Browser Source settings

| Page | Width | Height | FPS |
|---|---|---|---|
| `stage.html` | 1920 | 1080 | 30 |
| `webcam-frame.html` | 512 | 340 | 30 |
| `mic-badge.html` | 512 | 48 | 30 |

Tick **Local file**. The default Custom CSS is harmless and can stay. 30 fps is plenty: the only motion is blinking markers, a slow slat light, a scanner caret and the mic carrier bars, all on transform/opacity.

## Layout notes

- Everything sits clear of Deadlock's HUD, measured on live frames: the hero/score row (x 330 to 1590, y 0 to 150), the compass (top-left, x up to about 80), the kill feed (left, from y 200), stats and items (bottom-left), abilities (bottom-center) and the minimap (bottom-right, from y 640).
- Stage footprint: dispatch ticker x 100 to 320, y 14 to 62; station ident x 1620 to 1904, y 14 to 66. Nothing else, nothing near center.
- Webcam and mic occupy the right column x 1392 to 1904, y 168 to 564, between the hero row and the minimap.
- The REC timecode counts from when the source loads. Leave "Shutdown source when not visible" off if it should keep running while the webcam is hidden.
- `prefers-reduced-motion` stops the blinks and sweeps.
