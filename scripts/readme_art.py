"""Generate the README graphics in docs/readme/ (light and dark). Black and white only (docs/brand/README.md).

Run: python3 scripts/readme_art.py docs/readme
"""
import math
import os
import sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": dict(bg="#fafafa", card="#ffffff", line="#e5e5e5", line2="#d4d4d4", fg="#0a0a0a", fg2="#525252",
                  fg3="#a3a3a3", dot="#e5e5e5", tile="#0a0a0a", mark="#ffffff", tileline="#0a0a0a"),
    "dark": dict(bg="#0a0a0a", card="#141414", line="#262626", line2="#333333", fg="#fafafa", fg2="#a3a3a3",
                 fg3="#5c5c5c", dot="#1f1f1f", tile="#fafafa", mark="#0a0a0a", tileline="#fafafa"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mark(x, y, size, fill):
    s = size / 100.0
    return ('<g transform="translate(%.1f %.1f) scale(%.4f)"><path d="M36 26 H64 A10 10 0 0 1 64 46 H36 A10 10 0 0 1 36 26 Z" fill="%s"/>'
            '<path d="M36 54 H40 A10 10 0 0 1 40 74 H36 A10 10 0 0 1 36 54 Z" fill="%s"/>'
            '<rect x="58" y="54" width="16" height="20" rx="3" fill="%s"/></g>' % (x, y, s, fill, fill, fill))


def tile(cx, cy, size, t):
    r = size * 0.22
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"/>' % (cx - size / 2, cy - size / 2, size, size, r, t["tile"])
            + mark(cx - size / 2 + size * 0.14 - size * 0.72 * 0.26 + size * 0.72 * 0.12, cy - size / 2 + size * 0.14 - size * 0.72 * 0.26 + size * 0.72 * 0.12, size * 0.72 * 1.0 / 0.72 * 0.72 / 0.48 * 0.48, t["mark"]))


def tile2(cx, cy, size, t):
    # mark glyph spans 26..74 (48 units) of its 100 box; fit glyph to 50% of tile, centred
    r = size * 0.22
    glyph = size * 0.5
    scale = glyph / 48.0
    ox = cx - 50 * scale
    oy = cy - 50 * scale
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"/>' % (cx - size / 2, cy - size / 2, size, size, r, t["tile"])
            + mark(ox, oy, 100 * scale, t["mark"]))


def dots(w, h, t, step=24):
    return ('<defs><pattern id="d" width="%d" height="%d" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.5" fill="%s"/></pattern></defs>'
            '<rect width="%d" height="%d" fill="url(#d)"/>' % (step, step, t["dot"], w, h))


def frame(w, h, t, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
            '<rect width="%d" height="%d" rx="28" fill="%s"/>'
            '<g clip-path="url(#c)"><clipPath id="c"><rect width="%d" height="%d" rx="28"/></clipPath>%s</g>'
            '<rect x="0.5" y="0.5" width="%d" height="%d" rx="27.5" fill="none" stroke="%s"/>%s</svg>\n'
            % (w, h, w, h, w, h, t["bg"], w, h, dots(w, h, t), w - 1, h - 1, t["line"], body))


def text(x, y, s, size, fill, weight=400, anchor="start", family=SANS, ls=0):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" font-weight="%d" fill="%s" text-anchor="%s" letter-spacing="%s">%s</text>'
            % (x, y, family, size, weight, fill, anchor, ls, esc(s)))


def chip(cx, cy, label, t, size=25):
    w = len(label) * size * 0.54 + 72
    h = 58
    left = cx - w / 2
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" rx="29" fill="%s" stroke="%s"/>' % (left, cy - h / 2, w, h, t["card"], t["line2"])
            + '<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (left + 26, cy, t["fg"])
            + text(left + 44, cy + 9, label, size, t["fg"], 500))


TOOLS = ["Claude Code", "claude.ai", "Cowork", "Claude Desktop", "Claude Design",
         "Codex", "Gemini CLI", "Copilot", "Cursor", "Windsurf"]


def hero(t):
    w, h = 1600, 900
    cx, cy = 800, 590
    body = []
    body.append(text(cx, 150, "Every AI tool.", 96, t["fg"], 650, "middle", ls=-2))
    body.append(text(cx, 256, "On the same page.", 96, t["fg3"], 650, "middle", ls=-2))
    body.append(text(cx, 326, "One shared working context in a private repo you own.", 32, t["fg2"], 400, "middle"))
    rx, ry = 580, 196
    pts = []
    for i, name in enumerate(TOOLS):
        a = math.pi + i * 2 * math.pi / len(TOOLS) + math.pi / len(TOOLS)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), name))
    body.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-dasharray="2 8" stroke-linecap="round"/>' % (cx, cy, rx, ry, t["line2"]))
    body.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s"/>' % (cx, cy, 300, 84, t["line"]))
    for x, y, _ in pts:
        body.append('<line x1="%.1f" y1="%.1f" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"/>' % (x, y, cx, cy, t["line2"]))
    body.append('<rect x="%d" y="%d" width="%d" height="%d" rx="44" fill="%s" stroke="%s"/>' % (cx - 100, cy - 100, 200, 200, t["bg"], t["line"]))
    body.append(tile2(cx, cy - 12, 112, t))
    body.append(text(cx, cy + 78, "your store", 21, t["fg2"], 500, "middle", MONO, 1))
    for x, y, name in pts:
        body.append(chip(x, y, name, t))
    return frame(w, h, t, "".join(body))


def wrap(lines, x, y, size, fill, lh=None, weight=400):
    lh = lh or size * 1.5
    return "".join(text(x, y + i * lh, s, size, fill, weight) for i, s in enumerate(lines))


def how(t):
    w, h = 1600, 652
    body = [text(64, 92, "HOW IT WORKS", 22, t["fg3"], 600, family=MONO, ls=3)]
    cards = [
        ("01", "Boot", ["Every session starts", "from one small file", "of your context."]),
        ("02", "Write", ["The tool drafts a", "typed entry. You say", "yes. It's a commit."]),
        ("03", "Hand off", ["Leave a brief in one", "tool. The next tool", "picks it up."]),
    ]
    cw, ch, gap, top = 448, 456, 40, 132
    for i, (num, title, lines) in enumerate(cards):
        x = 64 + i * (cw + gap)
        body.append('<rect x="%d" y="%d" width="%d" height="%d" rx="22" fill="%s" stroke="%s"/>' % (x, top, cw, ch, t["card"], t["line"]))
        body.append('<rect x="%d" y="%d" width="%d" height="%d" rx="14" fill="%s" stroke="%s"/>' % (x + 24, top + 24, cw - 48, 168, t["bg"], t["line"]))
        body.append(text(x + 44, top + 62, num, 20, t["fg3"], 600, family=MONO, ls=2))
        ix, iy = x + 24, top + 24
        if i == 0:
            for k in range(3):
                ox, oy = ix + 150 + k * 16, iy + 40 - k * 10
                body.append('<rect x="%d" y="%d" width="120" height="104" rx="10" fill="%s" stroke="%s"/>' % (ox, oy + 20, t["card"], t["line2"]))
            fx, fy = ix + 182, iy + 40
            for j, ww in enumerate((70, 88, 56, 80)):
                body.append('<rect x="%d" y="%d" width="%d" height="6" rx="3" fill="%s"/>' % (fx + 12, fy + 34 + j * 16, ww, t["fg"] if j == 0 else t["line2"]))
            body.append(text(fx + 12, fy + 22, "boot.md", 14, t["fg3"], 500, family=MONO))
        elif i == 1:
            ex, ey = ix + 90, iy + 36
            body.append('<rect x="%d" y="%d" width="220" height="96" rx="10" fill="%s" stroke="%s"/>' % (ex, ey, t["card"], t["line2"]))
            body.append(text(ex + 18, ey + 34, "kind: ship", 18, t["fg"], 600, family=MONO))
            body.append(text(ex + 18, ey + 62, "tool: codex", 18, t["fg2"], 400, family=MONO))
            body.append('<circle cx="%d" cy="%d" r="22" fill="%s"/>' % (ex + 220, ey + 96, t["fg"]))
            body.append('<path d="M%d %d l7 7 l13 -14" fill="none" stroke="%s" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>' % (ex + 209, ey + 96, t["bg"]))
        else:
            ax, ay, bx = ix + 70, iy + 84, ix + 330
            body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" stroke-dasharray="4 7" stroke-linecap="round"/>' % (ax + 40, ay, bx - 40, ay, t["fg3"]))
            body.append('<path d="M%d %d l-10 -7 v14 z" fill="%s"/>' % (bx - 38, ay, t["fg3"]))
            for px, lab in ((ax, "chat"), (bx, "code")):
                body.append('<rect x="%d" y="%d" width="80" height="80" rx="20" fill="%s" stroke="%s"/>' % (px - 40, ay - 40, t["card"], t["line2"]))
                body.append(text(px, ay + 7, lab, 20, t["fg"], 500, "middle", MONO))
            body.append('<rect x="%d" y="%d" width="90" height="36" rx="9" fill="%s"/>' % ((ax + bx) / 2 - 45, ay - 52, t["fg"]))
            body.append(text((ax + bx) / 2, ay - 28, "brief", 18, t["bg"], 600, "middle", MONO))
        body.append(text(x + 32, top + 258, title, 40, t["fg"], 650))
        body.append(wrap(lines, x + 32, top + 316, 29, t["fg2"], 42))
        if i < 2:
            mx = x + cw + gap / 2
            body.append('<circle cx="%d" cy="%d" r="15" fill="%s" stroke="%s"/>' % (mx, top + ch / 2, t["bg"], t["line2"]))
            body.append('<path d="M%d %d l6 6 l-6 6" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="translate(-2 -6)"/>' % (mx - 1, top + ch / 2, t["fg"]))
    return frame(w, h, t, "".join(body))


def sync(t):
    w, h = 1600, 680
    body = [text(64, 92, "TWO ACCOUNTS, ONE PAGE", 22, t["fg3"], 600, family=MONO, ls=3)]
    stores = ((290, "work", "office"), (1310, "personal", "personal"))
    cy = 360
    for sx, name, sub in stores:
        body.append('<rect x="%d" y="%d" width="420" height="420" rx="28" fill="%s" stroke="%s"/>' % (sx - 210, cy - 210, t["card"], t["line"]))
        body.append(tile2(sx - 140, cy - 140, 76, t))
        body.append(text(sx - 86, cy - 136, name, 36, t["fg"], 650))
        body.append(text(sx - 86, cy - 104, sub + " account", 20, t["fg3"], 500, family=MONO))
        rows = [("rules", True), ("decisions", True), ("projects", False), ("ships", False), ("handoffs", False)]
        for j, (lab, crosses) in enumerate(rows):
            ry = cy - 38 + j * 50
            if crosses:
                body.append('<rect x="%d" y="%d" width="372" height="42" rx="10" fill="%s"/>' % (sx - 186, ry - 28, t["fg"]))
                body.append(text(sx - 166, ry, lab, 21, t["bg"], 600, family=MONO))
                body.append(text(sx + 166, ry, "shared", 18, t["bg"], 500, "end", MONO))
            else:
                body.append('<rect x="%d" y="%d" width="372" height="42" rx="10" fill="none" stroke="%s"/>' % (sx - 186, ry - 28, t["line2"]))
                body.append(text(sx - 166, ry, lab, 21, t["fg2"], 500, family=MONO))
                body.append(text(sx + 166, ry, "stays", 18, t["fg3"], 500, "end", MONO))
    x1, x2 = 500, 1100
    for k, (yy, d) in enumerate(((cy - 20, 1), (cy + 14, -1))):
        body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (x1 + 12, yy, x2 - 12, yy, t["fg"]))
        tip = x2 - 10 if d == 1 else x1 + 10
        body.append('<path d="M%d %d l%d -8 v16 z" fill="%s"/>' % (tip, yy, -14 * d, t["fg"]))
    body.append('<rect x="%d" y="%d" width="230" height="60" rx="30" fill="%s" stroke="%s"/>' % (800 - 115, cy - 33, t["bg"], t["line2"]))
    body.append(text(800, cy + 6, "sp sync", 26, t["fg"], 600, "middle", MONO))
    notes = ["newer edit wins", "you confirm first", "one commit per store"]
    for j, n in enumerate(notes):
        body.append(text(800, cy + 100 + j * 40, n, 26, t["fg2"], 400, "middle"))
    body.append(text(800, h - 46, "No server. No tokens. Both repos stay yours.", 22, t["fg3"], 500, "middle", MONO))
    return frame(w, h, t, "".join(body))


for name, fn in (("hero", hero), ("how", how), ("sync", sync)):
    for theme, tok in THEMES.items():
        with open(os.path.join(OUT, "%s-%s.svg" % (name, theme)), "w", encoding="utf-8") as f:
            f.write(fn(tok))
print("ok")
