#!/usr/bin/env python3
"""THE MONDAY LEDGER, v3 — the whole of Monday 23 November 2026 on one page.

Third build for make.fun news-image-20261123. v1 was drawn from Monday
morning's wires and v2 from Monday's early afternoon; both therefore missed
what the day still had in store. This page is drawn on Tuesday, with Monday
complete in every time zone, and it carries the day whole: FIFA's Zurich
Congress as a confirmed result rather than a sitting, Wall Street's historic
rebound (absent from both earlier pages, whose sweeps closed before New York
opened), and the final Monday figures for the stories the day was still
writing at v2's render — the Dymer toll, the Hormuz count, the Delta
recovery. What changed, item by item, is documented in news-notes.md.

The grammar is the broadsheet of the ni22 winner's family, at full strength:
count band, date masthead, strapline, six-figure stat strip, region bar, UTC
timeline, three illustrated heroes, twelve pictured cards, a dotted world
map pinned to the story numbers, a numbered ALSO list, a DATE CHECK box, a
sources line with a certainty legend, and a ledger close. Drawn at
2048x2048, downscaled to 1024x1024 with Lanczos (2x supersampling).
Deterministic: seeded randomness only, no clock, no network.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS = 2
FINAL = 1024
CANVAS = FINAL * SS
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

NOTO_DIR = "/usr/share/fonts/truetype/noto"
DEJA_DIR = "/usr/share/fonts/truetype/dejavu"


def _font(path, size):
    return ImageFont.truetype(path, int(round(size * SS)))


def display(size):
    return _font(f"{NOTO_DIR}/NotoSerifDisplay-Black.ttf", size)


def serif(size, bold=False, italic=False):
    if bold and italic:
        name = "NotoSerif-BoldItalic.ttf"
    elif bold:
        name = "NotoSerif-Bold.ttf"
    elif italic:
        name = "NotoSerif-Italic.ttf"
    else:
        name = "NotoSerif-Regular.ttf"
    return _font(f"{NOTO_DIR}/{name}", size)


def sans(size, bold=False):
    return _font(f"{NOTO_DIR}/NotoSans-Bold.ttf" if bold
                 else f"{NOTO_DIR}/NotoSans-Regular.ttf", size)


def mono(size, bold=False):
    return _font(f"{DEJA_DIR}/DejaVuSansMono-Bold.ttf" if bold
                 else f"{DEJA_DIR}/DejaVuSansMono.ttf", size)


# ------------------------------------------------------------------- colours
PAPER = (246, 241, 230)
INK = (24, 23, 20)
LEDGER = (15, 82, 51)
LEDGER_DEEP = (9, 55, 34)
SIGNAL = (176, 33, 39)
SIGNAL_DEEP = (138, 23, 30)
SMOKE = (97, 95, 88)
RULE = (176, 168, 148)
WHITE = (255, 255, 255)

REGION_INK = {
    "EUROPE": (56, 90, 138),
    "MIDDLE EAST": (176, 118, 38),
    "AMERICAS": (138, 51, 51),
    "ASIA-PACIFIC": (15, 82, 51),
    "AFRICA": (118, 82, 158),
    "OCEANIA": (42, 126, 138),
    "WORLD": (68, 68, 68),
}

# ------------------------------------------------------------------- helpers
ISSUES = []


def px(v):
    return v * SS


def tw_of(d, s, fnt):
    return d.textlength(s, font=fnt)


def wrap(d, s, fnt, max_w):
    lines, cur = [], ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if tw_of(d, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, s, fnt, fill, max_w, leading, cap=None, tag=""):
    lines = wrap(d, s, fnt, max_w)
    if cap is not None and len(lines) > cap:
        ISSUES.append(f"{tag}: needs {len(lines)} lines, slot allows {cap}")
    for i, line in enumerate(lines):
        d.text((x, y + i * leading), line, font=fnt, fill=fill)
    return len(lines)


def chip(d, x, y, s, fnt, bg, fg, padx=5.0, pady=2.0):
    w = tw_of(d, s, fnt) + px(padx) * 2
    h = fnt.size + px(pady) * 2
    d.rectangle([x, y, x + w, y + h], fill=bg)
    d.text((x + px(padx), y + px(pady) - SS), s, font=fnt, fill=fg)
    return w


def chip_w(d, s, fnt, padx=5.0):
    return tw_of(d, s, fnt) + px(padx) * 2


def tracked(d, x, y, s, fnt, fill, tracking=2.0):
    used = 0.0
    for ch in s:
        d.text((x + used, y), ch, font=fnt, fill=fill)
        used += tw_of(d, ch, fnt) + px(tracking)
    return used - px(tracking)


def tracked_w(d, s, fnt, tracking=2.0):
    return (sum(tw_of(d, ch, fnt) for ch in s)
            + px(tracking) * (len(s) - 1))


def vgrad(w, h, top, bottom):
    col = Image.new("RGB", (1, h))
    for i in range(h):
        t = i / max(1, h - 1)
        col.putpixel((0, i), tuple(int(top[c] + (bottom[c] - top[c]) * t)
                                   for c in range(3)))
    return col.resize((w, h))


def glow(img, cx, cy, radius, colour, peak=110):
    r = int(radius)
    mask = Image.new("L", (r * 2, r * 2), 0)
    md = ImageDraw.Draw(mask)
    for i in range(r, 0, -2):
        md.ellipse([r - i, r - i, r + i, r + i],
                   fill=int(peak * (1 - i / r) ** 1.6))
    img.paste(Image.new("RGB", (r * 2, r * 2), colour),
              (int(cx - r), int(cy - r)), mask)


def tile(img, box, top, bottom):
    x0, y0, x1, y1 = box
    img.paste(vgrad(int(x1 - x0), int(y1 - y0), top, bottom),
              (int(x0), int(y0)))
    return ImageDraw.Draw(img, "RGBA")


# ------------------------------------------------------------------- the day
# Every story traces to a named wire or national agency; the evidence trail,
# with event-day vs report-day for the heroes, is in news-notes.md. One
# canonical figure per index or commodity, page-wide: gold $3,635 (Monday's
# New York close), the Kospi 4,708.54 / -3.31% (Monday's Seoul close), the
# S&P 500 +4.73% (Monday's New York close).

HEROES = [
    {
        "n": 1, "region": "ASIA-PACIFIC", "scene": "markets",
        "label": "ASIA CLOSES IN THE RED", "chip": "KOSPI -3.31% AT THE CLOSE",
        "kicker": "SEOUL · SHANGHAI · TAIPEI · MARKETS", "status": "REPORTED",
        "headline": "Asia's AI rout rolls on; Seoul steadies, gold jumps",
        "summary": (
            "Seoul's Kospi closed 3.31% lower at 4,708.54 after a plunge of "
            "nearly 6% tripped a program-selling halt. Seoul readied its "
            "first stabilisation fund since 2008; Shanghai reversed to a "
            "small gain after China's exchanges eased margin rules, Taipei "
            "rebounded 2.16%, Japan was shut for the holiday — and gold "
            "jumped past $3,635."
        ),
        "source": "dpa · Yonhap · market wires",
        "pin": (127.0, 37.5),
    },
    {
        "n": 2, "region": "EUROPE", "scene": "barrage",
        "label": "153 DRONES OVERNIGHT", "chip": "134 DOWNED · 15 DEAD",
        "kicker": "KYIV, UKRAINE · WAR", "status": "REPORTED",
        "headline": "A 153-drone night, and Kyiv counts 15 dead",
        "summary": (
            "Ukraine's Air Force said on Monday that Russia sent 153 "
            "attack drones overnight, 134 downed or jammed by 08:00, with "
            "hits at 11 locations. The Kyiv region's toll reached at least "
            "15 — 11 of them in Dymer, where the search ended on Monday "
            "evening with every missing resident accounted for."
        ),
        "source": "Ukrainian Air Force via Ukrinform · Al Jazeera",
        "pin": (30.5, 50.4),
    },
    {
        "n": 3, "region": "AMERICAS", "scene": "wallst",
        "label": "THE GREAT REBOUND", "chip": "S&P +4.73% · NVIDIA +31%",
        "kicker": "NEW YORK, USA · MARKETS", "status": "REPORTED",
        "headline": "Wall Street roars back as Huang returns",
        "summary": (
            "Nvidia restored Jensen Huang as chief executive on Monday, "
            "and the AI trade came roaring back with him: the chipmaker "
            "leapt 31%, the Nasdaq surged 6.51% and the S&P 500 climbed "
            "4.73% — its best day since April 2025 — snapping a seven-day "
            "losing streak and leaving correction behind. The Dow rose "
            "1,448 points."
        ),
        "source": "Reuters · AP market wraps",
        "pin": (-74.0, 40.7),
    },
]

# n, scene, chip, region, kicker, headline, summary, source, status, pin
CARDS = [
    (4, "house", "258 SEATS", "AMERICAS", "WASHINGTON, USA · POLITICS",
     "Democrats reach 258 House seats",
     "Foxx concedes; Jeffries, speaker-designate, waits for Jan 3.",
     "AP", "REPORTED", (-79.0, 35.8)),
    (5, "cop31", "NO PACT — DAY AFTER", "WORLD", "ANTALYA, TÜRKIYE · CLIMATE",
     "Guterres: 'no ambiguity in the science'",
     "Monday's fallout: blame flies, Pacific nations despair.",
     "UN News · Reuters", "REPORTED", (30.7, 36.9)),
    (6, "fire", "24 DEAD CONFIRMED", "ASIA-PACIFIC", "CIKANDE, BANTEN · DISASTER",
     "Indonesia confirms 24 dead in fire",
     "Monday's toll from the weekend blaze; 30 still missing.",
     "Reuters", "REPORTED", (106.4, -6.3)),
    (7, "fifa", "HOSTS CONFIRMED", "EUROPE", "ZURICH, SWITZERLAND · FOOTBALL",
     "Two Women's World Cups awarded",
     "2031 to the US-led four; 2035 to the UK — by acclamation.",
     "Reuters · AP", "REPORTED", (8.5, 47.4)),
    (8, "nepal", "$1.62BN PACKAGE", "ASIA-PACIFIC", "NEW DELHI, INDIA · AID",
     "India pledges $1.62bn to Nepal",
     "Modi's package for the flood-hit Himalayan neighbour.",
     "Reuters", "REPORTED", (77.2, 28.6)),
    (9, "castle", "OPENS AT NOON", "ASIA-PACIFIC", "OKINAWA, JAPAN · HERITAGE",
     "Shuri Castle's hall reopens",
     "The public walks in Monday, seven years after the fire.",
     "Shurijo Park officials", "REPORTED", (127.8, 26.2)),
    (10, "southsudan", "24 CIVILIANS DEAD", "AFRICA", "SOUTH SUDAN · VIOLENCE",
     "24 civilians killed in fresh violence",
     "An SPLA-IO attack deals a new blow to the peace deal.",
     "AFP, Juba", "REPORTED", (31.6, 4.9)),
    (11, "refineries", "THREE OIL SITES HIT", "EUROPE", "RUSSIA · WAR",
     "Ukraine's drones hit three oil sites",
     "Refineries at Perm and Rostov, a Tatarstan pumping station.",
     "Ukrinform", "REPORTED", (39.7, 47.2)),
    (12, "benghazi", "CORVETTE SUNK", "AFRICA", "BENGHAZI, LIBYA · NAVAL WAR",
     "Zelenskyy: we sank Russia's corvette",
     "Seven sea drones; the Kremlin 'takes note', the UN wants inquiry.",
     "Reuters", "REPORTED", (20.1, 32.1)),
    (13, "hormuz", "TWO TANKERS HIT", "MIDDLE EAST", "STRAIT OF HORMUZ",
     "Two more tankers are hit in Hormuz",
     "UKMTO logs two Monday hits, crews safe; Iran claims six.",
     "UKMTO · Al Jazeera", "REPORTED", (56.3, 26.2)),
    (14, "kano", "35 KILLED", "AFRICA", "KANO, NIGERIA · VIOLENCE",
     "35 Fulani killed in revenge attacks",
     "Reprisal killings deepen Nigeria's farmer-herder crisis.",
     "AFP", "REPORTED", (8.5, 12.0)),
    (15, "kim", "SEOUL STATEMENT", "ASIA-PACIFIC", "PYONGYANG · DIPLOMACY",
     "Kim: we seek security, not supremacy",
     "Pyongyang's Monday message as the region's markets reeled.",
     "AFP, Seoul", "REPORTED", (125.8, 39.0)),
]

# n, region, text, source — every line wire-verified; see news-notes.md
ALSO = [
    (16, "EUROPE", "Flash PMIs: Germany 55.0, France 46.2", "S&P Global"),
    (17, "EUROPE", "Russian cargo ship hit by drones in the Baltic", "WSJ"),
    (18, "EUROPE", "Zelenskyy pleads Kyiv's case in Berlin", "NPR"),
    (19, "MIDDLE EAST", "Netanyahu–Eisenkot talks end with no deal", "AFP"),
    (20, "MIDDLE EAST", "Saudi-led coalition downs Houthi missile", "AFP"),
    (21, "MIDDLE EAST", "Gaza: three killed in ceasefire breaches", "Anadolu"),
    (22, "MIDDLE EAST", "UN site in Khartoum damaged in strikes", "AFP"),
    (23, "MIDDLE EAST", "Bahrain seeks UN action on Iran", "Arab News"),
    (24, "AMERICAS", "Bolsonaro 'stable' in intensive care", "AFP"),
    (25, "AMERICAS", "Trump gives Iran talks more time", "Reuters"),
    (26, "AMERICAS", "Delta largely back on track after outage", "AP"),
    (27, "AMERICAS", "Army to detonate bomb chemicals in Iowa", "AP"),
    (28, "AMERICAS", "ICE arrests at Seattle airport delay flight", "AP"),
    (29, "AMERICAS", "FBI probes hack of its crime database", "AP"),
    (30, "ASIA-PACIFIC", "Samsung Securities hit by data-leak hack", "Yonhap"),
    (31, "ASIA-PACIFIC", "Ayodhya–Janakpur train flagged off", "IANS"),
    (32, "ASIA-PACIFIC", "Thai court cuts lawmaker's defamation term", "AP"),
    (33, "AFRICA", "WHO pleads for calm in Ebola-hit DR Congo", "AFP"),
    (34, "AFRICA", "Uganda signs Vitol crude-marketing deal", "New Vision"),
    (35, "OCEANIA", "Albanese: COP31 failure 'difficult times'", "AFP"),
    (36, "OCEANIA", "Pacific nations despair at COP flop", "Reuters"),
    (37, "OCEANIA", "ASX slips for an eighth straight day", "AAP"),
    (38, "WORLD", "Oil slips as supply returns", "Reuters"),
]

STATS = [
    ("153", "DRONES FIRED OVERNIGHT AT\nUKRAINE — 134 DOWNED"),
    ("+4.73%", "THE S&P 500 ON MONDAY — ITS\nBEST DAY SINCE APRIL 2025"),
    ("+31%", "NVIDIA IN A DAY, AS HUANG\nRETURNS TO THE HELM"),
    ("$3,635", "GOLD, AN OUNCE, AT MONDAY'S\nNEW YORK CLOSE"),
    ("258", "HOUSE SEATS FOR THE\nDEMOCRATS — MOST SINCE 1992"),
    ("24", "DEATHS CONFIRMED MONDAY IN\nTHE BANTEN FACTORY FIRE"),
]

TIMELINE = [
    ("00:00", "JUBA — AFP: 24 CIVILIANS DEAD IN SOUTH SUDAN"),
    ("06:00", "HORMUZ — UKMTO: TANKER HIT AT DAWN, CREW SAFE"),
    ("08:00", "KYIV — AIR FORCE: 134 OF 153 DRONES DOWNED"),
    ("08:52", "BEIJING — dpa: ASIAN SHARES TUMBLE"),
    ("14:00", "ZURICH — FIFA CONGRESS CONFIRMS TWO WORLD CUPS"),
    ("21:00", "NEW YORK — S&P 500 +4.73% AT THE CLOSE"),
]

DATE_CHECK = (
    "Left out as other days' news: Verstappen's Las Vegas Grand Prix win "
    "(Sat night) \u00b7 Alcaraz's first ATP Finals title and Liverpool's win "
    "over Manchester United (Sunday finals) \u00b7 Lisbon's cost-of-living "
    "march (Sat) \u00b7 the rapper-plot revelations in Copenhagen and Warsaw "
    "(Fri\u2013Sun) \u00b7 BepiColombo's arrival at Mercury (Sat) \u00b7 Wall "
    "Street's Friday crash \u2014 Monday's news is the rebound, at the top "
    "of this page: S&P 500 +4.73%, gold $3,635 at the close."
)

SOURCES_LINE = (
    "Sources: Reuters, AP, AFP, dpa, Ukrinform, Al Jazeera, UN News, Yonhap, "
    "AAP, IANS, Anadolu, S&P Global and the wires named with each story. "
    "Pictures and map: original, drawn in code."
)
LEGEND = (
    "HOW TO READ THE TAGS \u2014 REPORTED = carried by Monday's wires \u00b7 "
    "CLAIM = one side's account, labelled as such \u00b7 FORECAST = still to "
    "happen when this page was drawn."
)


# ------------------------------------------------------------------- scenes
def sc_markets(img, box):
    """A falling red tape across a grid, a gold sun rising out of it."""
    x0, y0, x1, y1 = box
    d = tile(img, box, (14, 20, 32), (34, 18, 24))
    w, h = x1 - x0, y1 - y0
    for i in range(1, 6):
        yy = y0 + h * i / 6
        d.line([x0, yy, x1, yy], fill=(72, 86, 106, 110), width=SS)
    for i in range(1, 9):
        xx = x0 + w * i / 9
        d.line([xx, y0, xx, y1], fill=(72, 86, 106, 70), width=SS)
    pts = [(0.03, 0.20), (0.14, 0.30), (0.24, 0.26), (0.36, 0.44),
           (0.47, 0.40), (0.58, 0.58), (0.68, 0.52), (0.79, 0.66),
           (0.90, 0.62), (0.97, 0.72)]
    xy = [(x0 + w * fx, y0 + h * fy) for fx, fy in pts]
    d.line(xy, fill=(255, 96, 86, 255), width=int(px(2.4)), joint="curve")
    for fx, fy in pts[::3]:
        cx, cy = x0 + w * fx, y0 + h * fy
        d.ellipse([cx - px(2), cy - px(2), cx + px(2), cy + px(2)],
                  fill=(255, 160, 140, 255))
    d.line([x0 + w * 0.03, y0 + h * 0.13, x0 + w * 0.10, y0 + h * 0.13],
           fill=(150, 220, 170, 255), width=int(px(1.8)))
    d.line([x0 + w * 0.90, y0 + h * 0.79, x0 + w * 0.97, y0 + h * 0.79],
           fill=(255, 96, 86, 255), width=int(px(1.8)))
    glow(img, x0 + w * 0.90, y0 + h * 0.24, w * 0.15, (255, 198, 64), 150)
    d = ImageDraw.Draw(img, "RGBA")
    gx, gy, gr = x0 + w * 0.90, y0 + h * 0.24, w * 0.055
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(255, 208, 88, 255),
              outline=(168, 118, 28, 255), width=int(px(1.4)))
    tw = tw_of(d, "$", sans(12, bold=True))
    d.text((gx - tw / 2, gy - px(7)), "$", font=sans(12, bold=True),
           fill=(96, 64, 8, 255))
    d.polygon([(x0 + w * 0.80, y0 + h * 0.36), (x0 + w * 0.845, y0 + h * 0.30),
               (x0 + w * 0.83, y0 + h * 0.42)], fill=(255, 208, 88, 255))


def sc_barrage(img, box):
    """A night skyline under a drone formation; one block dark, rubble below."""
    x0, y0, x1, y1 = box
    d = tile(img, box, (18, 24, 52), (88, 66, 70))
    w, h = x1 - x0, y1 - y0
    glow(img, x0 + w * 0.24, y0 + h * 0.72, w * 0.26, (255, 120, 40), 120)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([x0 + w * 0.86, y0 + h * 0.08, x0 + w * 0.925, y0 + h * 0.30],
              fill=(236, 234, 210, 255))
    rng = random.Random(23)
    for bx, bw_, seed in ((0.04, 0.20, 3), (0.30, 0.16, 5), (0.72, 0.22, 8)):
        d.rectangle([x0 + w * bx, y0 + h * 0.42, x0 + w * (bx + bw_), y1],
                    fill=(34, 34, 44, 255))
        rr = random.Random(seed)
        for r in range(4):
            for c in range(4):
                wx = x0 + w * bx + px(4) + c * (w * bw_ - px(8)) / 4
                wy = y0 + h * 0.48 + r * h * 0.12
                on = rr.random() > 0.45
                d.rectangle([wx, wy, wx + (w * bw_ - px(8)) / 4 - px(3),
                             wy + h * 0.075],
                            fill=(255, 198, 96, 255) if on
                            else (64, 66, 80, 255))
    bx = x0 + w * 0.50
    d.polygon([(bx, y0 + h * 0.50), (bx + w * 0.17, y0 + h * 0.60),
               (bx + w * 0.17, y1), (bx, y1)], fill=(48, 44, 48, 255))
    for i in range(9):
        rx = bx + rng.uniform(0, w * 0.20)
        ry = y0 + h * rng.uniform(0.86, 0.98)
        rs = rng.uniform(px(1.5), px(4))
        d.rectangle([rx, ry, rx + rs, ry + rs * 0.7],
                    fill=(rng.randint(74, 118),) * 3 + (255,))

    def drone(cx, cy, s):
        d.ellipse([cx - 4 * s, cy - 2.2 * s, cx + 4 * s, cy + 2.2 * s],
                  fill=(16, 16, 20, 255))
        for dx, dy in ((-11, -5.5), (11, -5.5), (-11, 5.5), (11, 5.5)):
            d.ellipse([cx + (dx - 4) * s, cy + (dy - 1.6) * s,
                       cx + (dx + 4) * s, cy + (dy + 1.6) * s],
                      outline=(16, 16, 20, 255), width=int(px(1.1)))
        d.ellipse([cx - 1.2 * s, cy + 1.5 * s, cx + 1.2 * s, cy + 3.6 * s],
                  fill=(255, 80, 60, 255))

    drone(x0 + w * 0.10, y0 + h * 0.18, SS * 0.9)
    drone(x0 + w * 0.24, y0 + h * 0.30, SS * 0.7)
    drone(x0 + w * 0.38, y0 + h * 0.14, SS * 0.8)
    drone(x0 + w * 0.55, y0 + h * 0.26, SS * 0.6)
    for fx, fy in ((0.13, 0.30), (0.30, 0.40), (0.47, 0.24)):
        d.arc([x0 + w * (fx - 0.10), y0 + h * (fy - 0.05),
               x0 + w * (fx + 0.16), y0 + h * (fy + 0.42)],
              200, 320, fill=(255, 226, 150, 220), width=int(px(1.3)))
    d.polygon([(x0 + w * 0.80, y0 + h * 0.42), (x0 + w * 0.55, y0),
               (x0 + w * 0.68, y0)], fill=(255, 242, 190, 40))


def sc_wallst(img, box):
    """Dawn over a skyline; a fat green line climbs out of the week-long fall."""
    x0, y0, x1, y1 = box
    d = tile(img, box, (16, 26, 48), (196, 116, 52))
    w, h = x1 - x0, y1 - y0
    glow(img, x0 + w * 0.78, y0 + h * 0.62, w * 0.30, (255, 176, 72), 130)
    d = ImageDraw.Draw(img, "RGBA")
    # rising sun disc behind the towers
    d.ellipse([x0 + w * 0.70, y0 + h * 0.34, x0 + w * 0.86, y0 + h * 0.78],
              fill=(255, 196, 92, 255))
    # skyline: dark towers with lit windows, seeded
    rng = random.Random(1123)
    towers = [(0.00, 0.16, 0.52), (0.13, 0.10, 0.66), (0.21, 0.13, 0.44),
              (0.32, 0.09, 0.74), (0.40, 0.14, 0.56), (0.52, 0.10, 0.64),
              (0.61, 0.12, 0.48), (0.72, 0.09, 0.70), (0.80, 0.11, 0.54),
              (0.90, 0.10, 0.62)]
    for fx, fw, fh in towers:
        tx, ty = x0 + w * fx, y1 - h * fh
        d.rectangle([tx, ty, tx + w * fw, y1], fill=(22, 26, 38, 255))
        cols = max(2, int(fw * 22))
        rows = max(3, int(fh * 12))
        for r in range(rows):
            for c in range(cols):
                if rng.random() > 0.52:
                    wx = tx + px(2.5) + c * (w * fw - px(5)) / cols
                    wy = ty + px(3) + r * (h * fh - px(6)) / rows
                    d.rectangle([wx, wy, wx + px(1.8), wy + px(2.4)],
                                fill=(255, 214, 130, 255))
    # the day's line: a shallow slide, then the vertical rescue
    pts = [(0.02, 0.30), (0.16, 0.36), (0.30, 0.42), (0.42, 0.40),
           (0.52, 0.55), (0.60, 0.38), (0.70, 0.26), (0.82, 0.17),
           (0.96, 0.10)]
    xy = [(x0 + w * fx, y0 + h * fy) for fx, fy in pts]
    d.line(xy, fill=(74, 222, 128, 255), width=int(px(3.2)), joint="curve")
    for fx, fy in pts[::4]:
        cx, cy = x0 + w * fx, y0 + h * fy
        d.ellipse([cx - px(2.2), cy - px(2.2), cx + px(2.2), cy + px(2.2)],
                  fill=(190, 255, 214, 255))
    # arrowhead at the top of the climb
    ax, ay = x0 + w * 0.965, y0 + h * 0.095
    d.polygon([(ax, ay - px(5)), (ax + px(6.5), ay + px(3.5)),
               (ax - px(1.5), ay + px(3.0))], fill=(74, 222, 128, 255))


HERO_SCENES = {"markets": sc_markets, "barrage": sc_barrage,
               "wallst": sc_wallst}

CARD_TINTS = {
    "house": ((66, 92, 138), (168, 188, 214), (86, 90, 98)),
    "cop31": ((228, 158, 84), (128, 70, 62), (66, 98, 118)),
    "fire": ((74, 42, 42), (176, 94, 52), (42, 32, 32)),
    "fifa": ((30, 84, 54), (96, 156, 104), (26, 62, 40)),
    "nepal": ((86, 116, 158), (186, 200, 218), (70, 84, 96)),
    "castle": ((92, 122, 172), (202, 212, 226), (112, 122, 132)),
    "southsudan": ((98, 112, 72), (190, 198, 142), (82, 90, 60)),
    "refineries": ((52, 62, 84), (128, 116, 118), (48, 54, 66)),
    "benghazi": ((40, 54, 86), (112, 112, 130), (46, 62, 94)),
    "hormuz": ((54, 86, 122), (152, 180, 202), (42, 72, 107)),
    "kano": ((128, 92, 62), (210, 170, 112), (98, 76, 56)),
    "kim": ((60, 60, 96), (150, 140, 170), (70, 64, 90)),
}


def card_scene(img, box, scene):
    x0, y0, x1, y1 = box
    top, mid, ground = CARD_TINTS[scene]
    d = tile(img, box, top, mid)
    w, h = x1 - x0, y1 - y0
    gy = y0 + h * 0.74
    d.rectangle([x0, gy, x1, y1], fill=ground + (255,))
    cx, cy = x0 + w * 0.5, y0 + h * 0.46
    dark = (26, 26, 30, 255)
    light = (240, 238, 228, 255)
    gold = (255, 205, 84, 255)

    def flame(fx, fy, s, col=(255, 132, 42, 255)):
        d.polygon([(fx - 9 * s, fy + 12 * s), (fx - 2.5 * s, fy - 2 * s),
                   (fx, fy - 14 * s), (fx + 3.5 * s, fy - 2 * s),
                   (fx + 9 * s, fy + 12 * s)], fill=col)
        d.polygon([(fx - 4.5 * s, fy + 12 * s), (fx, fy - 3 * s),
                   (fx + 4.5 * s, fy + 12 * s)], fill=(255, 198, 82, 255))

    def vessel(fx, fy, s, col=dark):
        d.polygon([(fx - 24 * s, fy + 6 * s), (fx + 24 * s, fy + 6 * s),
                   (fx + 16 * s, fy + 14 * s), (fx - 16 * s, fy + 14 * s)],
                  fill=col)
        d.rectangle([fx - 11 * s, fy - 2 * s, fx + 7 * s, fy + 6 * s], fill=col)
        d.rectangle([fx + 11 * s, fy - 8 * s, fx + 16 * s, fy + 6 * s], fill=col)

    def quad(fx, fy, s):
        d.ellipse([fx - 4.5 * s, fy - 2.6 * s, fx + 4.5 * s, fy + 2.6 * s],
                  fill=dark)
        for dx, dy in ((-12, -6), (12, -6), (-12, 6), (12, 6)):
            d.ellipse([fx + (dx - 4.5) * s, fy + (dy - 1.8) * s,
                       fx + (dx + 4.5) * s, fy + (dy + 1.8) * s],
                      outline=dark, width=int(px(1.1)))

    if scene == "house":
        d.rectangle([cx - w * 0.30, cy + h * 0.10, cx + w * 0.30, cy + h * 0.20],
                    fill=light)
        d.pieslice([cx - w * 0.13, cy - h * 0.34, cx + w * 0.13, cy + h * 0.18],
                   180, 360, fill=light)
        d.rectangle([cx - px(1.2), cy - h * 0.40, cx + px(1.2), cy - h * 0.30],
                    fill=light)
        for i in range(5):
            xx = cx - w * 0.26 + i * w * 0.115
            d.rectangle([xx, cy - h * 0.02, xx + w * 0.055, cy + h * 0.10],
                        fill=light)
        d.rectangle([cx - w * 0.33, gy, cx + w * 0.33, gy + h * 0.05],
                    fill=light)
    elif scene == "cop31":
        d.ellipse([cx - w * 0.13, cy - h * 0.30, cx + w * 0.13, cy + h * 0.26],
                  outline=light, width=int(px(1.6)))
        d.ellipse([cx - w * 0.05, cy - h * 0.30, cx + w * 0.05, cy + h * 0.26],
                  outline=light, width=int(px(1)))
        d.line([cx - w * 0.13, cy - h * 0.02, cx + w * 0.13, cy - h * 0.02],
               fill=light, width=int(px(1)))
        d.arc([cx - w * 0.24, cy - h * 0.44, cx + w * 0.24, cy + h * 0.40],
              300, 60, fill=(255, 214, 130, 255), width=int(px(1.6)))
        d.polygon([(cx + w * 0.20, cy - h * 0.34), (cx + w * 0.245, cy - h * 0.22),
                   (cx + w * 0.155, cy - h * 0.225)], fill=(255, 214, 130, 255))
    elif scene == "fire":
        d.rectangle([cx - w * 0.30, gy - h * 0.30, cx + w * 0.30, gy], fill=dark)
        d.rectangle([cx - w * 0.30, gy - h * 0.36, cx + w * 0.30, gy - h * 0.30],
                    fill=(20, 18, 18, 255))
        for i in range(4):
            flame(cx - w * 0.21 + i * w * 0.14, gy - h * 0.38,
                  SS * (0.85 + (i % 2) * 0.3))
    elif scene == "fifa":
        # a gold cup on the green: bowl, two handle arcs, stem, base, a ball
        d.rectangle([cx - w * 0.055, cy + h * 0.13, cx + w * 0.055,
                     cy + h * 0.19], fill=gold)
        d.rectangle([cx - w * 0.115, cy + h * 0.19, cx + w * 0.115,
                     cy + h * 0.26], fill=gold)
        d.arc([cx - w * 0.20, cy - h * 0.26, cx - w * 0.045, cy + h * 0.06],
              270, 90, fill=gold, width=int(px(1.8)))
        d.arc([cx + w * 0.045, cy - h * 0.26, cx + w * 0.20, cy + h * 0.06],
              90, 270, fill=gold, width=int(px(1.8)))
        d.polygon([(cx - w * 0.075, cy - h * 0.30), (cx + w * 0.075,
                    cy - h * 0.30), (cx + w * 0.05, cy + h * 0.13),
                   (cx - w * 0.05, cy + h * 0.13)], fill=gold)
        bx, by, br = cx + w * 0.30, gy - h * 0.10, w * 0.055
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=light)
        d.polygon([(bx - br * 0.35, by - br * 0.3), (bx + br * 0.35,
                    by - br * 0.3), (bx + br * 0.5, by + br * 0.25),
                   (bx, by + br * 0.55), (bx - br * 0.5, by + br * 0.25)],
                  fill=dark)
        for sx in (-0.34, 0.20):
            stx, sty = cx + w * sx, cy - h * 0.34
            d.polygon([(stx, sty - px(2.6)), (stx + px(1.4), sty - px(0.7)),
                       (stx + px(2.8), sty - px(0.6)), (stx + px(1.8),
                       sty + px(0.6)), (stx + px(2.2), sty + px(2.4)),
                       (stx, sty + px(1.3)), (stx - px(2.2), sty + px(2.4)),
                       (stx - px(1.8), sty + px(0.6)), (stx - px(2.8),
                       sty - px(0.6)), (stx - px(1.4), sty - px(0.7))],
                      fill=(255, 240, 190, 255))
    elif scene == "nepal":
        d.polygon([(x0 + w * 0.02, gy), (x0 + w * 0.24, gy - h * 0.52),
                   (x0 + w * 0.44, gy)], fill=(226, 232, 238, 255))
        d.polygon([(x0 + w * 0.30, gy), (x0 + w * 0.58, gy - h * 0.66),
                   (x0 + w * 0.84, gy)], fill=(206, 216, 228, 255))
        d.polygon([(x0 + w * 0.52, gy - h * 0.52), (x0 + w * 0.58, gy - h * 0.66),
                   (x0 + w * 0.64, gy - h * 0.52)], fill=(250, 250, 250, 255))
        d.rectangle([cx - w * 0.16, gy - h * 0.13, cx + w * 0.10, gy - h * 0.02],
                    fill=(150, 44, 40, 255))
        d.rectangle([cx + w * 0.10, gy - h * 0.10, cx + w * 0.20, gy - h * 0.02],
                    fill=(52, 52, 58, 255))
        d.line([x0, gy + h * 0.03, x1, gy + h * 0.03], fill=light,
               width=int(px(1.2)))
    elif scene == "castle":
        d.rectangle([cx - w * 0.28, gy - h * 0.14, cx + w * 0.28, gy],
                    fill=(148, 58, 46, 255))
        d.rectangle([cx - w * 0.20, gy - h * 0.32, cx + w * 0.20, gy - h * 0.14],
                    fill=(238, 234, 226, 255))
        d.polygon([(cx - w * 0.26, gy - h * 0.32), (cx + w * 0.26, gy - h * 0.32),
                   (cx + w * 0.14, gy - h * 0.47), (cx - w * 0.14, gy - h * 0.47)],
                  fill=(148, 58, 46, 255))
        d.polygon([(cx - w * 0.14, gy - h * 0.47), (cx + w * 0.14, gy - h * 0.47),
                   (cx, gy - h * 0.58)], fill=(118, 46, 38, 255))
    elif scene == "southsudan":
        d.ellipse([cx - w * 0.30, y0 + h * 0.08, cx - w * 0.19, y0 + h * 0.32],
                  fill=(255, 222, 122, 255))
        for fx in (0.24, 0.52, 0.76):
            xx = x0 + w * fx
            d.polygon([(xx, gy), (xx + w * 0.065, gy - h * 0.30),
                       (xx + w * 0.13, gy)], fill=(58, 68, 42, 255))
        d.rectangle([cx - w * 0.025, cy - h * 0.10, cx + w * 0.025, cy + h * 0.14],
                    fill=light)
        d.rectangle([cx - w * 0.085, cy - h * 0.03, cx + w * 0.085, cy + h * 0.05],
                    fill=light)
    elif scene == "refineries":
        for fx, fh in ((0.22, 0.34), (0.44, 0.44), (0.66, 0.30)):
            xx = x0 + w * fx
            d.rectangle([xx, gy - h * fh, xx + w * 0.15, gy],
                        fill=(196, 200, 206, 255))
            d.ellipse([xx, gy - h * fh - h * 0.045, xx + w * 0.15,
                       gy - h * fh + h * 0.045], fill=(226, 230, 236, 255))
        flame(cx + w * 0.30, gy - h * 0.46, SS * 1.0)
        d.line([x0 + w * 0.08, gy - h * 0.06, x1 - w * 0.08, gy - h * 0.06],
               fill=(150, 154, 160, 255), width=int(px(1.2)))
    elif scene == "benghazi":
        vessel(cx, cy + h * 0.06, SS * 1.0)
        quad(cx - w * 0.26, y0 + h * 0.20, SS * 0.8)
        flame(cx + w * 0.10, cy - h * 0.10, SS * 0.8)
        for i in range(3):
            xx = x0 + w * (0.10 + i * 0.3)
            d.arc([xx, gy + h * 0.02, xx + w * 0.2, gy + h * 0.18], 0, 180,
                  fill=(220, 235, 245, 200), width=int(px(1.3)))
    elif scene == "hormuz":
        vessel(cx - w * 0.10, cy, SS * 0.95)
        d.ellipse([cx + w * 0.22, cy + h * 0.10, cx + w * 0.32, cy + h * 0.34],
                  outline=dark, width=int(px(1.6)))
        d.line([cx + w * 0.27, cy + h * 0.10, cx + w * 0.27, cy - h * 0.02],
               fill=dark, width=int(px(1.4)))
        for sp in range(6):
            ang = sp * math.pi / 3
            d.line([cx + w * 0.27, cy + h * 0.22,
                    cx + w * 0.27 + math.cos(ang) * w * 0.055,
                    cy + h * 0.22 + math.sin(ang) * h * 0.13],
                   fill=dark, width=int(px(1.2)))
        flame(cx - w * 0.02, cy - h * 0.16, SS * 0.7)
    elif scene == "kano":
        d.ellipse([cx + w * 0.24, y0 + h * 0.06, cx + w * 0.36, y0 + h * 0.30],
                  fill=(255, 226, 140, 255))
        for fx in (0.16, 0.44):
            xx = x0 + w * fx
            d.rectangle([xx, gy - h * 0.20, xx + w * 0.16, gy],
                        fill=(104, 78, 54, 255))
            d.polygon([(xx - w * 0.03, gy - h * 0.20), (xx + w * 0.19, gy - h * 0.20),
                       (xx + w * 0.08, gy - h * 0.36)], fill=(84, 60, 38, 255))
        d.rectangle([cx + w * 0.16, gy - h * 0.30, cx + w * 0.185, gy],
                    fill=(66, 56, 36, 255))
        d.ellipse([cx + w * 0.06, gy - h * 0.52, cx + w * 0.29, gy - h * 0.28],
                  fill=(86, 106, 58, 255))
    elif scene == "kim":
        d.rectangle([cx - w * 0.30, gy - h * 0.02, cx - w * 0.30 + px(2), gy],
                    fill=light)
        d.rectangle([cx - w * 0.30, y0 + h * 0.08, cx - w * 0.06, y0 + h * 0.30],
                    fill=(178, 34, 40, 255))
        d.polygon([(cx - w * 0.235, y0 + h * 0.115), (cx - w * 0.222, y0 + h * 0.155),
                   (cx - w * 0.198, y0 + h * 0.16), (cx - w * 0.216, y0 + h * 0.185),
                   (cx - w * 0.208, y0 + h * 0.215), (cx - w * 0.235, y0 + h * 0.195),
                   (cx - w * 0.262, y0 + h * 0.215), (cx - w * 0.252, y0 + h * 0.185),
                   (cx - w * 0.27, y0 + h * 0.16), (cx - w * 0.238, y0 + h * 0.155)],
                  fill=(255, 255, 255, 255))
        for i in range(4):
            xx = cx - w * 0.02 + i * w * 0.09
            d.rectangle([xx, gy - h * 0.16, xx + w * 0.045, gy], fill=dark)
            d.ellipse([xx - w * 0.004, gy - h * 0.235, xx + w * 0.05, gy - h * 0.16],
                      fill=(216, 178, 148, 255))
    return d


# ------------------------------------------------------------------- map
# Schematic dotted world on a 48 x 24 grid (columns from -180 degrees,
# rows from +84 degrees): each row lists its land runs as (first, last).
MAP_RUNS = {
    1: [(25, 44)],
    2: [(2, 11), (15, 16), (24, 45)],
    3: [(2, 12), (15, 17), (23, 45)],
    4: [(2, 13), (16, 17), (23, 44)],
    5: [(3, 14), (23, 43)],
    6: [(3, 14), (23, 26), (29, 42)],
    7: [(4, 14), (23, 26), (28, 31), (32, 41)],
    8: [(5, 13), (23, 29), (33, 40)],
    9: [(5, 11), (23, 30), (28, 32), (34, 39)],
    10: [(6, 10), (23, 30), (29, 32), (35, 39), (41, 41)],
    11: [(7, 8), (24, 30), (36, 37)],
    12: [(24, 30)],
    13: [(10, 13), (24, 30)],
    14: [(10, 14), (25, 29), (37, 41)],
    15: [(11, 14), (25, 29), (36, 42)],
    16: [(11, 14), (25, 29), (31, 31), (38, 44)],
    17: [(11, 13), (26, 28), (31, 31), (38, 44)],
    18: [(11, 13), (26, 28), (38, 44)],
    19: [(12, 13), (26, 27), (39, 44)],
    20: [(12, 13), (40, 44)],
    21: [(12, 12), (41, 42), (46, 46)],
    22: [(12, 12), (47, 47)],
}
MAP_COLS, MAP_ROWS = 48, 24
LAND = set()
for _r, _runs in MAP_RUNS.items():
    for _c0, _c1 in _runs:
        LAND.update((_r, c) for c in range(_c0, _c1 + 1))


def draw_map(img, box, pins):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img, "RGBA")
    cw, ch = (x1 - x0) / MAP_COLS, (y1 - y0) / MAP_ROWS
    r = max(px(1.1), cw * 0.30)
    for (ri, ci) in LAND:
        cx, cy = x0 + (ci + 0.5) * cw, y0 + (ri + 0.5) * ch
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(122, 118, 106, 255))
    pf = sans(7.5, bold=True)
    for n, lon, lat in pins:
        cx = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
        cy = y0 + (84.0 - lat) / 138.0 * (y1 - y0)
        pr = px(6.5)
        d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=SIGNAL,
                  outline=WHITE + (255,), width=int(px(1.2)))
        s = str(n)
        d.text((cx - tw_of(d, s, pf) / 2, cy - pf.size / 2 - SS), s,
               font=pf, fill=WHITE + (255,))


# ------------------------------------------------------------------- assembly
MX = 18.0
CW = 1024.0 - 2 * MX


def build():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    d = ImageDraw.Draw(img, "RGBA")

    def rect(x, y, w, h, **kw):
        d.rectangle([px(x), px(y), px(x + w), px(y + h)], **kw)

    total = len(HEROES) + len(CARDS) + len(ALSO)

    # ---- count band
    rect(0, 0, 1024, 28, fill=LEDGER)
    f_band = sans(10, bold=True)
    tracked(d, px(MX), px(8),
            "ONE PAGE · THE WHOLE DAY · SET IN TYPE BEFORE THE WIRES CLOSE",
            f_band, (240, 246, 240), tracking=1)
    right = "MONDAY EDITION"
    tracked(d, px(1024 - MX) - tracked_w(d, right, f_band, 1), px(8),
            right, f_band, (240, 246, 240), tracking=1)

    # ---- masthead: the paper's name, then the day spelled out
    title = "THE MONDAY LEDGER"
    f_title = display(54)
    tw = tw_of(d, title, f_title)
    d.text(((CANVAS - tw) / 2, px(34)), title, font=f_title, fill=INK)
    spell = "Monday, the twenty-third of November, two thousand and twenty-six"
    f_spell = serif(14.5, italic=True)
    tw = tw_of(d, spell, f_spell)
    d.text(((CANVAS - tw) / 2, px(94)), spell, font=f_spell, fill=LEDGER_DEEP)
    claim = (f"{total} STORIES · 7 REGIONS · EVERY ONE DATED "
             f"MONDAY 23 NOVEMBER 2026")
    f_claim = sans(11, bold=True)
    tracked(d, (CANVAS - tracked_w(d, claim, f_claim, 2)) / 2, px(114),
            claim, f_claim, LEDGER, tracking=2)
    d.line([px(MX), px(126), px(1024 - MX), px(126)], fill=INK,
           width=int(px(1.6)))
    d.line([px(MX), px(129), px(1024 - MX), px(129)], fill=INK,
           width=int(px(0.7)))

    # ---- strapline: the three heroes, teased
    strap = ("153 drones in the night over Kyiv \u00b7 Asia's rout meets "
             "rescue funds \u00b7 Wall Street roars back")
    f_strap = serif(14, italic=True)
    tw = tw_of(d, strap, f_strap)
    if tw > px(CW):
        ISSUES.append(f"strapline too wide: {tw / SS:.0f}px")
    d.text(((CANVAS - tw) / 2, px(134)), strap, font=f_strap, fill=SIGNAL_DEEP)

    # ---- stat strip: six of the day's numbers
    sy = 154.0
    cell = CW / 6
    f_num, f_cap = serif(25, bold=True), sans(8.5, bold=True)
    for i, (num, cap) in enumerate(STATS):
        cx = MX + i * cell
        tw = tw_of(d, num, f_num)
        d.text((px(cx + (cell - tw / SS) / 2), px(sy)), num, font=f_num,
               fill=LEDGER)
        for j, line in enumerate(cap.split("\n")):
            lw = tw_of(d, line, f_cap)
            d.text((px(cx + (cell - lw / SS) / 2), px(sy + 36 + j * 11)),
                   line, font=f_cap, fill=SMOKE)
        if i:
            d.line([px(cx), px(sy + 4), px(cx), px(sy + 58)], fill=RULE,
                   width=SS)
    d.line([px(MX), px(218), px(1024 - MX), px(218)], fill=RULE, width=SS)

    # ---- region bar: counts computed from the data, so the bar cannot lie
    counts = {}
    for hro in HEROES:
        counts[hro["region"]] = counts.get(hro["region"], 0) + 1
    for c in CARDS:
        counts[c[3]] = counts.get(c[3], 0) + 1
    for a in ALSO:
        counts[a[1]] = counts.get(a[1], 0) + 1
    assert sum(counts.values()) == total, "region tally != story total"
    assert len(counts) == 7, f"regions: {sorted(counts)}"
    order = ["EUROPE", "ASIA-PACIFIC", "AMERICAS", "AFRICA", "MIDDLE EAST",
             "OCEANIA", "WORLD"]
    widths = {r: max(48.0, CW * counts[r] / total) for r in order}
    widths[max(order, key=lambda r: widths[r])] -= sum(widths.values()) - CW
    f_reg = sans(9.5, bold=True)
    x = MX
    for reg in order:
        rect(x, 222, widths[reg], 24, fill=REGION_INK[reg])
        label = f"{reg} {counts[reg]}"
        lw = tw_of(d, label, f_reg)
        d.text((px(x + (widths[reg] - lw / SS) / 2), px(227)), label,
               font=f_reg, fill=WHITE)
        x += widths[reg]

    # ---- UTC strip: the day as the clock saw it
    rect(0, 250, 1024, 26, fill=(18, 18, 18))
    tracked(d, px(MX), px(254), "THE DAY IN UTC", sans(9.5, bold=True),
            WHITE, tracking=1)
    f_utc = mono(9, bold=True)
    items = [f"{t} {s}" for t, s in TIMELINE]
    for row_i in range(2):
        xx = MX + (150 if row_i == 0 else 0)
        for it in items[row_i * 3:(row_i + 1) * 3]:
            d.text((px(xx), px(252 + row_i * 12)), it, font=f_utc,
                   fill=(235, 232, 220))
            xx += tw_of(d, it, f_utc) / SS + 16

    # ---- heroes
    hy = 282.0
    hw = (CW - 24) / 3
    f_kick, f_head = sans(10.5, bold=True), serif(16.5, bold=True)
    f_sum, f_src = serif(11.5), sans(9, bold=True)
    pins = []
    for i, hro in enumerate(HEROES):
        hx = MX + i * (hw + 12)
        HERO_SCENES[hro["scene"]](img, (px(hx), px(hy), px(hx + hw),
                                        px(hy + 100)))
        d = ImageDraw.Draw(img, "RGBA")
        chip(d, px(hx + 6), px(hy + 6), hro["label"], sans(10, bold=True),
             SIGNAL, WHITE)
        cw_ = chip_w(d, hro["chip"], sans(10, bold=True))
        chip(d, px(hx + hw) - cw_, px(hy + 6), hro["chip"],
             sans(10, bold=True), (18, 18, 18), WHITE)
        ky = hy + 106
        num = f"{hro['n']}  "
        d.text((px(hx), px(ky)), num, font=serif(13, bold=True), fill=SIGNAL)
        nw = tw_of(d, num, serif(13, bold=True))
        tracked(d, px(hx) + nw, px(ky + 2), hro["kicker"], f_kick, INK,
                tracking=1)
        st_w = chip_w(d, hro["status"], sans(9, bold=True))
        chip(d, px(hx + hw) - st_w, px(ky + 1), hro["status"],
             sans(9, bold=True), LEDGER, WHITE)
        para(d, px(hx), px(hy + 124), hro["headline"], f_head, INK,
             px(hw), px(20), cap=2, tag=f"hero{hro['n']} headline")
        para(d, px(hx), px(hy + 170), hro["summary"], f_sum, (40, 40, 38),
             px(hw), px(14.2), cap=6, tag=f"hero{hro['n']} summary")
        tracked(d, px(hx), px(hy + 264), hro["source"].upper(), f_src,
                SMOKE, tracking=1)
        pins.append((hro["n"], hro["pin"][0], hro["pin"][1]))
        if i:
            d.line([px(hx - 6), px(hy + 106), px(hx - 6), px(hy + 278)],
                   fill=RULE, width=SS)
    d.line([px(MX), px(562), px(1024 - MX), px(562)], fill=RULE, width=SS)

    # ---- cards: six across, two rows
    cy0 = 568.0
    card_w = (CW - 5 * 8) / 6
    card_h = 102.0
    f_ck, f_ch, f_cs = sans(8.5, bold=True), serif(12.5, bold=True), sans(9.5)
    for idx, c in enumerate(CARDS):
        (n, scene, chip_t, region, kicker, headline, summary, source,
         status, pin) = c
        r, col = divmod(idx, 6)
        cx, cy = MX + col * (card_w + 8), cy0 + r * (card_h + 6)
        card_scene(img, (px(cx), px(cy), px(cx + card_w), px(cy + 34)), scene)
        d = ImageDraw.Draw(img, "RGBA")
        chip(d, px(cx + 4), px(cy + 4), chip_t, sans(8.5, bold=True),
             SIGNAL, WHITE, padx=4, pady=1.5)
        if status != "REPORTED":
            sw_ = chip_w(d, status, sans(8.5, bold=True), padx=4)
            chip(d, px(cx + card_w) - sw_, px(cy + 4), status,
                 sans(8.5, bold=True), LEDGER, WHITE, padx=4, pady=1.5)
        tracked(d, px(cx), px(cy + 38), f"{n} · {kicker}", f_ck,
                LEDGER_DEEP, tracking=0)
        para(d, px(cx), px(cy + 49), headline, f_ch, INK, px(card_w),
             px(14.5), cap=2, tag=f"card{n} headline")
        para(d, px(cx), px(cy + 79), summary, f_cs, (52, 52, 50),
             px(card_w), px(11.5), cap=2, tag=f"card{n} summary")
        pins.append((n, pin[0], pin[1]))

    # ---- map + ALSO
    my = 782.0
    d.line([px(MX), px(my), px(1024 - MX), px(my)], fill=RULE, width=SS)
    tracked(d, px(MX), px(my + 6), "WHERE IT HAPPENED — PINS = STORY NUMBERS",
            sans(10, bold=True), INK, tracking=1)
    draw_map(img, (px(MX), px(my + 24), px(MX + 348), px(my + 146)), pins)
    d = ImageDraw.Draw(img, "RGBA")
    ax = MX + 366
    aw = 1024 - MX - ax
    tracked(d, px(ax), px(my + 6),
            f"ALSO ON MONDAY 23 NOVEMBER — {len(ALSO)} MORE STORIES",
            sans(10, bold=True), INK, tracking=1)
    f_also, f_also_b = sans(9.5), sans(9.5, bold=True)
    half = (len(ALSO) + 1) // 2
    col_w = (aw - 14) / 2
    for j, (n, region, text_, source) in enumerate(ALSO):
        col = 0 if j < half else 1
        row = j if j < half else j - half
        xx, yy = ax + col * (col_w + 14), my + 25 + row * 11.0
        num = f"{n} "
        d.text((px(xx), px(yy)), num, font=f_also_b, fill=SIGNAL)
        nw = tw_of(d, num, f_also_b)
        line = f"{text_} — {region.title()} · {source}"
        if tw_of(d, line, f_also) / SS > col_w - nw / SS:
            ISSUES.append(f"also{n}: line too wide "
                          f"({tw_of(d, line, f_also) / SS:.0f} > "
                          f"{col_w - nw / SS:.0f})")
        d.text((px(xx) + nw, px(yy)), line, font=f_also, fill=(40, 40, 38))

    # ---- DATE CHECK
    dy = 936.0
    rect(MX, dy, CW, 42, outline=SIGNAL, width=int(px(1.6)))
    rect(MX, dy, 118, 15, fill=SIGNAL)
    d.text((px(MX + 6), px(dy + 2)), "DATE CHECK", font=sans(10, bold=True),
           fill=WHITE)
    para(d, px(MX + 126), px(dy + 3), DATE_CHECK, serif(10.5), (52, 40, 38),
         px(CW - 134), px(12.5), cap=3, tag="datecheck")

    # ---- sources + legend
    f_leg = sans(9.5)
    for yy, line in ((982, SOURCES_LINE), (994, LEGEND)):
        if tw_of(d, line, f_leg) / SS > CW:
            ISSUES.append(f"line at {yy} too wide")
        d.text((px(MX), px(yy)), line, font=f_leg, fill=SMOKE)

    # ---- ledger close
    rect(0, 1004, 1024, 20, fill=LEDGER)
    f_foot = sans(9.5, bold=True)
    tracked(d, px(MX), px(1009),
            f"THE LEDGER LINE — {total} STORIES · 7 REGIONS · "
            f"7 LEFT OUT AS OTHER DAYS", f_foot, (240, 246, 240), tracking=1)
    right = "THE WHOLE OF MONDAY · WIRES READ TO 05:15 UTC, TUESDAY 24 NOV"
    tracked(d, px(1024 - MX) - tracked_w(d, right, f_foot, 1), px(1009),
            right, f_foot, (240, 246, 240), tracking=1)
    return img


def save(img):
    small = img.resize((FINAL, FINAL), Image.LANCZOS)
    small.save(OUT, optimize=True)
    size = os.path.getsize(OUT)
    if size > 640_000:
        q = small.quantize(colors=256, method=Image.MEDIANCUT,
                           dither=Image.Dither.NONE)
        q.save(OUT, optimize=True)
        size = os.path.getsize(OUT)
        print(f"quantized to 256 colours: {size} bytes")
    return size


def main():
    img = build()
    if ISSUES:
        print("FIT PROBLEMS:")
        for p in ISSUES:
            print(" -", p)
    size = save(img)
    print(f"saved {OUT}: 1024x1024, {size} bytes")


if __name__ == "__main__":
    main()
