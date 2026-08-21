# assets

Runtime assets for the Rust app.

- `DejaVuSans.ttf` (optional, not committed) — drop a DejaVu Sans (or Noto Sans)
  TTF here to get full Portuguese accents (`ç ã á`) and nicer glyphs. If the
  file is absent the app falls back to macroquad's built-in font, so it still
  runs. Phase 6 bundles a font directly via `include_bytes!` so no external file
  is needed.
