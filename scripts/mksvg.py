# Font: MBF Royal from SAVAGE-SUITE/SAVAGE-SKIN src/fonts/ (not committed here: not redistributable).
# Run: uv run --with fonttools python -I scripts/mksvg.py <MBF-Royal.otf> assets hero "TITLE" "TAGLINE"
"""Outline MBF Royal lettering into paths-only SVGs on the house champagne foil.

No font binary ships: every glyph is converted to a <path>, so the SVGs are
artwork, render identically through GitHub's camo proxy, and need no @font-face.

  python -I mksvg.py <font.otf> <outdir> hero "SAVAGE CEO" "BUILD · SHIP · COLLECT · REPEAT" [file]
  python -I mksvg.py <font.otf> <outdir> name "THE ARCHITECT" [file]
  python -I mksvg.py <font.otf> <outdir> rule
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
    d, w = outline(font, text, size, tracking)
    if w > max_w:  # long names shrink to fit, keeping proportions
        k = max_w / w
        d, w = outline(font, text, size * k, tracking * k)
    return f'<path transform="translate({cx - w / 2:.2f} {baseline})" d="{d}"/>'


def hero(font, title, tagline):
    word = lettering(font, title, 104, 8, 620, 122, 1160)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 210" role="img" '
        f'aria-label="{title} — {tagline}">'
        f"<defs>{FOIL}{FADE}{GLOW}</defs>"
        f'<g fill="url(#foil)" stroke="{OBSIDIAN}" stroke-width="0.9" paint-order="stroke" '
        f'filter="url(#glow)">{word}</g>'
        '<rect x="492" y="150" width="256" height="1.6" fill="url(#fade)"/>'
        f'<path d="M620 146 L627 151 L620 156 L613 151 Z" fill="{CHAMPAGNE}"/>'
        '<text x="620" y="190" text-anchor="middle" '
        "font-family=\"ui-monospace, 'SF Mono', Menlo, monospace\" font-size=\"16\" "
        f'letter-spacing="11" fill="{BRASS}">{tagline}</text>'
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


def rule():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 16" role="presentation">'
        f"<defs>{FADE}</defs>"
        '<rect x="0" y="7" width="1000" height="1.5" fill="url(#fade)"/>'
        f'<path d="M500 2.5 L508 8 L500 13.5 L492 8 Z" fill="{CHAMPAGNE}"/>'
        "</svg>\n"
    )


def slug(text):
    return "-".join(text.lower().split())


if __name__ == "__main__":
    font = TTFont(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    kind = sys.argv[3]
    if kind == "hero":
        title, tagline = sys.argv[4], sys.argv[5]
        f = sys.argv[6] if len(sys.argv) > 6 else f"hero-{slug(title)}.svg"
        (out / f).write_text(hero(font, title, tagline.replace("·", "&#183;")))
    elif kind == "name":
        text = sys.argv[4]
        f = sys.argv[5] if len(sys.argv) > 5 else f"name-{slug(text)}.svg"
        (out / f).write_text(name(font, text))
    elif kind == "rule":
        (out / "rule.svg").write_text(rule())
    print(out / (f if kind != "rule" else "rule.svg"))
