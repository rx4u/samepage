# samepage brand

The mark is "Chunky Cursor": an equals sign built from short, fat rounded bars, where the bottom bar breaks into a short bar and a square block cursor. It reads as "same" and as a developer tool.

| File | Use |
|---|---|
| `samepage-mark.svg`, `samepage-mark-white.svg` | Freestanding mark: black on light, white on dark |
| `samepage-tile.svg` | App tile: #0a0a0a tile, white mark at 72% of the tile, corner radius 22% |
| `samepage-tile-16.svg`, `favicon-16.png` | Pixel-snapped 16 px tile with 1 px gaps (the master's gaps close up at 16 px) |
| `favicon-32.png`, `favicon-64.png` | Tile favicons |
| `samepage-1024.png` | 1024 x 1024 tile with transparent corners (also `.claude-plugin/icon.png`) |
| `samepage-lockup.svg`, `samepage-lockup-white.svg` | Mark plus the wordmark in Inter Tight 600, outlined |
| `preview.png` | GitHub light and dark previews |

## Geometry (viewBox 0 0 100 100, fills only)

- Top bar: pill, x 26 to 74, y 26 to 46, r 10
- Bottom bar: pill, x 26 to 50, y 54 to 74, r 10
- Cursor: rect, x 58 to 74, y 54 to 74, radius 3
- Gaps: 8 units vertical, 8 units between bottom bar and cursor

## Rules

- Black and white only for now. Never amber, gold, orange, yellow or teal.
- No gradients, glows, shadows, 3D or textures.
- Use the 16 px tile at 16 px; scale the master everywhere else.
