#!/usr/bin/env python3
"""THE DAY IN ONE PICTURE -- Saturday 21 November 2026.

Draws a newspaper front page that sums up the world's news of Saturday
21 November 2026 in a single 1024x1024 image:

  * LEAD: Russian missiles and a drone came down in Poland during a mass
    strike on Ukraine -- Poland calls it a deliberate provocation, NATO
    a grave violation of its airspace; Kyiv's bridges were hit and three
    utility workers killed.
  * The World Court (ICJ) rules Myanmar committed genocide against the
    Rohingya.
  * Trump-Xi-Putin trilateral summit in Shenzhen ends with pledges but
    no breakthroughs.
  * S&P 500 and Dow enter correction as the AI selloff deepens (-3.7%).
  * UK and EU sign landmark post-Brexit deals.

Python 3.13, Pillow only, no network. Deterministic: the same bytes are
written on every run. Output: $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png).
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- setup

SS = 2                      # supersample factor for clean edges
W = H = 1024                # final image size

PAPER = (246, 239, 222)     # newsprint cream
PANEL = (251, 247, 235)     # lighter box cream
INK = (24, 21, 17)          # ink black
RED = (176, 28, 36)         # the one red accent
DARK_RED = (128, 20, 28)
GRAY = (96, 89, 76)
FAINT = (203, 193, 168)
WATER = (205, 217, 221)
LAND = (240, 233, 208)
POL_FILL = (243, 198, 174)  # Poland, washed red
UKR_FILL = (229, 215, 173)  # Ukraine, deeper parchment
NAVY = (31, 55, 99)
GOLD = (228, 172, 30)
SKY_BLUE = (64, 96, 158)

# ---------------------------------------------------------------- fonts

_FONT_FILES = {
    "serif_b": ["DejaVuSerif-Bold.ttf"],
    "serif": ["DejaVuSerif.ttf"],
    "serif_i": ["DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf",
                "DejaVuSerif.ttf"],
    "sans_b": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "sans": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
}
_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts",
]
_font_cache = {}


def font(kind, size):
    """Best available font for `kind` at `size` points (final-image px).

    Defensive chain: known system paths first, then Pillow's bundled
    default; any failure degrades instead of crashing the render.
    """
    px = max(4, int(round(size * SS)))
    key = (kind, px)
    if key in _font_cache:
        return _font_cache[key]
    f = None
    for name in _FONT_FILES.get(kind, _FONT_FILES["sans"]):
        for d in _FONT_DIRS:
            try:
                f = ImageFont.truetype(os.path.join(d, name), px)
                break
            except Exception:
                f = None
        if f is not None:
            break
    if f is None:
        try:
            f = ImageFont.load_default(px)
        except Exception:
            try:
                f = ImageFont.load_default()
            except Exception:
                f = None
    _font_cache[key] = f
    return f

# ------------------------------------------------------------ draw utils
# All coordinates below are in final-image (1024) units; helpers scale.


def rect(d, box, **kw):
    d.rectangle([box[0] * SS, box[1] * SS, box[2] * SS, box[3] * SS], **kw)


def line(d, pts, fill=INK, w=1.0, joint="curve"):
    d.line([(x * SS, y * SS) for x, y in pts], fill=fill,
           width=max(1, int(round(w * SS))), joint=joint)


def poly(d, pts, **kw):
    d.polygon([(x * SS, y * SS) for x, y in pts], **kw)


def ell(d, box, **kw):
    d.ellipse([box[0] * SS, box[1] * SS, box[2] * SS, box[3] * SS], **kw)


def txt(d, x, y, s, f, fill=INK, anchor="la"):
    d.text((x * SS, y * SS), s, font=f, fill=fill, anchor=anchor)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return (b[2] - b[0]) / SS


def fit_font(d, s, kind, max_w, start, min_size=10):
    """Largest font of `kind`, at or below `start`, that fits `max_w`."""
    size = start
    while size > min_size:
        f = font(kind, size)
        if tw(d, s, f) <= max_w:
            return f, size
        size -= 1
    return font(kind, min_size), min_size


def wrap(d, s, f, max_w):
    """Greedy word wrap; returns a list of lines."""
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if tw(d, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def star_pts(cx, cy, r_out, r_in, n=5, rot=-90.0):
    pts = []
    for i in range(2 * n):
        ang = math.radians(rot + i * 180.0 / n)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def burst(d, cx, cy, r, fill=RED):
    pts = []
    for i in range(16):
        ang = i * math.pi / 8.0
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    poly(d, pts, fill=fill)


def bezier(p0, p1, p2, n=44):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts

# ---------------------------------------------------------------- icons


def icon_scales(d, cx, cy):
    """Scales of justice for the World Court story."""
    line(d, [(cx, cy - 30), (cx, cy + 25)], INK, 3.4)
    line(d, [(cx - 27, cy - 21), (cx + 27, cy - 21)], INK, 3.4)
    ell(d, [cx - 4, cy - 36, cx + 4, cy - 28], fill=INK)
    for sx in (-27, 27):
        px = cx + sx
        line(d, [(px, cy - 21), (px - 11, cy + 1)], INK, 1.6)
        line(d, [(px, cy - 21), (px + 11, cy + 1)], INK, 1.6)
        d.arc([(px - 13) * SS, (cy - 3) * SS, (px + 13) * SS,
               (cy + 15) * SS], start=0, end=180, fill=INK,
              width=max(1, int(2.2 * SS)))
        line(d, [(px - 13, cy + 1), (px + 13, cy + 1)], INK, 1.6)
    line(d, [(cx - 9, cy + 25), (cx + 9, cy + 25)], INK, 3.0)
    line(d, [(cx - 16, cy + 31), (cx + 16, cy + 31)], INK, 3.4)


def icon_flags(d, x, y):
    """Three small flags on poles: USA, China, Russia."""
    fw, fh = 20, 15
    for i in range(3):
        px = x + i * 23
        line(d, [(px, y), (px, y + 52)], INK, 2.0)
        ell(d, [px - 2, y - 4, px + 2, y], fill=INK)
        bx, by = px + 1.5, y + 1
        if i == 0:      # USA: stripes + blue canton
            rect(d, [bx, by, bx + fw, by + fh], fill=(250, 248, 242),
                 outline=INK, width=int(1.2 * SS))
            for r_ in range(0, 7, 2):
                rect(d, [bx, by + r_ * fh / 7, bx + fw,
                         by + (r_ + 1) * fh / 7], fill=RED)
            rect(d, [bx, by, bx + fw * 0.45, by + fh * 0.54], fill=NAVY)
            for gy in range(3):
                for gx in range(3):
                    dx = bx + 2 + gx * 3.2
                    dy = by + 2 + gy * 2.6
                    ell(d, [dx - 0.8, dy - 0.8, dx + 0.8, dy + 0.8],
                        fill=(255, 255, 255))
        elif i == 1:    # China: red field, gold stars
            rect(d, [bx, by, bx + fw, by + fh], fill=(206, 32, 40),
                 outline=INK, width=int(1.2 * SS))
            poly(d, star_pts(bx + 6, by + 5.5, 3.6, 1.5), fill=GOLD)
            for dx, dy in ((11.5, 2.6), (13.2, 5.6), (11.5, 8.6)):
                ell(d, [bx + dx - 1.1, by + dy - 1.1, bx + dx + 1.1,
                        by + dy + 1.1], fill=GOLD)
        else:           # Russia: white / blue / red bands
            rect(d, [bx, by, bx + fw, by + fh], outline=INK,
                 width=int(1.2 * SS))
            rect(d, [bx, by, bx + fw, by + fh / 3], fill=(250, 248, 242))
            rect(d, [bx, by + fh / 3, bx + fw, by + 2 * fh / 3],
                 fill=SKY_BLUE)
            rect(d, [bx, by + 2 * fh / 3, bx + fw, by + fh], fill=RED)


def icon_chart(d, x, y):
    """Falling market line for the Wall Street story."""
    line(d, [(x + 4, y + 2), (x + 4, y + 40)], GRAY, 1.6)
    line(d, [(x + 4, y + 40), (x + 76, y + 40)], GRAY, 1.6)
    pts = [(x + 6, y + 8), (x + 19, y + 14), (x + 29, y + 10),
           (x + 41, y + 22), (x + 51, y + 19), (x + 63, y + 31),
           (x + 72, y + 36)]
    line(d, pts, RED, 3.2)
    ang = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    hx, hy = pts[-1]
    head = [(hx, hy),
            (hx - 8 * math.cos(ang - 0.42), hy - 8 * math.sin(ang - 0.42)),
            (hx - 8 * math.cos(ang + 0.42), hy - 8 * math.sin(ang + 0.42))]
    poly(d, head, fill=RED)
    f = font("sans_b", 19)
    txt(d, x + 40, y + 46, "-3.7%", f, RED, anchor="ma")


def icon_uk_eu(d, cx, cy):
    """Overlapping discs: a simplified Union Jack and the EU star ring."""
    r = 25
    c2 = (cx + 17, cy)      # EU disc (right, behind)
    ell(d, [c2[0] - r, c2[1] - r, c2[0] + r, c2[1] + r], fill=NAVY,
        outline=PAPER, width=int(2.5 * SS))
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        sx, sy = c2[0] + 15.5 * math.cos(ang), c2[1] + 15.5 * math.sin(ang)
        poly(d, star_pts(sx, sy, 2.9, 1.25), fill=GOLD)
    c1 = (cx - 17, cy)      # UK disc (left, in front)
    ell(d, [c1[0] - r, c1[1] - r, c1[0] + r, c1[1] + r], fill=NAVY,
        outline=PAPER, width=int(2.5 * SS))
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        line(d, [(c1[0], c1[1]), (c1[0] + dx * r * 0.68,
                                  c1[1] + dy * r * 0.68)],
             (245, 245, 245), 4.6)
    line(d, [(c1[0] - r * 0.92, c1[1]), (c1[0] + r * 0.92, c1[1])],
         (245, 245, 245), 8.5)
    line(d, [(c1[0], c1[1] - r * 0.92), (c1[0], c1[1] + r * 0.92)],
         (245, 245, 245), 8.5)
    line(d, [(c1[0] - r * 0.92, c1[1]), (c1[0] + r * 0.92, c1[1])],
         RED, 4.6)
    line(d, [(c1[0], c1[1] - r * 0.92), (c1[0], c1[1] + r * 0.92)],
         RED, 4.6)
    ell(d, [c1[0] - r, c1[1] - r, c1[0] + r, c1[1] + r], outline=INK,
        width=int(1.6 * SS))
    ell(d, [c2[0] - r, c2[1] - r, c2[0] + r, c2[1] + r], outline=INK,
        width=int(1.6 * SS))

# ------------------------------------------------------------------ map

# Stylised country outlines as (longitude, latitude) pairs.
POLAND = [(14.1, 53.9), (14.6, 54.3), (16.0, 54.6), (17.5, 54.8),
          (18.9, 54.9), (19.6, 54.5), (20.9, 54.4), (22.0, 54.3),
          (23.2, 54.1), (23.9, 53.5), (24.1, 52.6), (24.3, 51.7),
          (23.9, 50.9), (24.0, 50.2), (22.9, 49.9), (22.0, 49.6),
          (21.0, 49.4), (20.2, 49.3), (19.6, 49.5), (19.0, 49.7),
          (18.4, 49.9), (17.8, 50.1), (17.0, 50.3), (16.2, 50.6),
          (15.4, 50.9), (14.9, 51.3), (14.4, 51.8), (14.2, 52.4),
          (14.0, 53.0)]
UKRAINE = [(22.1, 50.4), (22.9, 51.1), (24.0, 51.6), (25.6, 51.9),
           (27.5, 52.0), (29.5, 52.2), (31.5, 52.3), (32.6, 52.4),
           (33.8, 51.9), (35.2, 51.9), (36.5, 51.3), (37.8, 50.6),
           (39.0, 49.9), (39.9, 49.2), (40.1, 48.4), (39.7, 47.6),
           (38.6, 47.0), (37.2, 46.7), (35.6, 46.5), (34.0, 46.3),
           (32.6, 46.2), (31.6, 46.3), (30.8, 46.4), (30.2, 45.9),
           (29.7, 45.3), (28.9, 45.6), (27.9, 47.6), (27.0, 48.2),
           (26.2, 48.4), (25.2, 48.1), (24.3, 47.9), (23.4, 48.6),
           (22.7, 49.3), (22.2, 49.8)]
CRIMEA = [(32.6, 46.35), (33.6, 45.7), (34.8, 45.25), (35.6, 44.95),
          (35.4, 44.5), (34.3, 44.4), (33.4, 44.5), (32.7, 45.3),
          (32.5, 45.9)]

MX, MY, KX, KY = 92.0, 432.0, 15.5, 17.6   # projection constants


def proj(lon, lat):
    return (MX + (lon - 12.5) * KX, MY + (55.8 - lat) * KY)


def nato_badge(d, cx, cy, r):
    ell(d, [cx - r, cy - r, cx + r, cy + r], fill=PAPER, outline=INK,
        width=int(2.2 * SS))
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = r * 0.74 if i % 2 == 0 else r * 0.30
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    poly(d, pts, fill=NAVY)
    ell(d, [cx - 2.6, cy - 2.6, cx + 2.6, cy + 2.6], fill=PAPER)


def drone(d, cx, cy):
    for dx, dy in ((-8, -8), (8, -8), (-8, 8), (8, 8)):
        line(d, [(cx, cy), (cx + dx, cy + dy)], INK, 1.7)
        ell(d, [cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3],
            outline=INK, width=int(1.5 * SS))
    rect(d, [cx - 3.4, cy - 3.4, cx + 3.4, cy + 3.4], fill=INK)
    ell(d, [cx - 1.4, cy - 1.4, cx + 1.4, cy + 1.4], fill=RED)


def draw_map(d):
    """The lead visual: Poland and Ukraine, strikes arcing in."""
    x0, y0, x1, y1 = 40, 412, 596, 644
    rect(d, [x0, y0, x1, y1], fill=LAND, outline=INK,
         width=int(2.2 * SS))
    # Black Sea (bottom) and a Baltic hint (top left)
    poly(d, [proj(28.5, 46.4), proj(31.0, 46.6), proj(34.0, 46.3),
             proj(37.0, 46.7), proj(40.0, 47.0), proj(41.5, 46.6),
             proj(41.5, 43.8), proj(28.5, 43.8)], fill=WATER)
    poly(d, [proj(12.5, 55.8), proj(19.5, 55.8), proj(19.0, 54.6),
             proj(16.0, 54.3), proj(14.0, 53.8), proj(12.5, 54.2)],
         fill=WATER)
    # Countries
    poly(d, [proj(*p) for p in UKRAINE], fill=UKR_FILL, outline=INK,
         width=int(2 * SS))
    poly(d, [proj(*p) for p in CRIMEA], fill=UKR_FILL, outline=INK,
         width=int(1.4 * SS))
    poly(d, [proj(*p) for p in POLAND], fill=POL_FILL, outline=INK,
         width=int(2.2 * SS))
    # Missile trails: from Russia, arcing west into Poland and Kyiv
    origin = proj(39.6, 52.6)
    imp1, imp2 = proj(23.1, 51.15), proj(22.55, 50.65)
    kyiv = proj(30.52, 50.45)
    for target, lift in ((imp1, 96), (imp2, 118), (kyiv, 74)):
        ctrl = ((origin[0] + target[0]) / 2, min(origin[1], target[1]) - lift)
        pts = bezier(origin, ctrl, target)
        line(d, pts, (243, 178, 168), 6.5)
        line(d, pts, RED, 3.0)
        ang = math.atan2(pts[-1][1] - pts[-4][1], pts[-1][0] - pts[-4][0])
        hx, hy = pts[-1]
        poly(d, [(hx, hy),
                 (hx - 9 * math.cos(ang - 0.45),
                  hy - 9 * math.sin(ang - 0.45)),
                 (hx - 9 * math.cos(ang + 0.45),
                  hy - 9 * math.sin(ang + 0.45))], fill=DARK_RED)
    burst(d, imp1[0], imp1[1], 13)
    burst(d, imp2[0], imp2[1], 10.5)
    burst(d, kyiv[0], kyiv[1], 9, DARK_RED)
    dr = proj(24.35, 51.95)
    drone(d, dr[0], dr[1])
    # Cities
    wa = proj(21.01, 52.23)
    for (px, py), r_ in ((wa, 3.4), (kyiv, 3.4)):
        ell(d, [px - r_, py - r_, px + r_, py + r_], fill=INK)
    f_city = font("sans_b", 12.5)
    txt(d, wa[0] - 7, wa[1] - 6, "Warsaw", f_city, INK, anchor="ra")
    txt(d, kyiv[0] + 14, kyiv[1] + 5, "Kyiv", f_city, INK, anchor="la")
    # Country labels
    f_c = font("sans_b", 16)
    p = proj(17.9, 50.75)
    txt(d, p[0], p[1], "POLAND", f_c, DARK_RED, anchor="ma")
    p = proj(32.8, 48.3)
    txt(d, p[0], p[1], "UKRAINE", f_c, INK, anchor="ma")
    f_s = font("sans_b", 12)
    p = proj(39.9, 50.6)
    txt(d, p[0], p[1], "RUSSIA", f_s, GRAY, anchor="ma")
    f_sea = font("serif_i", 11.5)
    p = proj(33.6, 45.15)
    txt(d, p[0], p[1], "Black Sea", f_sea, GRAY, anchor="ma")
    # Impact callout
    f_i = font("sans_b", 11)
    txt(d, 148, 558, "MISSILES + DRONE DOWN", f_i, RED,
        anchor="la")
    line(d, [(258, 554), (imp2[0] + 3, imp2[1] + 9)], RED, 1.4)
    # Legend
    lx, ly = 452, 622
    line(d, [(lx, ly), (lx + 26, ly)], RED, 3.0)
    txt(d, lx + 32, ly - 6, "MISSILE TRAILS", font("sans_b", 9.5), GRAY,
        anchor="la")
    # NATO badge on the frame corner
    nato_badge(d, 68, 442, 23)
    txt(d, 68, 470, "NATO", font("sans_b", 10.5), NAVY, anchor="ma")

# --------------------------------------------------------------- panels


def panel(d, x, y, w, h, kicker, head_lines, summary, icon):
    rect(d, [x, y, x + w, y + h], fill=PANEL, outline=FAINT,
         width=int(1.2 * SS))
    line(d, [(x, y), (x + w, y)], INK, 3.2)
    txt(d, x + 14, y + 9, kicker, font("sans_b", 12.5), RED, anchor="la")
    tx = x + 116
    tw_max = x + w - tx - 12
    sizes = []
    for s in head_lines:
        _, sz = fit_font(d, s, "serif_b", tw_max, 24, 15)
        sizes.append(sz)
    hs = min(sizes)
    hf = font("serif_b", hs)
    hy = y + 33
    for s in head_lines:
        txt(d, tx, hy, s, hf, INK, anchor="la")
        hy += hs + 5
    sf = font("serif", 16)
    sy = hy + 3
    for ln in wrap(d, summary, sf, tw_max):
        txt(d, tx, sy, ln, sf, (52, 48, 40), anchor="la")
        sy += 20.5
    icon(d, x, y, h)


# ---------------------------------------------------------------- build


def build():
    img = Image.new("RGB", (W * SS, H * SS), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead
    line(d, [(40, 20), (984, 20)], INK, 3.4)
    line(d, [(40, 26), (984, 26)], INK, 1.1)
    txt(d, 512, 33, "ALL THE WORLD'S NEWS · ONE DAY · ONE PAGE",
        font("sans_b", 13), GRAY, anchor="ma")
    tf, _ = fit_font(d, "THE DAY IN ONE PICTURE", "serif_b", 944, 92, 40)
    txt(d, 512, 52, "THE DAY IN ONE PICTURE", tf, INK, anchor="ma")
    line(d, [(40, 128), (984, 128)], INK, 4.2)
    txt(d, 40, 139, "LATE EDITION", font("sans_b", 12.5), INK, anchor="la")
    txt(d, 512, 134, "SATURDAY 21 NOVEMBER 2026", font("serif_b", 30),
        INK, anchor="ma")
    txt(d, 984, 139, "FIVE STORIES · ONE PAGE", font("sans_b", 12.5), INK,
        anchor="ra")
    line(d, [(40, 170), (984, 170)], INK, 1.1)
    line(d, [(40, 175), (984, 175)], INK, 4.2)

    # ---- lead story
    rect(d, [40, 190, 984, 218], fill=RED)
    txt(d, 54, 196, "★ LEAD STORY — WAR IN EUROPE", font("sans_b", 14.5),
        (255, 250, 240), anchor="la")
    txt(d, 970, 196, "NATO'S EASTERN FLANK", font("sans_b", 14.5),
        (255, 250, 240), anchor="ra")
    hf, _ = fit_font(d, "MISSILES FALL ON NATO SOIL", "serif_b", 944, 66, 30)
    txt(d, 512, 228, "MISSILES FALL ON NATO SOIL", hf, INK, anchor="ma")
    df, _ = fit_font(
        d, "Russia's strike on Ukraine spills over NATO's border — the "
           "alliance condemns a grave violation of its airspace.",
        "serif_i", 944, 19, 13)
    txt(d, 512, 306, "Russia's strike on Ukraine spills over NATO's "
        "border — the alliance condemns a grave violation of its "
        "airspace.", df, (52, 48, 40), anchor="ma")

    draw_map(d)

    # ---- what happened (side panel of the lead)
    sx = 612
    txt(d, sx + 14, 420, "WHAT HAPPENED", font("sans_b", 16), RED,
        anchor="la")
    line(d, [(sx + 14, 446), (970, 446)], FAINT, 1.4)
    bullets = [
        "Russian missiles and a drone came down in eastern Poland "
        "during the mass strike on Ukraine.",
        "Poland calls it a deliberate provocation; NATO condemns a "
        "grave violation of allied airspace.",
        "In Kyiv, bridges were hit and three utility workers "
        "were killed.",
    ]
    bf = font("serif", 16)
    by = 456
    for b in bullets:
        txt(d, sx + 14, by, "•", bf, RED, anchor="la")
        for ln in wrap(d, b, bf, 326):
            txt(d, sx + 30, by, ln, bf, (52, 48, 40), anchor="la")
            by += 21.5
        by += 7

    # ---- secondary stories, 2 x 2
    def ic_scales(dd, x, y, h):
        icon_scales(dd, x + 58, y + h / 2 + 4)

    def ic_flags(dd, x, y, h):
        icon_flags(dd, x + 20, y + h / 2 - 26)

    def ic_chart(dd, x, y, h):
        icon_chart(dd, x + 16, y + h / 2 - 34)

    def ic_uk_eu(dd, x, y, h):
        icon_uk_eu(dd, x + 58, y + h / 2 + 4)

    panel(d, 40, 666, 460, 148, "LAW · THE HAGUE",
          ["WORLD COURT: MYANMAR", "COMMITTED GENOCIDE"],
          "The ICJ rules Myanmar's campaign against the Rohingya was "
          "genocide — a historic verdict at The Hague.",
          ic_scales)
    panel(d, 524, 666, 460, 148, "DIPLOMACY · SHENZHEN",
          ["TRUMP, XI & PUTIN SUMMIT", "ENDS WITHOUT BREAKTHROUGH"],
          "The trilateral summit closes with pledges of cooperation "
          "between the three powers — but no breakthroughs.",
          ic_flags)
    panel(d, 40, 830, 460, 148, "MARKETS · NEW YORK",
          ["WALL STREET SLIDES", "INTO CORRECTION"],
          "The S&P 500 and the Dow enter correction as the AI selloff "
          "deepens; stocks fall about 3.7% on the day.",
          ic_chart)
    panel(d, 524, 830, 460, 148, "EUROPE · LONDON–BRUSSELS",
          ["UK & EU SIGN LANDMARK", "POST-BREXIT DEALS"],
          "London and Brussels agree landmark deals on food trade, "
          "carbon markets and youth mobility.",
          ic_uk_eu)

    # ---- footer
    line(d, [(40, 990), (984, 990)], INK, 1.6)
    txt(d, 512, 996, "Drawn from the day's wire reports — every story "
        "first reported on Saturday 21 November 2026",
        font("sans", 12), GRAY, anchor="ma")

    return img.resize((W, H), Image.LANCZOS)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    build().save(os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
