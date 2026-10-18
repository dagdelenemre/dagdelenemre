#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the SVG assets for the GitHub profile README.

Each SVG embeds only the glyphs it actually uses, as a base64 WOFF2
@font-face, so the "operator file" type renders identically on any
GitHub theme without relying on the viewer having the fonts installed.

Run:  python build.py
Fonts (variable sources) live in assets/fonts/src/.
"""
import base64
import io
import os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.subset import Subsetter, Options

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "fonts", "src")
OUT = os.path.join(ROOT, "assets")

# ── Operator-file palette (from dagdelean.dev) ──────────────────────────
INK      = "#0b0b0a"   # page / card base
INK2     = "#111110"   # raised panel
INK3     = "#17170f"
LINE     = "#252421"   # hairline
LINE2    = "#3a3833"   # stronger hairline
BONE     = "#ece8de"   # primary text (dark bg)
BONE2    = "#cfc9bb"
ASH      = "#9a958a"   # dim text
SMOKE    = "#67635a"
SIGNAL   = "#ff3b21"   # accent red
SIGNAL2  = "#c42a15"
INK_TEXT = "#111110"   # primary text on light bg (section headers, light)

FAMS = {
    "display": ("BigShoulders-VF.ttf", "wght", "opsz"),  # display headings
    "text":    ("Archivo-VF.ttf",      "wght", "wdth"),  # body
    "mono":    ("MartianMono-VF.ttf",  "wght", "wdth"),  # labels
}

_cache = {}

def _instance(fam, wght, second):
    """Return a static TTFont instance of a variable font at the given axes."""
    key = (fam, wght, second)
    if key in _cache:
        return _cache[key]
    fname, a1, a2 = FAMS[fam]
    f = TTFont(os.path.join(SRC, fname))
    axes = {a1: wght, a2: second}
    instantiateVariableFont(f, axes, inplace=True)
    _cache[key] = f
    return f


class Font:
    """A font instance you can measure text with and emit as an @font-face."""
    _n = 0

    def __init__(self, fam, wght, second):
        self.tt = _instance(fam, wght, second)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.used = set()
        Font._n += 1
        self.css = f"f{Font._n}"

    def width(self, text, size):
        w = 0
        for ch in text:
            self.used.add(ch)
            gid = self.cmap.get(ord(ch))
            if gid is None:
                gid = ".notdef"
            adv = self.hmtx[gid][0] if gid in self.hmtx.metrics else self.hmtx[".notdef"][0]
            w += adv
        return w / self.upm * size

    def face(self):
        """Subset to used glyphs and return an @font-face rule (base64 woff2)."""
        f = TTFont()
        f = _clone(self.tt)
        opt = Options()
        opt.flavor = "woff2"
        opt.desubroutinize = True
        opt.recalc_bounds = True
        opt.name_IDs = []
        opt.notdef_outline = True
        opt.layout_features = []
        ss = Subsetter(options=opt)
        text = "".join(sorted(self.used)) or " "
        ss.populate(text=text)
        ss.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return (f"@font-face{{font-family:'{self.css}';"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


def _clone(tt):
    buf = io.BytesIO()
    tt.save(buf)
    buf.seek(0)
    return TTFont(buf)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def write(name, svg):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"  {name:22} {len(svg.encode()):>7} bytes")


# ════════════════════════════════════════════════════════════════════════
# Shared decorative bits
# ════════════════════════════════════════════════════════════════════════
def grain(w, h, op=".04"):
    return (f'<rect width="{w}" height="{h}" fill="url(#hatch)" opacity="{op}"/>')

HATCH = ('<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
         'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
         f'stroke="{BONE}" stroke-width="1"/></pattern>')

def corner(x, y, s, flip=1, color=SIGNAL):
    """Registration tick (dossier corner)."""
    return (f'<path d="M{x} {y+ s*flip}V{y}H{x+s}" fill="none" '
            f'stroke="{color}" stroke-width="2"/>')


# ════════════════════════════════════════════════════════════════════════
# BANNER
# ════════════════════════════════════════════════════════════════════════
def banner():
    W, H = 1200, 340
    disp = Font("display", 820, 72)   # name
    lab  = Font("mono", 560, 100)     # labels
    txt  = Font("text", 460, 100)     # tagline
    sig  = Font("mono", 620, 100)     # handle

    name = "EMRE KADİR DAĞDELEN"
    name_sz = 92
    # Fit name within content width
    maxw = W - 160
    nw = disp.width(name, name_sz)
    if nw > maxw:
        name_sz = int(name_sz * maxw / nw)
        nw = disp.width(name, name_sz)

    tagline = "I build for the web, and I am training to break it."
    tag_sz = 21

    labels = "OPERATOR FILE   /   TLP:CLEAR   /   REV 2026.10"
    handle = "@dagdelean"

    # header strip meta
    meta_r = "SAMSUN · TR · UTC+3"

    body = []
    body.append(f'<rect width="{W}" height="{H}" fill="{INK}"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    body.append(grain(W, H, ".05"))
    # animated scan lines
    body.append('<g clip-path="url(#clip)">')
    for i, (y, d) in enumerate([(70, 0), (150, -3), (250, -6), (300, -1.5)]):
        body.append(
            f'<line class="scan" x1="0" y1="{y}" x2="{W}" y2="{y}" '
            f'stroke="{SIGNAL}" stroke-width="1" style="animation-delay:{d}s"/>')
    body.append('</g>')

    # top hairline + label row
    body.append(f'<line x1="80" y1="56" x2="{W-80}" y2="56" stroke="{LINE2}"/>')
    body.append(
        f'<text x="80" y="44" font-family="{lab.css}" font-size="13" '
        f'letter-spacing="2" fill="{ASH}">{esc(labels)}</text>')
    mrw = lab.width(meta_r, 13)
    body.append(
        f'<text x="{W-80-mrw}" y="44" font-family="{lab.css}" font-size="13" '
        f'letter-spacing="2" fill="{ASH}">{esc(meta_r)}</text>')

    # signal corner ticks
    body.append(corner(80, 92, 16))
    body.append(corner(W-80, 92, -16))

    # name
    body.append(
        f'<text x="80" y="188" font-family="{disp.css}" font-size="{name_sz}" '
        f'fill="{BONE}" letter-spacing="1">{esc(name)}</text>')
    # handle under name, right-aligned to name end
    hw = sig.width(handle, 18)
    body.append(
        f'<text x="82" y="224" font-family="{sig.css}" font-size="18" '
        f'letter-spacing="1" fill="{SIGNAL}">{esc(handle)}'
        f'<animate attributeName="opacity" values="1;.35;1" dur="2.4s" '
        f'repeatCount="indefinite"/></text>')

    # tagline
    body.append(
        f'<text x="80" y="276" font-family="{txt.css}" font-size="{tag_sz}" '
        f'fill="{BONE2}">{esc(tagline)}</text>')

    # bottom hairline + class line
    body.append(f'<line x1="80" y1="300" x2="{W-80}" y2="300" stroke="{LINE}"/>')
    cls = "CLASS  Offensive security, in training        STATUS  shipping · studying · open to work"
    body.append(
        f'<text x="80" y="322" font-family="{lab.css}" font-size="12" '
        f'letter-spacing="1.5" fill="{SMOKE}">{esc(cls)}</text>')

    faces = disp.face() + lab.face() + txt.face() + sig.face()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Emre Kadir Dagdelen (dagdelean), operator file. I build for the web, and I am training to break it.">
<defs>
<radialGradient id="vig" cx=".2" cy="0" r="1.1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".10"/>
<stop offset=".5" stop-color="{SIGNAL}" stop-opacity="0"/>
</radialGradient>
{HATCH}
<clipPath id="clip"><rect width="{W}" height="{H}"/></clipPath>
</defs>
<style>
{faces}
.scan{{opacity:.14;animation:scan 7s linear infinite}}
@keyframes scan{{0%{{transform:translateX(-40px);opacity:0}}10%{{opacity:.16}}90%{{opacity:.16}}100%{{transform:translateX(40px);opacity:0}}}}
@media (prefers-reduced-motion: reduce){{.scan{{animation:none}}}}
</style>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="{INK}"/>
<clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<g clip-path="url(#r)">
{chr(10).join(body)}
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{LINE2}"/>
</svg>'''
    write("banner.svg", svg)


# ════════════════════════════════════════════════════════════════════════
# SECTION HEADERS  (light + dark variants)
# ════════════════════════════════════════════════════════════════════════
def header(slug, index, title, icon):
    for mode, fg, dim in (("light", INK_TEXT, SMOKE), ("dark", BONE, ASH)):
        disp = Font("display", 760, 72)
        lab = Font("mono", 560, 100)
        H = 58
        idx_w = lab.width(index, 14)
        tx = 0
        # icon box
        parts = []
        parts.append(
            f'<g transform="translate(2,15)" fill="none" stroke="{SIGNAL}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon}</g>')
        parts.append(
            f'<text x="38" y="40" font-family="{disp.css}" font-size="34" '
            f'font-weight="700" fill="{fg}" letter-spacing="1">{esc(title)}</text>')
        tw = disp.width(title, 34)
        # index tag after title
        parts.append(
            f'<text x="{38+tw+16}" y="38" font-family="{lab.css}" font-size="13" '
            f'letter-spacing="2" fill="{SIGNAL}">{esc(index)}</text>')
        W = int(38 + tw + 16 + idx_w + 30)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">
<style>{disp.face()}{lab.face()}</style>
{chr(10).join(parts)}
</svg>'''
        write(f"h-{slug}-{mode}.svg", svg)


# ════════════════════════════════════════════════════════════════════════
# PROJECT CARD
# ════════════════════════════════════════════════════════════════════════
def card(slug, tag, title, meta, desc, chips, footL, footR, seed=0):
    W, H = 560, 300
    lab  = Font("mono", 560, 100)
    disp = Font("display", 760, 72)
    txt  = Font("text", 440, 100)
    chipf = Font("mono", 520, 100)

    P = 28
    parts = []
    parts.append(f'<rect width="{W}" height="{H}" fill="{INK2}"/>')
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#cardglow{seed})"/>')
    parts.append(grain(W, H, ".045"))
    # faint moving signal line at top edge
    parts.append(
        f'<line class="edge" x1="0" y1="2" x2="{W}" y2="2" stroke="{SIGNAL}" '
        f'stroke-width="2" stroke-dasharray="80 {W}" style="animation-delay:{-seed*0.7}s"/>')

    # tag row
    parts.append(
        f'<text x="{P}" y="{P+16}" font-family="{lab.css}" font-size="12.5" '
        f'letter-spacing="2" fill="{ASH}">{esc(tag)}</text>')
    tagw = lab.width(tag, 12.5)

    # title
    parts.append(
        f'<text x="{P}" y="{P+70}" font-family="{disp.css}" font-size="52" '
        f'fill="{BONE}" letter-spacing="1">{esc(title)}'
        f'<tspan fill="{SIGNAL}">_</tspan></text>')

    # meta line (under title)
    parts.append(
        f'<text x="{P}" y="{P+96}" font-family="{lab.css}" font-size="11.5" '
        f'letter-spacing="1.5" fill="{SMOKE}">{esc(meta)}</text>')

    # description (wrap)
    parts += wrap(txt, desc, P, P + 130, W - 2*P, 16, 23, BONE2, max_lines=3)

    # chips row
    cy = H - 74
    cx = P
    for c in chips:
        cw = chipf.width(c, 11.5) + 22
        parts.append(
            f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="26" rx="4" '
            f'fill="none" stroke="{LINE2}"/>')
        parts.append(
            f'<text x="{cx+cw/2:.1f}" y="{cy+17}" font-family="{chipf.css}" '
            f'font-size="11.5" letter-spacing="1" fill="{BONE2}" '
            f'text-anchor="middle">{esc(c)}</text>')
        cx += cw + 8
        if cx > W - P - 60:
            break

    # footer
    parts.append(f'<line x1="{P}" y1="{H-40}" x2="{W-P}" y2="{H-40}" stroke="{LINE}"/>')
    parts.append(
        f'<text x="{P}" y="{H-18}" font-family="{lab.css}" font-size="11.5" '
        f'letter-spacing="1.5" fill="{ASH}">{esc(footL)}</text>')
    frw = lab.width(footR, 11.5)
    parts.append(
        f'<text x="{W-P-frw}" y="{H-18}" font-family="{lab.css}" font-size="11.5" '
        f'letter-spacing="1.5" fill="{SIGNAL}">{esc(footR)}</text>')

    faces = lab.face() + disp.face() + txt.face() + chipf.face()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}: {esc(desc)}">
<defs>
<radialGradient id="cardglow{seed}" cx=".1" cy="0" r="1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".12"/>
<stop offset=".55" stop-color="{SIGNAL}" stop-opacity="0"/>
</radialGradient>
{HATCH}
</defs>
<style>
{faces}
.edge{{opacity:.6;animation:slide 5s linear infinite}}
@keyframes slide{{to{{stroke-dashoffset:-{W+80}}}}}
@media (prefers-reduced-motion: reduce){{.edge{{animation:none;opacity:.3}}}}
</style>
<clipPath id="rc{seed}"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#rc{seed})">
{chr(10).join(parts)}
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{LINE2}"/>
</svg>'''
    write(f"p-{slug}.svg", svg)


def wrap(font, text, x, y, maxw, size, lh, fill, max_lines=3):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.width(t, size) > maxw and cur:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
        else:
            cur = t
    if cur and len(lines) < max_lines:
        lines.append(cur)
    out = []
    for i, ln in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y+i*lh}" font-family="{font.css}" '
            f'font-size="{size}" fill="{fill}">{esc(ln)}</text>')
    return out


# ════════════════════════════════════════════════════════════════════════
# STACK
# ════════════════════════════════════════════════════════════════════════
def stack():
    items = ["Python", "C (C11)", "C++", "C#", "JavaScript", "HTML", "CSS"]
    W = 1140
    chipf = Font("mono", 520, 100)
    lab = Font("mono", 560, 100)
    H = 128
    P = 28
    parts = [f'<rect width="{W}" height="{H}" fill="{INK2}"/>',
             f'<rect width="{W}" height="{H}" fill="url(#sg)"/>',
             grain(W, H, ".04")]
    parts.append(
        f'<text x="{P}" y="34" font-family="{lab.css}" font-size="12" '
        f'letter-spacing="2" fill="{ASH}">LANGUAGES I BUILD AND BREAK IN</text>')
    cx, cy = P, 56
    sz = 15
    for c in items:
        cw = chipf.width(c, sz) + 34
        if cx + cw > W - P:
            cx = P
            cy += 42
        parts.append(
            f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="34" rx="6" '
            f'fill="{INK}" stroke="{LINE2}"/>')
        parts.append(
            f'<circle cx="{cx+15:.1f}" cy="{cy+17}" r="3" fill="{SIGNAL}"/>')
        parts.append(
            f'<text x="{cx+26:.1f}" y="{cy+22}" font-family="{chipf.css}" '
            f'font-size="{sz}" letter-spacing=".5" fill="{BONE}">{esc(c)}</text>')
        cx += cw + 10
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Stack: {esc(', '.join(items))}">
<defs>
<radialGradient id="sg" cx=".05" cy="0" r="1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".09"/>
<stop offset=".5" stop-color="{SIGNAL}" stop-opacity="0"/>
</radialGradient>
{HATCH}
</defs>
<style>{chipf.face()}{lab.face()}</style>
<clipPath id="rs"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#rs)">{chr(10).join(parts)}</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{LINE2}"/>
</svg>'''
    write("stack.svg", svg)


# ════════════════════════════════════════════════════════════════════════
# BUTTONS
# ════════════════════════════════════════════════════════════════════════
def button(slug, label, icon):
    f = Font("mono", 560, 100)
    H = 52
    sz = 14
    tw = f.width(label, sz)
    pad_l = 48   # icon area
    pad_r = 22
    W = int(pad_l + tw + pad_r)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
<style>{f.face()}
.btn:hover rect{{fill:{INK3}}}</style>
<g class="btn">
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="{INK2}" stroke="{LINE2}"/>
<g transform="translate(18,16)" fill="none" stroke="{SIGNAL}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<text x="{pad_l}" y="{H/2+5:.0f}" font-family="{f.css}" font-size="{sz}" letter-spacing="1" fill="{BONE}">{esc(label)}</text>
</g>
</svg>'''
    write(f"btn-{slug}.svg", svg)


# ── icon paths (20x20 stroke) ───────────────────────────────────────────
IC_SITE = '<circle cx="10" cy="10" r="9"/><path d="M1 10h18M10 1c3 3 3 15 0 18M10 1c-3 3-3 15 0 18"/>'
IC_MAIL = '<rect x="1" y="3" width="18" height="14" rx="2"/><path d="M1 5l9 6 9-6"/>'
IC_GH   = '<path d="M7.5 18c-4 1.2-4-2.2-5.5-2.6M18 17v-2.8c0-1 .1-1.4-.5-2 2.3-.3 4.5-1.2 4.5-5a3.9 3.9 0 0 0-1.1-2.7 3.6 3.6 0 0 0-.1-2.7s-.9-.3-2.9 1.1a9.6 9.6 0 0 0-5 0C5.4.2 4.5.5 4.5.5a3.6 3.6 0 0 0-.1 2.7A3.9 3.9 0 0 0 3.3 6c0 3.7 2.2 4.6 4.4 5-.5.5-.5 1-.5 1.7V18"/>'
IC_LI   = '<rect x="1" y="1" width="18" height="18" rx="2"/><path d="M6 8v6M6 5v.01M10 14V8M14 14v-3.5a2 2 0 0 0-4 0"/>'
IC_PYPI = '<path d="M3 6l7-4 7 4v8l-7 4-7-4z"/><path d="M3 6l7 4 7-4M10 10v8"/>'

# section icons (24x24 stroke)
SI_CURRENT = '<circle cx="11" cy="11" r="9"/><path d="M11 6v5l3 2"/>'
SI_PROJ    = '<path d="M2 6l9-4 9 4v10l-9 4-9-4z"/><path d="M2 6l9 4 9-4M11 10v10"/>'
SI_STACK   = '<path d="M11 2l9 5-9 5-9-5z"/><path d="M2 12l9 5 9-5M2 17l9 5 9-5"/>'
SI_CONTACT = '<path d="M20 15a2 2 0 0 1-2 2H6l-4 4V4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
SI_PATH    = '<circle cx="4" cy="19" r="2.5"/><circle cx="19" cy="5" r="2.5"/><path d="M6 17L17 7"/>'
SI_CAP     = '<circle cx="11" cy="11" r="9"/><circle cx="11" cy="11" r="4"/><path d="M11 1v4M11 17v4M1 11h4M17 11h4"/>'
SI_CERT    = '<path d="M11 2l8 3v6c0 5-4 8-8 10-4-2-8-5-8-10V5z"/><path d="M7.5 11l2.5 2.5 5-5"/>'


# ════════════════════════════════════════════════════════════════════════
# CAPABILITY MATRIX  (status, not percentages)
# ════════════════════════════════════════════════════════════════════════
def capability():
    rows = [
        ("Web application testing", "ACTIVE"),
        ("Network & infrastructure testing", "ACTIVE"),
        ("Applied cryptography", "ACTIVE"),
        ("Windows internals & Win32 API", "TRAINING"),
        ("Active Directory attack paths", "TRAINING"),
        ("Adversary emulation & C2", "NEXT"),
    ]
    stat_col = {"ACTIVE": SIGNAL, "TRAINING": BONE2, "NEXT": SMOKE}
    W = 1140
    P = 28
    gap = 22
    colw = (W - 2 * P - gap) / 2
    rh = 56
    top = 56
    lab = Font("mono", 560, 100)
    txt = Font("text", 460, 100)
    badge = Font("mono", 600, 100)

    parts = [f'<rect width="{W}" height="10" fill="{INK2}"/>']  # placeholder, replaced
    H = top + 3 * rh + 20
    parts = [f'<rect width="{W}" height="{H}" fill="{INK2}"/>',
             f'<rect width="{W}" height="{H}" fill="url(#cg)"/>',
             grain(W, H, ".04")]
    parts.append(
        f'<text x="{P}" y="34" font-family="{lab.css}" font-size="12" '
        f'letter-spacing="2" fill="{ASH}">STATUS, NOT PERCENTAGES</text>')

    for i, (label, status) in enumerate(rows):
        col = i // 3
        row = i % 3
        x = P + col * (colw + gap)
        y = top + row * rh
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{colw:.1f}" height="{rh-10}" rx="7" '
            f'fill="{INK}" stroke="{LINE2}"/>')
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="3" height="{rh-10}" rx="1.5" '
            f'fill="{stat_col[status]}"/>')
        parts.append(
            f'<text x="{x+18:.1f}" y="{y+29}" font-family="{txt.css}" font-size="15.5" '
            f'fill="{BONE}">{esc(label)}</text>')
        bw = badge.width(status, 11)
        bx = x + colw - bw - 30
        parts.append(
            f'<rect x="{bx-10:.1f}" y="{y+13}" width="{bw+20:.1f}" height="20" rx="10" '
            f'fill="none" stroke="{stat_col[status]}" stroke-opacity=".5"/>')
        parts.append(
            f'<text x="{bx:.1f}" y="{y+27}" font-family="{badge.css}" font-size="11" '
            f'letter-spacing="1.5" fill="{stat_col[status]}">{esc(status)}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Capability matrix: web application testing, network and infrastructure testing, applied cryptography (active); Windows internals and Win32 API, Active Directory attack paths (training); adversary emulation and C2 (next).">
<defs>
<radialGradient id="cg" cx=".05" cy="0" r="1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".09"/>
<stop offset=".5" stop-color="{SIGNAL}" stop-opacity="0"/>
</radialGradient>
{HATCH}
</defs>
<style>{lab.face()}{txt.face()}{badge.face()}</style>
<clipPath id="rcap"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#rcap)">{chr(10).join(parts)}</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{LINE2}"/>
</svg>'''
    write("capability.svg", svg)


# ════════════════════════════════════════════════════════════════════════
# CLEARANCES  (certifications)
# ════════════════════════════════════════════════════════════════════════
def clearances():
    rows = [
        ("LVL 1", "CAPT", "Certified Associate Penetration Tester · Hackviser", "HV-CAPT-P746FUJO"),
        ("LVL 2", "Siber Vatan", "Penetration Testing Training, 200 hours · national program", "12625794724929"),
        ("LVL 3", "HV-CORE", "Hackviser Core Certification · Hackviser", "HV-CORE-0F82DTZZ"),
    ]
    W = 1140
    P = 28
    rh = 66
    top = 52
    H = top + len(rows) * rh + 8
    lab = Font("mono", 560, 100)
    disp = Font("display", 720, 72)
    txt = Font("text", 440, 100)
    cred = Font("mono", 540, 100)

    parts = [f'<rect width="{W}" height="{H}" fill="{INK2}"/>',
             f'<rect width="{W}" height="{H}" fill="url(#clg)"/>',
             grain(W, H, ".04")]
    parts.append(
        f'<text x="{P}" y="34" font-family="{lab.css}" font-size="12" '
        f'letter-spacing="2" fill="{ASH}">ESCALATION LOG · CREDENTIAL IDs ARE VERIFIABLE</text>')

    for i, (lvl, name, desc, cid) in enumerate(rows):
        y = top + i * rh
        if i:
            parts.append(f'<line x1="{P}" y1="{y}" x2="{W-P}" y2="{y}" stroke="{LINE}"/>')
        cy = y + rh / 2
        # level badge
        lw = lab.width(lvl, 11)
        parts.append(
            f'<rect x="{P}" y="{cy-13:.1f}" width="{lw+22:.1f}" height="26" rx="5" '
            f'fill="{INK}" stroke="{LINE2}"/>')
        parts.append(
            f'<text x="{P+11:.1f}" y="{cy+4:.1f}" font-family="{lab.css}" font-size="11" '
            f'letter-spacing="1.5" fill="{SIGNAL}">{esc(lvl)}</text>')
        nx = P + lw + 22 + 22
        parts.append(
            f'<text x="{nx:.1f}" y="{cy-4:.1f}" font-family="{disp.css}" font-size="26" '
            f'fill="{BONE}" letter-spacing=".5">{esc(name)}</text>')
        parts.append(
            f'<text x="{nx:.1f}" y="{cy+18:.1f}" font-family="{txt.css}" font-size="13.5" '
            f'fill="{ASH}">{esc(desc)}</text>')
        # credential id, right
        cw = cred.width(cid, 12.5)
        parts.append(
            f'<text x="{W-P-cw:.1f}" y="{cy-2:.1f}" font-family="{cred.css}" font-size="12.5" '
            f'letter-spacing="1" fill="{SIGNAL}">{esc(cid)}</text>')
        parts.append(
            f'<text x="{W-P-cred.width("CREDENTIAL",10):.1f}" y="{cy+16:.1f}" '
            f'font-family="{cred.css}" font-size="10" letter-spacing="2" '
            f'fill="{SMOKE}">CREDENTIAL</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Clearances: CAPT (HV-CAPT-P746FUJO), Siber Vatan 200-hour penetration testing training, HV-CORE (HV-CORE-0F82DTZZ).">
<defs>
<radialGradient id="clg" cx=".05" cy="0" r="1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity=".09"/>
<stop offset=".5" stop-color="{SIGNAL}" stop-opacity="0"/>
</radialGradient>
{HATCH}
</defs>
<style>{lab.face()}{disp.face()}{txt.face()}{cred.face()}</style>
<clipPath id="rcl"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#rcl)">{chr(10).join(parts)}</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="15.5" fill="none" stroke="{LINE2}"/>
</svg>'''
    write("clearances.svg", svg)


def main():
    print("Building assets …")
    banner()
    header("currently", "§ ACTIVE", "Currently", SI_CURRENT)
    header("projects",  "§ ARSENAL", "Projects", SI_PROJ)
    header("capability","§ MATRIX", "Capability", SI_CAP)
    header("stack",     "§ RUNTIME", "Stack", SI_STACK)
    header("certs",     "§ CLEARANCE", "Clearances", SI_CERT)
    header("contact",   "§ C2", "Contact", SI_CONTACT)

    card("nopanic", "TOOL 01 · PYTHON 3.10+ · MIT · PyPI", "nopanic",
         "pip install nopanic",
         "The resilience toolkit Python was missing: retry, circuit breaker, "
         "timeout, adaptive rate limit, bulkhead, hedging and fallback behind "
         "one decorator API. Sync and async, zero runtime deps.",
         ["retry", "breaker", "hedging", "0 deps"],
         "141 TESTS · < 2S SUITE", "github.com/dagdelenemre/nopanic", seed=1)

    card("bicbic416", "TOOL 02 · C11 · MIT · 12.10.2026", "bicbic416",
         "experimental · read before use",
         "An experimental 416-bit block cipher designed and written in portable "
         "C11, with CTR mode, a hash, a file-encryption tool, a browser build and "
         "a Python reference, plus its own cryptanalysis report.",
         ["ARX", "CTR", "hash", "C11"],
         "WITH WRITE-UP", "github.com/dagdelenemre/bicbic416", seed=2)

    card("omusiber", "ENG 04 · DESIGN · BUILD · DEPLOY", "omusiber.org",
         "OMU Siber · live 28.09.2026",
         "Website for the Ondokuz Mayis University cyber security community, whose "
         "board I sit on: six training tracks, an event calendar and a three-part "
         "flag hunt hidden in the page.",
         ["design", "deploy", "CTF"],
         "COMMUNITY SITE", "omusiber.org", seed=3)

    card("sites", "AGENCY · POLLYKOO · SINCE 2024", "Client sites",
         "4 live production builds",
         "End-to-end websites for small businesses through Pollykoo Agency: "
         "arzagro.com (bilingual TR/EN), lotusinsaatemlak.com (dual-site) and "
         "solislumentr.com (cafe with a live QR menu).",
         ["design", "build", "deploy", "TR/EN"],
         "FOUNDER", "dagdelean.dev", seed=4)

    capability()
    stack()
    clearances()

    button("site", "DAGDELEAN.DEV", IC_SITE)
    button("mail", "DAGDELEN.CYBER@GMAIL.COM", IC_MAIL)
    button("github", "GITHUB", IC_GH)
    button("linkedin", "LINKEDIN", IC_LI)
    button("pypi", "PYPI", IC_PYPI)

    print("Done.")


if __name__ == "__main__":
    main()
