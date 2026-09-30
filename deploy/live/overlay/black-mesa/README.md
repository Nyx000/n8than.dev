# Stream overlay: Black Mesa / Test Chamber C-33/a

Two OBS Browser Sources (local file) on a 1920x1080 canvas. The theme is the Anomalous Materials test chamber control room: beige lab-console enamel, black CRT glass with amber phosphor readouts, hazard striping, and the HEV suit's amber numerals as the HUD layer. Each page is self-contained: inline CSS and JS, system fonts only (Bahnschrift, Consolas, Segoe UI fallback), no network requests, transparent background. It replaces the City 17 theme one folder up (same geometry, so OBS placement is unchanged); the mic badge is dropped.

## Placement

| Page | Size (w x h) | Canvas position (x, y) | Shown |
|---|---|---|---|
| `stage.html` | 1920 x 1080 | 0, 0 | Always |
| `webcam-frame.html` | 512 x 340 | 1392, 168 | Webcam on |

## Webcam hole (16:9, fully transparent)

| Coordinates | x | y | w | h |
|---|---|---|---|---|
| Page (`webcam-frame.html`) | 32 | 44 | 448 | 252 |
| Canvas | 1424 | 212 | 448 | 252 |

Place the webcam source at 1424, 212 sized 448 x 252, **below** `webcam-frame.html` in the source list. The frame is one element clipped with an even-odd `clip-path` that cuts the hole out, so no background, glow or scanline can paint into it. Verified pixel-exact against a magenta background: 0 of 112,896 hole pixels painted, and the console glass starts on the adjacent pixel.

## OBS Browser Source settings

| Page | Width | Height | FPS |
|---|---|---|---|
| `stage.html` | 1920 | 1080 | 30 |
| `webcam-frame.html` | 512 | 340 | 30 |

Tick **Local file**. The default Custom CSS is harmless and can stay. 30 fps is plenty: all motion is blinks, a typed status line, a sliding caret and a stepped power meter, on opacity/transform or a once-a-second text update.

## Layout notes

- Everything sits clear of Deadlock's HUD: the hero/score row (x 330 to 1590, y 0 to 150), the compass (top-left, x up to about 80), the kill feed (left, from y 200), stats and items (bottom-left), abilities (bottom-center) and the minimap (bottom-right, from y 640).
- Stage footprint, measured on a magenta background: chamber status console x 100 to 320, HEV readout x 1620 to 1904, both y 14 to 67. Nothing else, nothing near center.
- Webcam occupies the right column x 1392 to 1904, y 168 to 508, between the hero row and the minimap.
- The status console types a new line every 8 s. The webcam's PWR meter spools the anti-mass spectrometer to 105% over about 100 s, then runs hot for 16 s (warn lamp, hot segments, "We can't shut it down"), then resets. That is the theme's one alarm moment.
- The REC timecode and the power cycle count from when the source loads. Leave "Shutdown source when not visible" off if they should keep running while the webcam is hidden.
- `prefers-reduced-motion` stops the blinks, the typing, the caret and the spool (the meter holds at 100%).
