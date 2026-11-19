#!/usr/bin/env python3
"""news-image-20261118: front-page image summing up world news of
Wednesday 18 November 2026. Stdlib only. Draws an 800x800 PNG with a
hand-rolled encoder and a 5x7 bitmap font; no network, no fonts, no PIL.
Writes $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
Deterministic: identical bytes on every run.
"""
import os
import struct
import zlib

W, H = 800, 800

# ---------------------------------------------------------------- palette
PAPER = (250, 248, 240)
NAVY = (16, 32, 64)
NAVY2 = (24, 48, 92)
INK = (22, 22, 22)
WHITE = (255, 255, 255)
RED = (178, 34, 34)
DARKRED = (130, 20, 20)
BLUE = (40, 90, 160)
SKY = (140, 185, 225)
SEA = (28, 105, 165)
SAND = (222, 200, 150)
GREY = (110, 110, 110)
LIGHTGREY = (225, 222, 214)
ORANGE = (235, 130, 30)
YELLOW = (245, 205, 60)
GREEN = (34, 139, 60)
NIGHT = (10, 18, 40)
GOLD = (200, 160, 40)

# ---------------------------------------------------------------- framebuffer
_px = bytearray(W * H * 3)


def _set(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        _px[i], _px[i + 1], _px[i + 2] = c


def rect(x, y, w, h, c):
    for yy in range(max(0, y), min(H, y + h)):
        base = (yy * W + max(0, x)) * 3
        for xx in range(max(0, x), min(W, x + w)):
            i = (yy * W + xx) * 3
            _px[i], _px[i + 1], _px[i + 2] = c


def hline(x0, x1, y, c):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        _set(x, y, c)


def vline(x, y0, y1, c):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        _set(x, y, c)


def line(x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        _set(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                _set(xx, yy, c)


def blob(cx, cy, r, c):
    """Irregular filled blob (fireball / smoke) made of overlapping discs."""
    for dx, dy, rr in ((-r // 2, -r // 3, r // 2), (r // 3, -r // 4, r // 2),
                       (0, r // 3, r // 2), (-r // 4, r // 4, r // 3),
                       (r // 2, r // 4, r // 3), (0, 0, (r * 3) // 5)):
        disc(cx + dx, cy + dy, rr, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    for yy in range(min(y0, y1, y2), max(y0, y1, y2) + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                 (x2, y2, x0, y0)):
            if ay == by:
                continue
            if min(ay, by) <= yy < max(ay, by):
                xs.append(ax + (yy - ay) * (bx - ax) // (by - ay))
        if len(xs) >= 2:
            for x in range(min(xs), max(xs) + 1):
                _set(x, yy, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = ink. Written fresh for this entry.
FONT = {
    'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    'D': ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    'G': (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'I': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    'J': ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    'N': ("#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"),
    'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    'X': ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    '0': (" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "),
    '1': ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    '2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    '3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    '4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    '5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    '6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    '7': ("#####", "    #", "   # ", "   # ", "  #  ", "  #  ", "  #  "),
    '8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    '9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    ' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    '&': (" ##  ", "#  # ", "#  # ", " #   ", "# # #", "#  # ", " ## #"),
    '-': ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    '.': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ',': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    "'": ("  #  ", "  #  ", "  #  ", "     ", "     ", "     ", "     "),
    ':': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ';': ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    '!': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    '?': (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    '%': ("#   #", "#  # ", "   # ", "  #  ", " #   ", "#  # ", "#   #"),
    '$': ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    '(': ("   ##", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   ##"),
    ')': ("##   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", "##   "),
    '/': ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    '+': ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    '=': ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
    '"': (" # # ", " # # ", " # # ", "     ", "     ", "     ", "     "),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c, align="left"):
    s = s.upper()
    w = text_w(s, scale)
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == '#':
                    rect(cx + cc * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return w


def wrap(s, max_chars):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        nxt = (cur + " " + wd).strip()
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- PNG encoder
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += _px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- scenes
def panel(x, y, w, h):
    rect(x, y, w, h, WHITE)
    for xx in range(x, x + w):
        _set(xx, y, INK)
        _set(xx, y + h - 1, INK)
    for yy in range(y, y + h):
        _set(x, yy, INK)
        _set(x + w - 1, yy, INK)


def caption_block(x, y, w, heading, lines, hcol=RED, max_chars=19):
    cx = x + 8
    draw_text(cx, y, heading, 2, hcol)
    yy = y + 18
    # Wrap every caption line to the panel's inner width so nothing ever
    # runs past the panel border.
    for ln in lines:
        for part in wrap(ln, max_chars):
            draw_text(cx, yy, part, 2, INK)
            yy += 16


def scene_hero(x, y, w, h):
    # Night sky over a Gulf air base: missile trails, blasts, interceptors.
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(NIGHT[k] + (NAVY2[k] - NIGHT[k]) * t) for k in range(3))
        hline(x, x + w - 1, y + i, c)
    import random
    rnd = random.Random(1811)
    for _ in range(60):
        _set(x + rnd.randrange(w), y + rnd.randrange(h // 2), WHITE)
    # ground + runway
    rect(x, y + h - 70, w, 70, (28, 28, 34))
    rect(x, y + h - 46, w, 4, (200, 200, 200))
    for i in range(0, w, 40):
        rect(x + i, y + h - 45, 18, 2, YELLOW)
    # base buildings + tower
    rect(x + 40, y + h - 110, 90, 40, (52, 52, 60))
    rect(x + 150, y + h - 128, 14, 58, (52, 52, 60))
    rect(x + 146, y + h - 138, 22, 10, (52, 52, 60))
    for bx in (60, 90, 120):
        rect(x + bx, y + h - 100, 8, 8, YELLOW)
    # parked jet silhouette
    rect(x + 560, y + h - 92, 120, 10, (20, 20, 26))
    tri(x + 680, y + h - 92, x + 700, y + h - 92, x + 690, y + h - 108, (20, 20, 26))
    tri(x + 560, y + h - 92, x + 580, y + h - 92, x + 570, y + h - 104, (20, 20, 26))
    # incoming missile trails (top-right to base)
    for (tx, ty, ex, ey) in ((x + 700, y + 8, x + 430, y + h - 80),
                             (x + 620, y + 4, x + 300, y + h - 76),
                             (x + 760, y + 30, x + 620, y + h - 74)):
        for s in range(0, 101, 4):
            t = s / 100.0
            px = int(tx + (ex - tx) * t)
            py = int(ty + (ey - ty) * t + 18 * (1 - t) * t * 4 * -0.4)
            disc(px, py, 2, ORANGE if s % 8 == 0 else YELLOW)
    # interceptor streaks rising
    line(x + 220, y + h - 70, x + 330, y + 40, WHITE)
    line(x + 480, y + h - 70, x + 560, y + 60, WHITE)
    # explosions on the ground
    blob(x + 300, y + h - 78, 26, ORANGE)
    blob(x + 300, y + h - 78, 15, YELLOW)
    blob(x + 430, y + h - 76, 20, ORANGE)
    blob(x + 430, y + h - 76, 11, YELLOW)
    blob(x + 620, y + h - 74, 16, ORANGE)
    # smoke columns
    blob(x + 300, y + h - 120, 18, (90, 90, 96))
    blob(x + 430, y + h - 112, 14, (90, 90, 96))


def scene_kerch(x, y, w, h):
    rect(x, y, w, h, SKY)
    disc(x + 200, y + 18, 14, YELLOW)
    rect(x, y + h - 18, w, 18, SEA)
    for i in range(0, w, 26):
        hline(x + i, x + i + 14, y + h - 12, (200, 225, 240))
        hline(x + i + 8, x + i + 20, y + h - 6, (200, 225, 240))
    # bridge deck, left span intact, right span collapsed into the sea
    rect(x + 8, y + 28, 120, 8, (70, 70, 76))
    rect(x + 8, y + 36, 5, 20, (70, 70, 76))
    rect(x + 122, y + 36, 5, 20, (70, 70, 76))
    line(x + 132, y + 36, x + 200, y + h - 6, (70, 70, 76))
    line(x + 132, y + 30, x + 200, y + h - 12, (70, 70, 76))
    rect(x + 204, y + 28, 36, 8, (70, 70, 76))
    rect(x + 234, y + 36, 5, 20, (70, 70, 76))
    # smoke + fire at the break
    blob(x + 148, y + 22, 13, (90, 90, 96))
    blob(x + 164, y + 34, 10, ORANGE)
    blob(x + 164, y + 34, 6, YELLOW)


def scene_apex(x, y, w, h):
    # Shenzhen skyline at dusk + two flags (China red, Russia tricolour).
    rect(x, y, w, h, (250, 200, 140))
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int((250, 200, 140)[k] + ((90, 110, 160)[k] - (250, 200, 140)[k]) * t)
                  for k in range(3))
        hline(x, x + w - 1, y + i, c)
    for bx, bh, bw in ((0, 34, 22), (26, 52, 20), (50, 40, 24), (78, 62, 20),
                       (102, 44, 22), (128, 70, 20), (152, 48, 22),
                       (178, 58, 20), (202, 38, 22), (228, 52, 20)):
        rect(x + bx, y + h - bh, bw, bh, (60, 66, 84))
    # flags on poles
    vline(x + 96, y + 8, y + 44, INK)
    rect(x + 96, y + 8, 34, 22, RED)
    disc(x + 104, y + 15, 3, YELLOW)
    disc(x + 114, y + 13, 1, YELLOW)
    disc(x + 118, y + 19, 1, YELLOW)
    vline(x + 152, y + 8, y + 44, INK)
    rect(x + 152, y + 8, 34, 8, WHITE)
    rect(x + 152, y + 16, 34, 7, BLUE)
    rect(x + 152, y + 23, 34, 7, RED)


def scene_senate(x, y, w, h):
    # Ballot box + 56-44 bars: Democrats take the Senate.
    rect(x, y, w, h, (235, 238, 245))
    rect(x + 18, y + 26, 84, 44, (245, 245, 245))
    rect(x + 18, y + 26, 84, 8, RED)
    rect(x + 52, y + 16, 16, 12, (245, 245, 245))
    line(x + 56, y + 34, x + 62, y + 42, GREEN)
    line(x + 62, y + 42, x + 76, y + 24, GREEN)
    line(x + 76, y + 24, x + 82, y + 30, GREEN)
    # bars
    rect(x + 130, y + 22, 16, 44, BLUE)
    rect(x + 150, y + 22, 90, 10, BLUE)
    rect(x + 150, y + 40, 70, 10, RED)
    draw_text(x + 128, y + 4, "56", 2, BLUE)
    draw_text(x + 222, y + 36, "44", 2, RED)


def scene_knesset(x, y, w, h):
    # Knesset-style building: dome, columns, Israeli flag stripes.
    rect(x, y, w, h, SKY)
    rect(x, y + h - 34, w, 34, (120, 170, 90))
    rect(x + 46, y + 26, 160, 44, (232, 226, 210))
    for cx in range(56, 206, 22):
        rect(x + cx, y + 34, 8, 36, (200, 194, 178))
    rect(x + 40, y + 20, 172, 8, (200, 194, 178))
    disc(x + 126, y + 20, 22, (200, 194, 178))
    rect(x + 104, y + 18, 44, 6, (200, 194, 178))
    # flag
    vline(x + 18, y + 10, y + 60, INK)
    rect(x + 18, y + 10, 30, 16, WHITE)
    hline(x + 18, x + 47, y + 12, BLUE)
    hline(x + 18, x + 47, y + 23, BLUE)
    disc(x + 33, y + 18, 3, BLUE)


def scene_ebola(x, y, w, h):
    # Clinic tent, red cross, virus shapes.
    rect(x, y, w, h, (238, 232, 220))
    tri(x + 30, y + 58, x + 110, y + 58, x + 70, y + 18, (245, 245, 240))
    rect(x + 34, y + 58, 72, 4, (180, 60, 50))
    rect(x + 62, y + 30, 16, 16, RED)
    rect(x + 66, y + 26, 8, 24, RED)
    # virus: spiky discs
    for (vx, vy, vr) in ((180, 26, 12), (216, 48, 9), (196, 62, 7)):
        for ang in range(0, 360, 45):
            import math
            ex = vx + int((vr + 5) * math.cos(math.radians(ang)))
            ey = vy + int((vr + 5) * math.sin(math.radians(ang)))
            line(x + vx, y + vy, x + ex, y + ey, DARKRED)
        disc(x + vx, y + vy, vr, DARKRED)
        disc(x + vx - 3, y + vy - 3, 3, RED)


def scene_nvidia(x, y, w, h):
    # Green chip + rising chart arrow.
    rect(x, y, w, h, (232, 240, 235))
    rect(x + 26, y + 16, 74, 52, (30, 120, 50))
    rect(x + 46, y + 32, 34, 20, (16, 80, 34))
    for px in range(36, 96, 12):
        vline(x + px, y + 8, y + 15, (30, 120, 50))
        vline(x + px, y + 68, y + 75, (30, 120, 50))
    for py in range(26, 62, 12):
        hline(x + 18, x + 25, y + py, (30, 120, 50))
        hline(x + 100, x + 107, y + py, (30, 120, 50))
    # rising arrow
    line(x + 130, y + 62, x + 160, y + 44, GREEN)
    line(x + 160, y + 44, x + 190, y + 48, GREEN)
    line(x + 190, y + 48, x + 228, y + 18, GREEN)
    tri(x + 228, y + 18, x + 214, y + 18, x + 228, y + 32, GREEN)


# ---------------------------------------------------------------- compose
def build():
    rect(0, 0, W, H, PAPER)
    # Masthead
    rect(0, 0, W, 108, NAVY)
    rect(0, 104, W, 4, GOLD)
    draw_text(W // 2, 14, "THE WORLD IN ONE DAY", 5, WHITE, "center")
    draw_text(W // 2, 66, "WEDNESDAY 18 NOVEMBER 2026", 3, GOLD, "center")

    # Hero panel
    hx, hy, hw, hh = 12, 116, 776, 256
    panel(hx, hy, hw, hh)
    scene_hero(hx + 1, hy + 1, hw - 2, 182)
    caption_block(hx, hy + 190, hw, "IRAN STRIKES KUWAIT & BAHRAIN",
                  ["Missiles hit a US air base;", "Bahrain shot several down."],
                  hcol=RED, max_chars=60)
    draw_text(hx + hw - 12, hy + 10, "TOP STORY", 2, GOLD, "right")

    # Grid: 2 rows x 3 cols, 6 panels
    gw, gh, gap = 253, 150, 8
    cells = [
        (scene_kerch, "KERCH BRIDGE HIT",
         ["Bridge span falls", "into the sea."]),
        (scene_apex, "XI MEETS PUTIN",
         ["Meet in Shenzhen", "before Trump talks."]),
        (scene_senate, "PELTOLA WINS ALASKA",
         ["Democrats take the", "Senate, 56-44."]),
        (scene_knesset, "KAHANA IS SPEAKER",
         ["Win for Eisenkot;", "blow to Netanyahu."]),
        (scene_ebola, "EBOLA IN CONGO",
         ["Cases pass 11,000;", "most deaths under 5"]),
        (scene_nvidia, "NVIDIA RECORD",
         ["$115.8B quarter;", "Huang return denied"]),
    ]
    for i, (fn, head, lines) in enumerate(cells):
        cx = 12 + (i % 3) * (gw + gap)
        cy = 380 + (i // 3) * (gh + gap)
        panel(cx, cy, gw, gh)
        fn(cx + 1, cy + 1, gw - 2, 74)
        caption_block(cx, cy + 80, gw, head, lines)

    # Footer: ticker + date repeat
    rect(0, 696, W, 4, GOLD)
    draw_text(W // 2, 710, "ALSO: US LOSES MEASLES-FREE STATUS AFTER 26 YEARS",
              2, INK, "center")
    draw_text(W // 2, 740, "WEDNESDAY 18 NOVEMBER 2026  -  THE WORLD IN ONE DAY",
              2, NAVY, "center")


def main():
    build()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.png"), "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
