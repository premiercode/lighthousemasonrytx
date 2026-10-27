"""Procedural SVG art for the Lighthouse Masonry site (run by hand, not a build step).

    python3 tools/gen.py        # writes tools/frag/*, assets/img/logo*.svg, favicon.svg
    python3 tools/assemble.py   # writes index.html and 404.html from tools/tpl + frag

Sources that are not generated (lighthouse, map, icons, v1 wall geometry,
outlined logo text) live in tools/src/.
"""
import math, os, random, re, shutil

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
SRC = os.path.join(TOOLS, 'src')
OUT = os.path.join(TOOLS, 'frag')
os.makedirs(OUT, exist_ok=True)


def f(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def save(name, s):
    open(os.path.join(OUT, name), 'w').write(s)


def src(name):
    return open(os.path.join(SRC, name)).read()


# =====================================================================
# HERO WALL — v1 geometry; tones narrowed (no t5) + shared brick texture
# =====================================================================
def hero_wall():
    rnd = random.Random(11)
    wall = src('wall-base.svg').strip()
    # anchored to the top so the caps always show; the base courses crop first
    wall = wall.replace('preserveAspectRatio="xMidYMax slice"', 'preserveAspectRatio="xMidYMin slice"')
    wall = re.sub(r'class="b t5"', lambda m: f'class="b t{rnd.choice([1, 3])}"', wall)

    # Texture tile: 360 x 160 = 3 bricks x 4 courses of the panel bond.
    # Course tops on y = 0 mod 80 are offset half a brick (bricks x 60..174),
    # tops on 40 mod 80 start at 0 (x 0..114). Brick face = 34 tall after a 6 joint.
    t = random.Random(5)
    faces = []
    for cy in (0, 40, 80, 120):
        off = 60 if cy % 80 == 0 else 0
        for k in range(-1, 4):
            x1 = off + k * 120
            faces.append((x1, cy + 6, 114, 34))
    parts = []
    for (x, y, w, h) in faces:
        # bevel: lit top edge, shaded bed
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="2" fill="#fff" fill-opacity=".09"/>')
        parts.append(f'<rect x="{x}" y="{y + h - 3}" width="{w}" height="3" fill="#000" fill-opacity=".16"/>')
        parts.append(f'<rect x="{x + w - 2}" y="{y}" width="2" height="{h}" fill="#000" fill-opacity=".08"/>')
        # fired-clay speckle
        for _ in range(9):
            sx = x + 4 + t.random() * (w - 10)
            sy = y + 4 + t.random() * (h - 10)
            s = 1.4 + t.random() * 2.4
            dark = t.random() < 0.7
            parts.append(f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(s)}" height="{f(s * (0.6 + t.random() * 0.6))}" '
                         f'fill="{"#000" if dark else "#fff"}" fill-opacity="{0.14 if dark else 0.08}"/>')
    pattern = ('<defs><pattern id="wall-tex" width="360" height="160" patternUnits="userSpaceOnUse">'
               + ''.join(parts) + '</pattern></defs>')
    # silhouette: panels (8 courses) + piers (10 courses)
    piers = [0, 600, 1200, 1800, 2400]
    sil = 'M0 160H2400V480H0Z' + ''.join(f'M{p - 117} 80h234v80h-234Z' for p in piers)
    tex = f'<path class="tex" d="{sil}" fill="url(#wall-tex)"/>'
    # texture sits above bricks but under copings/caps (first .cope group)
    i = wall.index('<g class="cope"')
    wall = wall.replace('aria-hidden="true" focusable="false">', 'aria-hidden="true" focusable="false">' + pattern, 1)
    i = wall.index('<g class="cope"')
    wall = wall[:i] + tex + wall[i:]
    assert 't5' not in wall
    save('wall.svg', '    ' + wall)


# =====================================================================
# ELEVATION DRAWINGS — cream linework on night-800, mason's drawing set
# =====================================================================
INK = '#f4ecdc'


class D:
    def __init__(self):
        self.o = []

    def add(self, s):
        self.o.append(s)

    def line(self, x1, y1, x2, y2, cls='l'):
        self.add(f'<path class="{cls}" d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}"/>')

    def text(self, x, y, s, cls='t', anchor='start', rot=None):
        tr = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot is not None else ''
        a = '' if anchor == 'start' else f' text-anchor="{anchor}"'
        self.add(f'<text class="{cls}" x="{f(x)}" y="{f(y)}"{a}{tr}>{s}</text>')

    def hdim(self, x1, x2, y, label, ext_from=None, above=True):
        """Horizontal dimension with architectural tick marks."""
        if ext_from is not None:
            for x in (x1, x2):
                self.line(x, ext_from, x, y + (-6 if ext_from > y else 6), 'dm')
        self.line(x1 - 8, y, x2 + 8, y, 'dm')
        for x in (x1, x2):
            self.line(x - 5, y + 5, x + 5, y - 5, 'tk')
        self.text((x1 + x2) / 2, y - 7 if above else y + 17, label, 'td', 'middle')

    def vdim(self, x, y1, y2, label, ext_from=None):
        if ext_from is not None:
            for y in (y1, y2):
                self.line(ext_from, y, x + (6 if ext_from < x else -6), y, 'dm')
        self.line(x, y1 - 8, x, y2 + 8, 'dm')
        for y in (y1, y2):
            self.line(x - 5, y + 5, x + 5, y - 5, 'tk')
        self.text(x - 8, (y1 + y2) / 2, label, 'td', 'middle', rot=-90)

    def leader(self, x1, y1, x2, y2, label, anchor='start', shoulder=26):
        """Note at (x1,y1) with a leader to (x2,y2). '|' splits lines. Text is knocked out of the hatch."""
        lines = label.split('|')
        cw = 7.95
        sx = x1 + (-shoulder if anchor == 'end' else shoulder)
        tx = sx + (-4 if anchor == 'end' else 4)
        self.add(f'<path class="ld" d="M{f(x2)} {f(y2)}L{f(x1)} {f(y1)}H{f(sx)}"/><circle class="dot" cx="{f(x2)}" cy="{f(y2)}" r="2.6"/>')
        for i, ln in enumerate(lines):
            n = len(re.sub(r'&#?\w+;', 'x', ln))
            w = n * cw + 8
            ty = y1 + 4 + i * 16
            rx = tx - 4 if anchor != 'end' else tx - w + 4
            self.add(f'<rect class="ko" x="{f(rx)}" y="{f(ty - 12)}" width="{f(w)}" height="16"/>')
            self.text(tx, ty, ln, 'tn', anchor)

    def grade(self, x1, x2, y):
        self.line(x1, y, x2, y, 'g')
        x = x1 + 6
        while x < x2 - 6:
            self.line(x, y + 2, x - 9, y + 11, 'gh')
            x += 14

    def title_block(self, W, y, h, cells):
        """cells: list of (width_fraction, small_label, value)."""
        x0, x1 = 24, W - 24
        self.add(f'<rect class="tb" x="{x0}" y="{y}" width="{x1 - x0}" height="{h}"/>')
        x = x0
        for i, (frac, small, value) in enumerate(cells):
            w = (x1 - x0) * frac
            if i:
                self.line(x, y, x, y + h, 'tbl')
            self.text(x + 10, y + 15, small, 'tbs')
            self.text(x + 10, y + h - 11, value, 'tbv')
            x += w

    def style_text(self):
        return self.svg(0, 0, _style_only=True)

    def svg(self, W, H, extra_defs='', _style_only=False):
        style = (
            f'.dwg .l{{stroke:{INK};stroke-width:2;fill:none;stroke-linejoin:round}}'
            f'.dwg .lb{{stroke:{INK};stroke-width:2.6;fill:none;stroke-linejoin:round}}'
            f'.dwg .lt{{stroke:{INK};stroke-width:1;fill:none;opacity:.55}}'
            f'.dwg .c{{stroke:{INK};stroke-width:.8;fill:none;opacity:.26}}'
            f'.dwg .hd{{stroke:{INK};stroke-width:.8;fill:none;opacity:.34}}'
            f'.dwg .hid{{stroke:{INK};stroke-width:1.2;fill:none;stroke-dasharray:7 5;opacity:.55}}'
            f'.dwg .cl{{stroke:{INK};stroke-width:.8;fill:none;stroke-dasharray:18 4 3 4;opacity:.45}}'
            f'.dwg .dm{{stroke:{INK};stroke-width:.8;fill:none;opacity:.6}}'
            f'.dwg .tk{{stroke:{INK};stroke-width:1.6;opacity:.85}}'
            f'.dwg .ld{{stroke:{INK};stroke-width:.8;fill:none;opacity:.7}}'
            f'.dwg .dot{{fill:{INK}}}.dwg .ko{{fill:#17233a}}'
            f'.dwg .g{{stroke:{INK};stroke-width:2.4}}'
            f'.dwg .gh{{stroke:{INK};stroke-width:.8;opacity:.4}}'
            f'.dwg .fl{{fill:{INK};fill-opacity:.07}}'
            f'.dwg .fs{{fill:{INK};fill-opacity:.14}}'
            f'.dwg .tb{{fill:none;stroke:{INK};stroke-width:1.2;opacity:.8}}'
            f'.dwg .tbl{{stroke:{INK};stroke-width:1;opacity:.5}}'
            f'.dwg .frame{{fill:none;stroke:{INK};stroke-width:1;opacity:.35}}'
            f'.dwg text{{fill:{INK};letter-spacing:.06em}}'
            f'.dwg .t,.dwg .tn{{font-size:12px;opacity:.85}}'
            f'.dwg .td{{font-size:13px;opacity:.9}}'
            f'.dwg .tbs{{font-size:9px;opacity:.55;letter-spacing:.14em}}'
            f'.dwg .tbv{{font-size:12.5px;font-weight:600}}'
        )
        if _style_only:
            return style
        return (f'<svg class="dwg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">'
                f'{extra_defs}'
                f'<rect class="frame" x="12" y="12" width="{W - 24}" height="{H - 24}"/>'
                + ''.join(self.o) + '</svg>')


def hatch_courses(d, x1, x2, y_top, y_bot, pitch, cls='c'):
    y = y_bot - pitch
    while y > y_top + 0.5:
        d.line(x1, y, x2, y, cls)
        y -= pitch


def head_joints(d, x1, x2, y_top, y_bot, pitch, unit, cls='hd', flemish=False):
    """Running (or Flemish) bond head joints inside a rectangular patch."""
    row = 0
    y = y_bot
    while y - pitch >= y_top - 0.5:
        if flemish:
            # stretcher (unit) + header (unit/2) alternating; next row shifted so headers centre on stretchers
            seq = [unit, unit / 2]
            x = x1 - (0 if row % 2 == 0 else unit * 0.75)
            i = 0
            while x < x2:
                x += seq[i % 2]
                if x1 + 2 < x < x2 - 2:
                    d.line(x, y - pitch, x, y, cls)
                i += 1
        else:
            off = 0 if row % 2 == 0 else unit / 2
            x = x1 + off
            while x < x2:
                if x1 + 2 < x < x2 - 2:
                    d.line(x, y - pitch, x, y, cls)
                x += unit
        y -= pitch
        row += 1


def plate_screening():
    W, H = 1200, 560
    d = D()
    GR = 404                       # grade
    piers = [130, 450, 770, 1090]  # 20'-0" O.C.
    PW = 46                        # pier width
    PANEL_TOP = 236                # 8'-0" panel
    PIER_TOP = 206                 # 9'-4" pier
    ppf = (GR - PANEL_TOP) / 8     # px per foot (21)

    # below grade: grade beam + drilled piers (hidden lines)
    d.add(f'<path class="hid" d="M{piers[0] - PW / 2} {GR}V{GR + 22}H{piers[-1] + PW / 2}V{GR}"/>')
    for p in piers:
        d.add(f'<path class="hid" d="M{p - 13} {GR + 22}V{GR + 74}H{p + 13}V{GR + 22}"/>')
        d.line(p, PIER_TOP - 40, p, GR + 84, 'cl')

    # panels
    for a, b in zip(piers, piers[1:]):
        x1, x2 = a + PW / 2, b - PW / 2
        hatch_courses(d, x1, x2, PANEL_TOP + 9, GR, 7)
        # coping
        d.add(f'<path class="fs" d="M{x1 - 2} {PANEL_TOP - 9}H{x2 + 2}V{PANEL_TOP}H{x1 - 2}Z"/>')
        d.add(f'<path class="l" d="M{x1 - 2} {PANEL_TOP}V{PANEL_TOP - 9}H{x2 + 2}V{PANEL_TOP}"/>')
        d.line(x1, GR, x1, PANEL_TOP, 'l')
        d.line(x2, GR, x2, PANEL_TOP, 'l')
    # material patch: running-bond head joints on one panel corner
    head_joints(d, piers[0] + PW / 2, piers[0] + PW / 2 + 150, GR - 70, GR, 7, 22)

    # piers + caps
    for p in piers:
        L, R = p - PW / 2, p + PW / 2
        d.add(f'<path class="fl" d="M{L} {GR}V{PIER_TOP}H{R}V{GR}Z"/>')
        hatch_courses(d, L, R, PIER_TOP, GR, 7, 'c')
        d.add(f'<path class="lb" d="M{L} {GR}V{PIER_TOP}H{R}V{GR}"/>')
        d.add(f'<path class="fs" d="M{L - 7} {PIER_TOP}V{PIER_TOP - 9}H{R + 7}V{PIER_TOP}Z"/>')
        d.add(f'<path class="l" d="M{L - 7} {PIER_TOP}V{PIER_TOP - 9}H{R + 7}V{PIER_TOP}ZM{L - 4} {PIER_TOP - 9}L{p} {PIER_TOP - 26}L{R + 4} {PIER_TOP - 9}"/>')

    d.grade(48, W - 48, GR)

    # dimensions
    d.hdim(piers[0], piers[1], 140, '20&#8242;-0&#8243; O.C.', ext_from=PIER_TOP - 32)
    d.hdim(piers[1], piers[2], 140, '20&#8242;-0&#8243; O.C.', ext_from=PIER_TOP - 32)
    d.hdim(piers[2], piers[3], 140, '20&#8242;-0&#8243; O.C.', ext_from=PIER_TOP - 32)
    d.vdim(70, PANEL_TOP, GR, '8&#8242;-0&#8243;', ext_from=piers[0] - PW / 2 - 6)
    d.vdim(40, PIER_TOP - 26, GR, '9&#8242;-4&#8243;', ext_from=piers[0] - PW / 2 - 12)

    # notes
    d.leader(560, 182, 452, PIER_TOP - 16, 'CAST-STONE PIER CAP')
    d.leader(880, 196, 820, PANEL_TOP - 5, 'PRECAST COPING')
    d.leader(170, 300, 236, 362, 'MODULAR BRICK, RUNNING BOND', shoulder=16)
    d.leader(520, 458, 463, GR + 52, '&#216;12&#8243; DRILLED PIER')

    d.title_block(W, 496, 44, [
        (0.27, 'CONTRACTOR', 'LIGHTHOUSE MASONRY, INC.'),
        (0.33, 'DRAWING', 'SCREENING WALL &#183; TYPICAL ELEV.'),
        (0.16, 'LOCATION', 'PROSPER, TX'),
        (0.14, 'SCALE', '1/8&#8243; = 1&#8242;-0&#8243;'),
        (0.10, 'SHEET', 'A-201'),
    ])
    return d.svg(W, H)


def voussoirs(d, cx, cy, r1, r2, n, key_ext=14, key_w=1.35):
    """Semicircular ring of n voussoirs (n odd, keystone in the middle)."""
    step = math.pi / n
    for i in range(1, n):
        a = math.pi - i * step
        d.line(cx + r1 * math.cos(a), cy - r1 * math.sin(a), cx + r2 * math.cos(a), cy - r2 * math.sin(a), 'lt')
    # keystone: widened, projecting
    k = (n - 1) // 2
    a1 = math.pi - k * step + step * (key_w - 1) / 2
    a2 = math.pi - (k + 1) * step - step * (key_w - 1) / 2
    pts = [(cx + r1 * math.cos(a1), cy - r1 * math.sin(a1)), (cx + (r2 + key_ext) * math.cos(a1), cy - (r2 + key_ext) * math.sin(a1)),
           (cx + (r2 + key_ext) * math.cos(a2), cy - (r2 + key_ext) * math.sin(a2)), (cx + r1 * math.cos(a2), cy - r1 * math.sin(a2))]
    p = 'M' + 'L'.join(f'{f(x)} {f(y)}' for x, y in pts) + 'Z'
    d.add(f'<path class="fs" d="{p}"/><path class="l" d="{p}"/>')
    return pts


def plate_archway():
    W, H = 600, 640
    d = D()
    GR = 520
    cx, cy, r1, r2 = 248, 322, 96, 140
    X1, X2, TOP = 64, 432, 112
    # field coursing, masked around the ring and opening
    defs = (f'<defs><mask id="p2-m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>'
            f'<path d="M{cx - r2 - 3} {cy}A{r2 + 3} {r2 + 3} 0 0 1 {cx + r2 + 3} {cy}Z" fill="#000"/>'
            f'<rect x="{cx - r1}" y="{cy - 1}" width="{2 * r1}" height="{GR - cy + 1}" fill="#000"/>'
            f'<rect x="{cx - 34}" y="{cy - r2 - 20}" width="68" height="30" fill="#000"/>'
            f'</mask></defs>')
    d.add('<g mask="url(#p2-m)">')
    hatch_courses(d, X1, X2, TOP, GR, 8)
    head_joints(d, X1, X1 + 120, GR - 96, GR, 8, 24)
    head_joints(d, X2 - 120, X2, TOP, TOP + 64, 8, 24)
    d.add('</g>')
    # wall outline (break lines top/sides suggest a portion of a larger wall)
    d.add(f'<path class="lt" d="M{X1} {GR}V{TOP}M{X2} {GR}V{TOP}"/>')
    d.add(f'<path class="lt" d="M{X1} {TOP}H{cx - 20}l6 -10l8 20l6 -10H{X2}"/>')
    # arch ring + opening
    d.add(f'<path class="lb" d="M{cx - r2} {cy}A{r2} {r2} 0 0 1 {cx + r2} {cy}"/>')
    d.add(f'<path class="lb" d="M{cx - r1} {GR}V{cy}A{r1} {r1} 0 0 1 {cx + r1} {cy}V{GR}"/>')
    d.add(f'<path class="fl" d="M{cx - r1} {GR}V{cy}A{r1} {r1} 0 0 1 {cx + r1} {cy}V{GR}Z"/>')
    voussoirs(d, cx, cy, r1, r2, 19)
    # springline + centre mark
    d.line(cx - r2 - 20, cy, cx + r2 + 20, cy, 'cl')
    d.line(cx, cy - 12, cx, cy + 12, 'lt'); d.line(cx - 12, cy, cx + 12, cy, 'lt')
    # radius dimension
    a = math.radians(140)
    d.line(cx, cy, cx + r1 * math.cos(a), cy - r1 * math.sin(a), 'dm')
    d.text(cx + 0.55 * r1 * math.cos(a) - 6, cy - 0.55 * r1 * math.sin(a) - 8, 'R 3&#8242;-8&#8243;', 'td', 'middle', rot=-40)
    d.grade(36, W - 36, GR)
    # dims
    d.hdim(cx - r1, cx + r1, GR + 30, '7&#8242;-4&#8243; CLEAR', ext_from=GR + 4, above=False)
    d.vdim(36, cy, GR, '7&#8242;-0&#8243;', ext_from=X1 - 6)
    # notes
    d.leader(446, 150, cx + 14, cy - r2 - 6, 'CAST-STONE|KEYSTONE', shoulder=12)
    d.leader(446, 236, cx + 104, cy - 70, '19 VOUSSOIRS', shoulder=12)
    d.leader(446, 300, cx + r2 + 4, cy, 'SPRINGLINE', shoulder=12)
    d.leader(446, 420, X2 - 20, 440, 'KING-SIZE|BRICK', shoulder=12)
    d.title_block(W, 574, 44, [
        (0.48, 'DRAWING', 'FULL-ROUND ARCH &#183; ELEV.'),
        (0.32, 'LOCATION', 'SOUTHLAKE, TX'),
        (0.20, 'SHEET', 'A-302'),
    ])
    return d.svg(W, H, defs)


def plate_arcade():
    W, H = 600, 640
    d = D()
    GR = 520
    X1, X2 = 56, 544
    PAR, COR_T, COR_B = 112, 150, 176      # parapet top, cornice band
    bays = [137, 300, 463]                  # 16'-0" O.C.
    r1, r2, spring = 52, 72, 352
    defs = (f'<defs><mask id="p3-m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>'
            + ''.join(f'<path d="M{c - r2 - 2} {spring}A{r2 + 2} {r2 + 2} 0 0 1 {c + r2 + 2} {spring}Z" fill="#000"/>'
                      f'<rect x="{c - r1}" y="{spring - 1}" width="{2 * r1}" height="{GR - spring + 1}" fill="#000"/>'
                      f'<rect x="{c - 16}" y="{spring - r2 - 16}" width="32" height="26" fill="#000"/>' for c in bays)
            + '</mask></defs>')
    d.add('<g mask="url(#p3-m)">')
    hatch_courses(d, X1, X2, COR_B + 4, GR - 26, 8)
    head_joints(d, X1, X2, COR_B + 4, COR_B + 4 + 48, 8, 28, flemish=True)
    d.add('</g>')
    # base course (cast stone water table)
    d.add(f'<path class="fs" d="M{X1 - 4} {GR}V{GR - 26}H{X2 + 4}V{GR}Z"/>')
    d.add(f'<path class="l" d="M{X1 - 4} {GR}V{GR - 26}H{X2 + 4}V{GR}"/>')
    # facade outline + parapet + cornice with dentils
    d.add(f'<path class="lb" d="M{X1} {GR - 26}V{COR_B}M{X2} {GR - 26}V{COR_B}"/>')
    d.add(f'<path class="l" d="M{X1 + 6} {COR_T}V{PAR}H{X2 - 6}V{COR_T}"/>')
    hatch_courses(d, X1 + 6, X2 - 6, PAR + 4, COR_T, 8)
    d.add(f'<path class="fs" d="M{X1 + 2} {PAR}V{PAR - 7}H{X2 - 2}V{PAR}Z"/>')
    d.add(f'<path class="l" d="M{X1 + 2} {PAR}V{PAR - 7}H{X2 - 2}V{PAR}"/>')
    d.add(f'<path class="fs" d="M{X1 - 12} {COR_T}H{X2 + 12}V{COR_T + 12}H{X1 - 12}Z"/>')
    d.add(f'<path class="lb" d="M{X1 - 12} {COR_T}H{X2 + 12}V{COR_T + 12}H{X1 - 12}Z"/>')
    d.add(f'<path class="l" d="M{X1 - 4} {COR_T + 12}V{COR_B}H{X2 + 4}V{COR_T + 12}"/>')
    x = X1 + 2
    dents = []
    while x + 6 < X2:
        dents.append(f'M{x} {COR_T + 12}h6v8h-6Z')
        x += 14
    d.add(f'<path class="fs" d="{"".join(dents)}"/>')
    # bays
    for c in bays:
        d.add(f'<path class="fl" d="M{c - r1} {GR - 26}V{spring}A{r1} {r1} 0 0 1 {c + r1} {spring}V{GR - 26}Z"/>')
        d.add(f'<path class="lb" d="M{c - r1} {GR - 26}V{spring}A{r1} {r1} 0 0 1 {c + r1} {spring}V{GR - 26}"/>')
        d.add(f'<path class="l" d="M{c - r2} {spring}A{r2} {r2} 0 0 1 {c + r2} {spring}"/>')
        voussoirs(d, c, spring, r1, r2, 11, key_ext=8, key_w=1.5)
        # impost blocks
        for s in (-1, 1):
            xa, xb = sorted((c + s * r1, c + s * (r2 + 6)))
            d.add(f'<path class="fs" d="M{xa} {spring}h{xb - xa}v8h-{xb - xa}Z"/>')
            d.add(f'<path class="l" d="M{xa} {spring}h{xb - xa}v8h-{xb - xa}Z"/>')
        # storefront mullions
        d.add(f'<path class="lt" d="M{c} {spring - r1}V{GR - 26}M{c - r1} {spring + 64}H{c + r1}"/>')
        d.line(c, PAR - 30, c, PAR - 16, 'cl')
    d.grade(30, W - 30, GR)
    for a, b in zip(bays, bays[1:]):
        d.hdim(a, b, PAR - 34, '16&#8242;-0&#8243;')
    d.vdim(30, PAR - 7, GR, '24&#8242;-6&#8243;', ext_from=X1 - 16)
    d.leader(360, 248, 463 - 4, spring - r2 - 4, 'KEYSTONE', shoulder=12)
    d.leader(224, 244, 150, 204, 'FLEMISH BOND', shoulder=12)
    d.leader(330, 552, 390, GR - 13, 'LIMESTONE BASE', shoulder=12)
    d.title_block(W, 574, 44, [
        (0.48, 'DRAWING', 'RETAIL ARCADE &#183; FRONT ELEV.'),
        (0.32, 'LOCATION', 'FRISCO, TX'),
        (0.20, 'SHEET', 'A-401'),
    ])
    return d.svg(W, H, defs)


# =====================================================================
# LOGO MARK — simplified: 4 big courses, solid dome, one beam to the right
# Geometry in a 64 x 72 box (same as v1 so lockups don't shift).
# =====================================================================
CX = 22


def mark(ink, idp, beam_opacity='.92'):
    tl, tr, bl, br, ty, by = CX - 7, CX + 7, CX - 13, CX + 13, 24.6, 64
    courses = [(25.0, 33.2), (35.2, 43.4), (45.4, 53.6), (55.6, 64.0)]
    bricks = []
    for i, (y1, y2) in enumerate(courses):
        h = y2 - y1
        if i == 0:
            spans = [(0, 64)]
        elif i % 2 == 1:
            spans = [(0, CX - 1), (CX + 1, 64)]
        else:
            spans = [(0, CX - 6.5), (CX - 4.5, CX + 4.5), (CX + 6.5, 64)]
        for a, b in spans:
            bricks.append(f'<rect x="{f(a)}" y="{f(y1)}" width="{f(b - a)}" height="{f(h)}"/>')
    return (
        f'<path fill="#f5b841" fill-opacity="{beam_opacity}" d="M{CX + 6} 14.4 63 5v19.6L{CX + 6} 19.6Z"/>'
        f'<path fill="{ink}" d="M{CX - 0.9} 1.6h1.8v4h-1.8zM{CX - 8.4} 13.2a8.4 8.4 0 0 1 16.8 0Z"/>'
        f'<rect x="{CX - 6}" y="13.2" width="12" height="7" fill="#f5b841"/>'
        f'<path fill="{ink}" d="M{CX - 0.8} 13.2h1.6v7h-1.6zM{CX - 9.6} 20.2h19.2a.8.8 0 0 1 .8.8v2a.8.8 0 0 1-.8.8H{CX - 9.6}a.8.8 0 0 1-.8-.8v-2a.8.8 0 0 1 .8-.8Z"/>'
        f'<clipPath id="{idp}-tower"><path d="M{tl} {ty}H{tr}L{br} {by}H{bl}Z"/></clipPath>'
        f'<g fill="#c0532f" clip-path="url(#{idp}-tower)">' + ''.join(bricks) + '</g>'
        f'<path fill="{ink}" d="M{CX - 2.8} 64v-4.6a2.8 2.8 0 0 1 5.6 0V64Z"/>'
        f'<rect x="{CX - 15}" y="65.4" width="30" height="3.4" rx="1" fill="{ink}"/>'
    )


def logos():
    save('mark-symbol.svg', f'<symbol id="logo-mark" viewBox="0 0 64 72">{mark("currentColor", "lms")}</symbol>')
    for fn, key, ink, idp in (('logo.svg', 'light', '#0f1828', 'lml'), ('logo-reverse.svg', 'reverse', '#f4ecdc', 'lmr')):
        out = src(f'logo-{key}-head.svg') + f'<g>{mark(ink, idp)}</g>\n' + src(f'logo-{key}-text.svg')
        open(os.path.join(REPO, 'assets/img', fn), 'w').write(out)
    fav = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n<title>Lighthouse Masonry</title>\n'
           '<rect width="64" height="64" rx="14" fill="#0f1828"/>\n'
           f'<g transform="translate(3.4 2.6) scale(.86)">{mark("#f4ecdc", "lmf")}</g>\n</svg>\n')
    open(os.path.join(REPO, 'assets/img/favicon.svg'), 'w').write(fav)


# =====================================================================
# BEFORE / AFTER — weathered vs restored brick (viewBox 960 x 540)
# Same brick family and grey mortar as the hero wall.
# Rows: brick 72 x 22, head + bed joints 6. Row k: y = 3 + 28k, offset 0 / -39.
# =====================================================================
BA_W, BA_H = 960, 540
BA_TONES = ['#8c3b26', '#7f3624', '#96442b', '#773222', '#923f29', '#86392a', '#9a4a30']
BA_MORTAR = '#6e675d'


def _row_off(k):
    return 0 if k % 2 == 0 else -39


def _crack_points(rnd, xc, k0, steps, direction):
    """Stair-step through head and bed joints, jittered inside the 6-unit joint."""
    pts = []
    x, k = xc, k0
    for _ in range(steps):
        y0, y1 = 28 * k, 28 * k + 28
        for t in (0, 0.35, 0.7):
            pts.append((x + rnd.uniform(-1.3, 1.3), y0 + t * 28 + rnd.uniform(-1.5, 1.5)))
        x2 = x + 39 * direction
        for t in (0, 0.5):
            pts.append((x + (x2 - x) * t + rnd.uniform(-1.5, 1.5), y1 + rnd.uniform(-1.2, 1.2)))
        x, k = x2, k + 1
    pts.append((x + rnd.uniform(-1, 1), 28 * k + rnd.uniform(-1, 1)))
    return pts


def _crack_joints(xc, k0, steps, direction):
    """Joint rectangles the crack runs through (repointed on the after side)."""
    r = []
    x, k = xc, k0
    for _ in range(steps):
        r.append((x - 3, 28 * k + 3, 6, 22))
        x2 = x + 39 * direction
        r.append((min(x, x2) - 3, 28 * k + 25, 45, 6))
        x, k = x2, k + 1
    return r


def before_after():
    rnd = random.Random(21)
    bricks = []
    rows = BA_H // 28 + 1
    for k in range(rows):
        y = 3 + 28 * k
        x = _row_off(k)
        while x < BA_W:
            bricks.append(f'<rect x="{x}" y="{y}" width="72" height="22" fill="{rnd.choice(BA_TONES)}"/>')
            x += 78
    # shared per-brick texture, tile = 2 bricks x 2 rows
    tr = random.Random(4)
    tex = []
    faces = [(0, 3), (78, 3), (-39, 31), (39, 31), (117, 31)]
    for (bx, by) in faces:
        tex.append(f'<rect x="{bx}" y="{by}" width="72" height="1.5" fill="#fff" fill-opacity=".1"/>')
        tex.append(f'<rect x="{bx}" y="{by + 19.5}" width="72" height="2.5" fill="#000" fill-opacity=".18"/>')
        for _ in range(7):
            sx, sy, s = bx + 3 + tr.random() * 64, by + 3 + tr.random() * 15, 1 + tr.random() * 1.8
            dark = tr.random() < 0.7
            tex.append(f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(s)}" height="{f(s * .8)}" fill="{"#000" if dark else "#fff"}" fill-opacity="{.16 if dark else .09}"/>')

    # cracks: one long run from the top centre, one shorter on the left
    cracks = [(_row_off(1) + 75 + 78 * 5, 1, 7, -1), (_row_off(10) + 75 + 78 * 3, 10, 4, -1)]
    crack_paths = []
    repoint = []
    for xc, k0, steps, dirn in cracks:
        pts = _crack_points(rnd, xc, k0, steps, dirn)
        for a, b in zip(pts, pts[1:]):
            w = rnd.uniform(2.0, 3.4)
            crack_paths.append(f'<path d="M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}" stroke-width="{w:.1f}"/>')
        for (x, y, w, h) in _crack_joints(xc, k0, steps, dirn):
            repoint.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>')

    # efflorescence: chalky salt bloom under bed joints, heavier toward the base,
    # with the odd thin run where water carried it down the face
    efflo = []
    for k in range(8, rows):
        yb = 28 * k + 31
        weight = (k - 8) / (rows - 8)
        for _ in range(int(1 + weight * 5)):
            x0 = rnd.uniform(-20, BA_W - 30)
            w = rnd.uniform(24, 110)
            depth = rnd.uniform(5, 20) * (0.6 + 0.6 * weight)
            pts = [(x0, yb - 2), (x0 + w, yb - 2)]
            steps = rnd.randint(4, 7)
            for t in range(1, steps):
                px = x0 + w * (1 - t / steps) + rnd.uniform(-4, 4)
                edge = min(t, steps - t) / (steps / 2)          # deeper toward the middle
                pts.append((px, yb + depth * edge * rnd.uniform(0.4, 1.1)))
            d = 'M' + 'L'.join(f'{f(x)} {f(y)}' for x, y in pts) + 'Z'
            efflo.append(f'<path d="{d}" opacity="{rnd.uniform(.35, .6):.2f}"/>')
            if rnd.random() < 0.35:   # a run down the brick face
                rx = x0 + rnd.uniform(0.2, 0.8) * w
                efflo.append(f'<rect x="{f(rx)}" y="{yb}" width="{rnd.uniform(1.5, 3):.1f}" height="{rnd.uniform(14, 34):.0f}" opacity="{rnd.uniform(.3, .5):.2f}"/>')
        for _ in range(int(weight * 3)):
            x0 = rnd.uniform(0, BA_W - 60)
            efflo.append(f'<rect x="{f(x0)}" y="{yb - 6}" width="{f(rnd.uniform(30, 110))}" height="6" opacity="{rnd.uniform(.3, .5):.2f}"/>')

    # spalled brick (face popped off, rough core showing)
    sx, sy = _row_off(14) + 78 * 7, 3 + 28 * 14
    spall = (f'<path d="M{sx + 8} {sy + 4}l14 -2 10 3 18 -1 8 6 -4 9 -12 3 -16 -1 -12 2 -7 -6Z" fill="#4e2419"/>'
             f'<path d="M{sx + 8} {sy + 4}l14 -2 10 3 18 -1" fill="none" stroke="#c98a6a" stroke-opacity=".5" stroke-width="1.2"/>')

    # water beads: one small cluster on the sealed side
    beads = []
    for (bx, by, r) in [(742, 262, 7.5), (761, 270, 5.2), (729, 279, 4.6), (752, 288, 6.2), (772, 255, 4), (724, 260, 3.4), (785, 276, 3)]:
        beads.append(f'<ellipse cx="{bx + 0.8}" cy="{by + r * 0.55}" rx="{r}" ry="{r * 0.7:.1f}" fill="#2a120b" fill-opacity=".35"/>'
                     f'<ellipse cx="{bx}" cy="{by}" rx="{r}" ry="{r * 0.82:.1f}" fill="url(#ba-bead)"/>'
                     f'<circle cx="{bx - r * 0.35:.1f}" cy="{by - r * 0.35:.1f}" r="{r * 0.28:.1f}" fill="#fff" fill-opacity=".9"/>')

    defs = (
        '<svg class="ba__defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
        '<pattern id="ba-tex" width="156" height="56" patternUnits="userSpaceOnUse">' + ''.join(tex) + '</pattern>'
        f'<g id="ba-field"><rect width="{BA_W}" height="{BA_H}" fill="{BA_MORTAR}"/>' + ''.join(bricks)
        + f'<rect width="{BA_W}" height="{BA_H}" fill="url(#ba-tex)"/></g>'
        '<filter id="ba-dull"><feColorMatrix type="saturate" values=".72"/><feComponentTransfer>'
        '<feFuncR type="linear" slope=".86"/><feFuncG type="linear" slope=".86"/><feFuncB type="linear" slope=".84"/></feComponentTransfer></filter>'
        '<filter id="ba-grime" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".01 .05" numOctaves="3" seed="4"/>'
        '<feColorMatrix values="0 0 0 0 .12  0 0 0 0 .1  0 0 0 0 .08  0 0 0 -2.2 1.35"/></filter>'
        '<filter id="ba-soft" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.4"/></filter>'
        '<linearGradient id="ba-efflo-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3efe6"/><stop offset=".55" stop-color="#ece6da" stop-opacity=".7"/><stop offset="1" stop-color="#e6e0d4" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="ba-damp" x1="0" y1="0" x2="0" y2="1"><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#efe9de" stop-opacity=".16"/></linearGradient>'
        '<linearGradient id="ba-sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".12"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<radialGradient id="ba-bead" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".6" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity=".3"/></radialGradient>'
        '</defs></svg>')

    vb = f'viewBox="0 0 {BA_W} {BA_H}" preserveAspectRatio="xMidYMid slice" focusable="false"'
    after = (f'<svg {vb}><use href="#ba-field"/>'
             f'<g fill="#756d62">{"".join(repoint)}</g>'
             f'<rect width="{BA_W}" height="{BA_H}" fill="url(#ba-sheen)"/>' + ''.join(beads) + '</svg>')
    before = (f'<svg {vb}><use href="#ba-field" filter="url(#ba-dull)"/>'
              f'<rect width="{BA_W}" height="{BA_H}" fill="#2a1d16" opacity=".14"/>'
              f'<rect width="{BA_W}" height="{BA_H}" filter="url(#ba-grime)" opacity=".42"/>'
              f'<rect width="{BA_W}" height="{BA_H}" fill="url(#ba-damp)"/>'
              f'<g fill="url(#ba-efflo-g)" filter="url(#ba-soft)">{"".join(efflo)}</g>'
              + spall +
              f'<g fill="none" stroke="#150e0b" stroke-linecap="round" stroke-linejoin="round">{"".join(crack_paths)}</g></svg>')

    return f'''    <div class="ba" data-ba data-reveal style="--pos: 50%">
      {defs}
      <div class="ba__layer ba__layer--after" aria-hidden="true">
        {after}
        <span class="ba__tag ba__tag--after">After</span>
      </div>
      <div class="ba__layer ba__layer--before" aria-hidden="true">
        <div class="ba__before-inner">
          {before}
          <span class="ba__tag ba__tag--before">Before</span>
        </div>
      </div>
      <div class="ba__handle" aria-hidden="true"><span><svg class="icon" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="m9 6-6 6 6 6m6-12 6 6-6 6"/></svg></span></div>
      <label class="visually-hidden" for="ba-range">Compare before and after: how much of the before illustration is shown</label>
      <input class="ba__range" id="ba-range" type="range" min="0" max="100" value="50" step="1" aria-valuetext="50% before, 50% after">
    </div>'''

if __name__ == '__main__':
    for name in ('lighthouse.svg', 'map.svg', 'icons.txt', 'i-google.txt', 'svc-symbols.txt'):
        shutil.copy(os.path.join(SRC, name), os.path.join(OUT, name))
    hero_wall()
    save('ba.html', before_after())
    save('plate-screening.svg', plate_screening())
    save('plate-archway.svg', plate_archway())
    save('plate-arcade.svg', plate_arcade())
    logos()
    print('ok', sorted(os.listdir(OUT)))
