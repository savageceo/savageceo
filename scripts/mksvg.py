# Font: MBF Royal from SAVAGE-SUITE/SAVAGE-SKIN src/fonts/ (not committed here: not redistributable).
# Run: uv run --with fonttools python -I scripts/mksvg.py <MBF-Royal.otf> assets hero "TITLE" "TAGLINE" [motif]
"""Outline MBF Royal lettering into paths-only SVGs on the house champagne foil.

No font binary ships: every glyph is converted to a <path>, so the SVGs are
artwork, render identically through GitHub's camo proxy, and need no @font-face.
Every org shares the foil, the face and the diamond; each gets its own motif.

  python -I mksvg.py <font.otf> <outdir> hero "SAVAGE CEO" "BUILD · SHIP · COLLECT · REPEAT" [motif] [file]
  python -I mksvg.py <font.otf> <outdir> name "THE ARCHITECT" [file]
  python -I mksvg.py <font.otf> <outdir> tile "GOALPOST" [file]
  python -I mksvg.py <font.otf> <outdir> rule

Motifs: classic · viewfinder · marquee · blueprint · skyline · dropcut · letterhead · terminal
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# shipped @savage-suite/skin tokens (src/styles/tokens.css)
OBSIDIAN = "#0a0a0a"
CHAMPAGNE = "#c9a962"
GOLD = "#d4af37"
BRASS = "#b5956b"
MONO = "font-family=\"ui-monospace, 'SF Mono', Menlo, monospace\""

# --gradient-gold: linear-gradient(135deg, champagne 0%, gold 50%, brass 100%)
FOIL = (
    '<linearGradient id="foil" x1="0" y1="0" x2="1" y2="1">'
    f'<stop offset="0" stop-color="{CHAMPAGNE}"/>'
    f'<stop offset="0.5" stop-color="{GOLD}"/>'
    f'<stop offset="1" stop-color="{BRASS}"/>'
    "</linearGradient>"
)
FADE = (
    '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
    f'<stop offset="0" stop-color="{CHAMPAGNE}" stop-opacity="0"/>'
    f'<stop offset="0.5" stop-color="{CHAMPAGNE}" stop-opacity="0.9"/>'
    f'<stop offset="1" stop-color="{CHAMPAGNE}" stop-opacity="0"/>'
    "</linearGradient>"
)
GLOW = (
    '<filter id="glow" x="-6%" y="-40%" width="112%" height="180%">'
    f'<feDropShadow dx="0" dy="0" stdDeviation="1.6" flood-color="{CHAMPAGNE}" flood-opacity="0.3"/>'
    "</filter>"
)


def outline(font, text, size, tracking):
    """Return (path d, advance width) for text set at size, baseline y=0, x from 0."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(gs)
    x = 0.0
    chars = list(text)
    for i, ch in enumerate(chars):
        name = cmap.get(ord(ch))
        if name is None:
            raise SystemExit(f"glyph missing for {ch!r}")
        g = gs[name]
        g.draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
        x += g.width * scale
        if i < len(chars) - 1:
            x += tracking
    return pen.getCommands(), x


def lettering(font, text, size, tracking, cx, baseline, max_w):
    """Centered lettering; long text shrinks to max_w. Returns (svg path, width, size used)."""
    d, w = outline(font, text, size, tracking)
    if w > max_w:  # long names shrink to fit, keeping proportions
        k = max_w / w
        size, tracking = size * k, tracking * k
        d, w = outline(font, text, size, tracking)
    return f'<path transform="translate({cx - w / 2:.2f} {baseline})" d="{d}"/>', w, size


def cap_height(font, size):
    os2 = font["OS/2"]
    caps = getattr(os2, "sCapHeight", 0) or font["head"].unitsPerEm * 0.7
    return caps * size / font["head"].unitsPerEm


def diamond(cx, cy, r, attrs=f'fill="{CHAMPAGNE}"'):
    return f'<path d="M{cx} {cy - r} L{cx + r} {cy} L{cx} {cy + r} L{cx - r} {cy} Z" {attrs}/>'


def rule_at(y, half=128):
    return (
        f'<rect x="{620 - half}" y="{y - 1}" width="{half * 2}" height="1.6" fill="url(#fade)"/>'
        + diamond(620, y, 5)
    )


def tagline_at(y, tagline, x=620, anchor="middle", size=16, spacing=11):
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" {MONO} font-size="{size}" '
        f'letter-spacing="{spacing}" fill="{BRASS}">{tagline}</text>'
    )


def blink(dur="1.1s", begin="0s"):
    return (f'<animate attributeName="opacity" values="1;0;1" dur="{dur}" begin="{begin}" '
            'calcMode="discrete" repeatCount="indefinite"/>')


def pulse(dur="1.4s", begin="0s", lo="0.25"):
    return (f'<animate attributeName="opacity" values="1;{lo};1" dur="{dur}" begin="{begin}" '
            'repeatCount="indefinite"/>')


# ── motifs: same foil, same face, same diamond; a different room for every org ──

def m_classic(title_w, tagline):
    return dict(h=210, baseline=122, max_w=1160,
                front=rule_at(151) + tagline_at(190, tagline))


def m_viewfinder(title_w, tagline):
    """SAVAGE STUDIO: a camera viewfinder framing the name."""
    x0, x1, y0, y1, L = 34, 1206, 14, 216, 44
    s = f'stroke="{CHAMPAGNE}" stroke-width="2" fill="none" stroke-linecap="square"'
    corners = (
        f'<path d="M{x0} {y0 + L} V{y0} H{x0 + L}" {s}/>'
        f'<path d="M{x1 - L} {y0} H{x1} V{y0 + L}" {s}/>'
        f'<path d="M{x0} {y1 - L} V{y1} H{x0 + L}" {s}/>'
        f'<path d="M{x1 - L} {y1} H{x1} V{y1 - L}" {s}/>'
    )
    ticks = (f'<path d="M{x0} 115 H{x0 + 14} M{x1 - 14} 115 H{x1}" stroke="{CHAMPAGNE}" '
             'stroke-width="1.2" stroke-opacity="0.6"/>')
    rec = (f'<circle cx="{x1 - 34}" cy="{y0 + 22}" r="4" fill="{CHAMPAGNE}">{blink("1.6s")}</circle>'
           f'<text x="{x1 - 46}" y="{y0 + 27}" text-anchor="end" {MONO} font-size="13" '
           f'letter-spacing="4" fill="{BRASS}">REC</text>')
    return dict(h=230, baseline=126, max_w=1020,
                back=corners + ticks + rec, front=rule_at(156) + tagline_at(196, tagline))


def m_marquee(title_w, tagline):
    """SAVAGE ROSTER: a marquee — the bulbs chase around the names."""
    frame = (f'<rect x="56" y="6" width="1128" height="226" rx="12" fill="none" '
             f'stroke="{CHAMPAGNE}" stroke-opacity="0.35" stroke-width="1.2"/>')
    bulbs = []
    for row_y in (22, 216):
        for i, x in enumerate(range(86, 1160, 30)):
            bulbs.append(f'<g>{diamond(x, row_y, 4)}{pulse("1.4s", "0.7s" if i % 2 else "0s")}</g>')
    return dict(h=238, baseline=134, max_w=1000,
                back=frame + "".join(bulbs), front=rule_at(160) + tagline_at(192, tagline))


def m_blueprint(title_w, tagline):
    """SAVAGE SUITE: an engineering drawing — grid, extension lines, a dimension."""
    defs = (
        '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{CHAMPAGNE}" stroke-width="0.6"/></pattern>'
        '<radialGradient id="vign" cx="0.5" cy="0.5" r="0.6">'
        '<stop offset="0" stop-color="#fff" stop-opacity="1"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        '<mask id="vm"><rect width="1240" height="230" fill="url(#vign)"/></mask>'
    )
    a, b = 620 - title_w / 2, 620 + title_w / 2
    back = (
        '<rect width="1240" height="230" fill="url(#grid)" opacity="0.22" mask="url(#vm)"/>'
        f'<path d="M{a:.1f} 40 V168 M{b:.1f} 40 V168" stroke="{CHAMPAGNE}" stroke-width="0.8" '
        'stroke-dasharray="3 5" stroke-opacity="0.5"/>'
    )
    dim = (
        f'<path d="M{a:.1f} 156 H{b:.1f}" stroke="{CHAMPAGNE}" stroke-width="1" stroke-opacity="0.8"/>'
        f'<path d="M{a:.1f} 150 V162 M{b:.1f} 150 V162" stroke="{CHAMPAGNE}" stroke-width="1.4"/>'
        + diamond(620, 156, 5)
    )
    return dict(h=230, baseline=124, max_w=1080, defs=defs, back=back,
                front=dim + tagline_at(200, tagline))


def m_skyline(title_w, tagline):
    """SAVAGE CITY: the name over a skyline, a beacon on the tallest tower."""
    blocks = [(30, 16), (22, 28), (40, 20), (18, 40), (34, 30), (26, 48), (44, 34), (22, 58),
              (36, 38), (24, 26), (42, 46), (28, 22), (38, 34), (20, 18), (32, 26)]
    base = 198
    x = 620 - sum(w for w, _ in blocks) / 2
    d = f"M{x:.1f} {base}"
    tallest = max(range(len(blocks)), key=lambda i: blocks[i][1])
    beacon = None
    for i, (w, hgt) in enumerate(blocks):
        d += f" V{base - hgt} H{x + w:.1f}"
        if i == tallest:
            beacon = (x + w / 2, base - hgt)
        x += w
    d += f" V{base}"
    bx, by = beacon
    city = (
        '<rect x="300" y="197.2" width="640" height="1.6" fill="url(#fade)"/>'
        f'<path d="{d}" fill="none" stroke="{CHAMPAGNE}" stroke-width="1.3" stroke-linejoin="miter"/>'
        f'<path d="M{bx:.1f} {by} V{by - 12}" stroke="{CHAMPAGNE}" stroke-width="1.3"/>'
        f'<g>{diamond(round(bx, 1), by - 18, 5)}{pulse("2s", "0s", "0.3")}</g>'
    )
    return dict(h=250, baseline=110, max_w=1160, front=city + tagline_at(236, tagline))


def m_dropcut(title_w, tagline):
    """SAVAGE x BUNNY: chrome-cut slashes, the tagline as a drop label."""
    cuts = ""
    for i, sw in enumerate((3.2, 2, 1)):
        off = i * 18
        cuts += (f'<path d="M{70 + off} 186 L{126 + off} 24" stroke="url(#foil)" stroke-width="{sw}"/>'
                 f'<path d="M{1170 - off} 24 L{1114 - off} 186" stroke="url(#foil)" stroke-width="{sw}"/>')
    return dict(h=210, baseline=122, max_w=940,
                back=cuts, front=rule_at(151) + tagline_at(190, f"// {tagline} //"))


def m_letterhead(title_w, tagline):
    """SAVAGE CLIENTS: a letterhead — double rules, sealed at the centre."""
    def double(y):
        return (f'<rect x="80" y="{y}" width="1080" height="1.4" fill="url(#fade)"/>'
                f'<rect x="80" y="{y + 5}" width="1080" height="0.8" fill="url(#fade)"/>'
                + diamond(620, y + 3, 6, f'fill="{OBSIDIAN}" stroke="{CHAMPAGNE}" stroke-width="1.2"'))
    return dict(h=230, baseline=128, max_w=1040,
                back=double(14) + double(208), front=tagline_at(180, tagline))


def m_terminal(title_w, tagline):
    """GHOST CROWN: built in the dark — a terminal window, the cursor still blinking."""
    win = (
        f'<rect x="6" y="6" width="1228" height="252" rx="14" fill="{OBSIDIAN}" '
        f'stroke="{CHAMPAGNE}" stroke-opacity="0.45" stroke-width="1.2"/>'
        f'<path d="M6 44 H1234" stroke="{CHAMPAGNE}" stroke-opacity="0.25"/>'
        + "".join(f'<circle cx="{30 + 20 * i}" cy="25" r="5.5" fill="{CHAMPAGNE}" fill-opacity="{o}"/>'
                  for i, o in enumerate((0.9, 0.55, 0.3)))
        + f'<text x="620" y="30" text-anchor="middle" {MONO} font-size="13" letter-spacing="3" '
        f'fill="{BRASS}" fill-opacity="0.8">ghost@crown: ~/kingdom</text>'
    )
    prompt = (
        f'<text x="48" y="226" {MONO} font-size="17" letter-spacing="5" fill="{BRASS}">'
        f'<tspan fill="{CHAMPAGNE}">$ </tspan>{tagline.lower()} '
        f'<tspan fill="{CHAMPAGNE}">█{blink()}</tspan></text>'
    )
    return dict(h=264, baseline=158, max_w=1040, back=win, front=prompt)


MOTIFS = {f.__name__[2:]: f for f in (m_classic, m_viewfinder, m_marquee, m_blueprint,
                                       m_skyline, m_dropcut, m_letterhead, m_terminal)}


def hero(font, title, tagline, motif="classic"):
    probe = MOTIFS[motif](0, tagline)
    word, w, _ = lettering(font, title, 104, 8, 620, probe["baseline"], probe["max_w"])
    m = MOTIFS[motif](w, tagline)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 {m["h"]}" role="img" '
        f'aria-label="{title} — {tagline}">'
        f'<defs>{FOIL}{FADE}{GLOW}{m.get("defs", "")}</defs>'
        f'{m.get("back", "")}'
        f'<g fill="url(#foil)" stroke="{OBSIDIAN}" stroke-width="0.9" paint-order="stroke" '
        f'filter="url(#glow)">{word}</g>'
        f'{m.get("front", "")}'
        "</svg>\n"
    )


def name(font, text):
    d, w = outline(font, text, 56, 14)
    vw = int(w + 80)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} 96" role="img" aria-label="{text}">'
        f"<defs>{FOIL}</defs>"
        f'<path transform="translate({(vw - w) / 2:.2f} 66)" d="{d}" fill="url(#foil)" '
        f'stroke="{OBSIDIAN}" stroke-width="0.6" paint-order="stroke"/>'
        "</svg>\n"
    )


def tile(font, text):
    """A build's logo slot until its real logo lands: the name set in the house face."""
    W, H, MAXW, SIZE, TRACK = 300, 180, 236, 46, 5
    lines = [text]
    d, w = outline(font, text, SIZE, TRACK)
    words = text.split()
    if w > MAXW * 1.25 and len(words) > 1:  # too long for one line: break at the best space
        best = min(range(1, len(words)),
                   key=lambda i: max(outline(font, " ".join(words[:i]), SIZE, TRACK)[1],
                                     outline(font, " ".join(words[i:]), SIZE, TRACK)[1]))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    widest = max(outline(font, ln, SIZE, TRACK)[1] for ln in lines)
    k = min(1.0, MAXW / widest)
    size, track = SIZE * k, TRACK * k
    cap = cap_height(font, size)
    gap = cap * 0.55
    block = cap * len(lines) + gap * (len(lines) - 1)
    top = (H - 18) / 2 - block / 2
    paths = ""
    for i, ln in enumerate(lines):
        p, _, _ = lettering(font, ln, size, track, W / 2, round(top + cap * (i + 1) + gap * i, 2), MAXW)
        paths += p
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{text}">'
        f"<defs>{FOIL}{FADE}</defs>"
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="{OBSIDIAN}" '
        f'stroke="{CHAMPAGNE}" stroke-opacity="0.45" stroke-width="1.2"/>'
        f'<rect x="9" y="9" width="{W - 18}" height="{H - 18}" rx="10" fill="none" '
        f'stroke="{CHAMPAGNE}" stroke-opacity="0.14"/>'
        f'<g fill="url(#foil)">{paths}</g>'
        f'<rect x="{W / 2 - 44}" y="{H - 31}" width="88" height="1.2" fill="url(#fade)"/>'
        + diamond(W / 2, H - 30.4, 3.5)
        + "</svg>\n"
    )


def rule():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 16" role="presentation">'
        f"<defs>{FADE}</defs>"
        '<rect x="0" y="7" width="1000" height="1.5" fill="url(#fade)"/>'
        f'<path d="M500 2.5 L508 8 L500 13.5 L492 8 Z" fill="{CHAMPAGNE}"/>'
        "</svg>\n"
    )


def slug(text):
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


if __name__ == "__main__":
    font = TTFont(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    kind = sys.argv[3]
    if kind == "hero":
        title, tagline = sys.argv[4], sys.argv[5]
        motif = sys.argv[6] if len(sys.argv) > 6 else "classic"
        f = sys.argv[7] if len(sys.argv) > 7 else f"hero-{slug(title)}.svg"
        svg = hero(font, title, tagline.replace("·", "&#183;"), motif)
    elif kind == "name":
        text = sys.argv[4]
        f = sys.argv[5] if len(sys.argv) > 5 else f"name-{slug(text)}.svg"
        svg = name(font, text)
    elif kind == "tile":
        text = sys.argv[4]
        f = sys.argv[5] if len(sys.argv) > 5 else f"{slug(text)}.svg"
        svg = tile(font, text)
    elif kind == "rule":
        f, svg = "rule.svg", rule()
    (out / f).parent.mkdir(parents=True, exist_ok=True)
    (out / f).write_text(svg)
    print(out / f)
