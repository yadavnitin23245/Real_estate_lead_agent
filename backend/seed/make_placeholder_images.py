"""Generate the bundled placeholder property images in ``seed/assets``.

These are simple flat illustrations drawn with Pillow (no third-party photos,
so there is no licensing question). Swap in your own CC0 photos by dropping
files named ``<category>_<n>.jpg`` into ``seed/assets``; categories are
apartment, house, villa, plot, commercial and interior.

    python -m seed.make_placeholder_images
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

W, H = 1280, 800
OUT = Path(__file__).parent / "assets"

Color = tuple[int, int, int]


def _sky(draw: ImageDraw.ImageDraw, top: Color, bottom: Color, horizon: int) -> None:
    for y in range(horizon):
        t = y / max(horizon - 1, 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)


def _ground(draw: ImageDraw.ImageDraw, horizon: int, color: Color) -> None:
    draw.rectangle([0, horizon, W, H], fill=color)


def _tree(draw: ImageDraw.ImageDraw, x: int, base: int, s: float, leaf: Color) -> None:
    draw.rectangle([x - 6 * s, base - 70 * s, x + 6 * s, base], fill=(110, 80, 55))
    draw.ellipse([x - 45 * s, base - 160 * s, x + 45 * s, base - 55 * s], fill=leaf)
    draw.ellipse([x - 30 * s, base - 185 * s, x + 35 * s, base - 110 * s], fill=leaf)


def _cloud(draw: ImageDraw.ImageDraw, x: int, y: int, s: float) -> None:
    for dx, dy, r in [(0, 0, 40), (45, -15, 50), (95, 0, 40), (50, 10, 45)]:
        draw.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s],
                     fill=(255, 255, 255))


def _windows(draw, x0, y0, x1, y1, cols, rows, glass: Color, rng: random.Random) -> None:
    cw = (x1 - x0) / cols
    rh = (y1 - y0) / rows
    for c in range(cols):
        for r in range(rows):
            lit = rng.random() < 0.25
            fill = (250, 222, 140) if lit else glass
            draw.rectangle([x0 + c * cw + cw * 0.2, y0 + r * rh + rh * 0.2,
                            x0 + c * cw + cw * 0.8, y0 + r * rh + rh * 0.75], fill=fill)


def apartment(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 640
    _sky(d, (120, 175, 230), (215, 232, 248), horizon)
    for _ in range(3):
        _cloud(d, rng.randint(50, 1100), rng.randint(60, 220), rng.uniform(0.7, 1.3))
    _ground(d, horizon, (120, 160, 95))
    palettes = [(232, 224, 210), (214, 200, 186), (240, 236, 228), (200, 210, 220)]
    x = rng.randint(60, 140)
    while x < W - 200:
        bw = rng.randint(220, 320)
        top = rng.randint(90, 300)
        body = rng.choice(palettes)
        d.rectangle([x, top, x + bw, horizon], fill=body)
        d.rectangle([x, top, x + bw, top + 18], fill=tuple(max(0, c - 40) for c in body))
        floors = (horizon - top - 40) // 42
        _windows(d, x + 15, top + 30, x + bw - 15, horizon - 20, 4, floors, (120, 150, 175), rng)
        # balconies
        for f in range(floors):
            y = top + 30 + f * ((horizon - top - 50) / floors) + 28
            d.line([(x + 10, y), (x + bw - 10, y)], fill=(90, 90, 90), width=3)
        x += bw + rng.randint(30, 80)
    for tx in range(40, W, rng.randint(150, 220)):
        _tree(d, tx, horizon + 20, rng.uniform(0.8, 1.2), (70, 130, 70))
    d.rectangle([0, horizon + 80, W, horizon + 140], fill=(110, 110, 115))
    return img


def house(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 600
    _sky(d, (140, 190, 235), (225, 238, 250), horizon)
    _cloud(d, rng.randint(80, 400), 120, 1.1)
    _cloud(d, rng.randint(700, 1050), 90, 0.9)
    _ground(d, horizon, (115, 165, 90))
    wall = rng.choice([(238, 220, 190), (225, 205, 180), (245, 240, 230)])
    roof = rng.choice([(170, 70, 55), (120, 75, 60), (90, 95, 110)])
    x0, x1 = 340, 940
    d.rectangle([x0, 340, x1, horizon + 20], fill=wall)
    d.polygon([(x0 - 50, 350), ((x0 + x1) // 2, 170), (x1 + 50, 350)], fill=roof)
    d.rectangle([600, 450, 680, horizon + 20], fill=(120, 80, 50))
    for wx in (400, 760):
        d.rectangle([wx, 400, wx + 120, 500], fill=(140, 175, 200))
        d.line([(wx + 60, 400), (wx + 60, 500)], fill=wall, width=5)
    d.polygon([(560, H), (720, H), (690, horizon + 20), (590, horizon + 20)], fill=(190, 180, 165))
    _tree(d, 180, horizon + 30, 1.4, (60, 125, 65))
    _tree(d, 1100, horizon + 30, 1.2, (75, 140, 70))
    d.rectangle([0, horizon + 40, 300, horizon + 60], fill=(235, 235, 235))
    d.rectangle([980, horizon + 40, W, horizon + 60], fill=(235, 235, 235))
    return img


def villa(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 560
    _sky(d, (95, 160, 225), (205, 228, 250), horizon)
    _ground(d, horizon, (105, 160, 85))
    wall = rng.choice([(248, 246, 240), (236, 228, 214)])
    d.rectangle([220, 300, 760, horizon + 40], fill=wall)
    d.rectangle([700, 190, 1080, horizon + 40], fill=tuple(c - 12 for c in wall))
    d.rectangle([200, 285, 780, 305], fill=(80, 80, 85))
    d.rectangle([680, 175, 1100, 195], fill=(80, 80, 85))
    d.rectangle([260, 340, 700, 470], fill=(130, 170, 200))
    for gx in range(260, 700, 88):
        d.line([(gx, 340), (gx, 470)], fill=(240, 240, 240), width=4)
    _windows(d, 730, 220, 1050, 520, 3, 3, (130, 170, 200), rng)
    d.rectangle([260, horizon + 70, 860, horizon + 150], fill=(80, 170, 210))
    d.rectangle([250, horizon + 60, 870, horizon + 70], fill=(225, 225, 220))
    for tx in (120, 1180):
        _tree(d, tx, horizon + 40, 1.5, (55, 120, 60))
    return img


def plot(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 420
    _sky(d, (130, 185, 235), (225, 238, 250), horizon)
    # hills
    d.polygon([(0, horizon), (250, 300), (520, horizon)], fill=(110, 140, 110))
    d.polygon([(380, horizon), (720, 270), (1050, horizon)], fill=(95, 130, 100))
    d.polygon([(900, horizon), (1150, 320), (W, horizon)], fill=(115, 145, 115))
    _ground(d, horizon, rng.choice([(180, 155, 110), (165, 145, 105)]))
    # boundary posts and wire
    pts = [(120, 760), (420, 470), (1000, 470), (1180, 760)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]):
        steps = 8
        for i in range(steps):
            px = xa + (xb - xa) * i / steps
            py = ya + (yb - ya) * i / steps
            d.rectangle([px - 5, py - 45, px + 5, py], fill=(225, 225, 225))
        d.line([(xa, ya - 30), (xb, yb - 30)], fill=(90, 90, 90), width=2)
    # blank sign board
    d.rectangle([600, 380, 610, 470], fill=(90, 70, 50))
    d.rectangle([540, 330, 670, 395], fill=(245, 245, 240), outline=(60, 60, 60), width=3)
    for tx in (60, 300, 1100, 1230):
        _tree(d, tx, horizon + 10, 0.8, (70, 125, 70))
    return img


def commercial(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 650
    _sky(d, (110, 170, 230), (215, 232, 250), horizon)
    _ground(d, horizon, (150, 150, 155))
    glass = rng.choice([(95, 140, 175), (85, 125, 150)])
    d.rectangle([260, 120, 1020, horizon], fill=glass)
    for gx in range(260, 1020, 76):
        d.line([(gx, 120), (gx, horizon)], fill=(200, 210, 220), width=3)
    for gy in range(120, horizon, 60):
        d.line([(260, gy), (1020, gy)], fill=(200, 210, 220), width=3)
    d.rectangle([240, 520, 1040, horizon], fill=(60, 60, 65))
    for sx in range(270, 1010, 190):
        d.rectangle([sx, 540, sx + 160, horizon - 5], fill=(240, 220, 160))
    d.rectangle([240, 500, 1040, 520], fill=(200, 80, 60))
    d.rectangle([0, horizon + 50, W, horizon + 60], fill=(240, 240, 240))
    _tree(d, 120, horizon + 20, 1.2, (70, 130, 70))
    _tree(d, 1160, horizon + 20, 1.2, (70, 130, 70))
    return img


def interior(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    wall = rng.choice([(238, 232, 222), (226, 232, 236), (240, 228, 214)])
    d.rectangle([0, 0, W, 560], fill=wall)
    for y in range(560, H):
        t = (y - 560) / (H - 560)
        d.line([(0, y), (W, y)], fill=(int(190 - 40 * t), int(160 - 35 * t), int(120 - 30 * t)))
    # window with daylight
    d.rectangle([760, 90, 1160, 450], fill=(200, 225, 245), outline=(250, 250, 250), width=12)
    d.line([(960, 90), (960, 450)], fill=(250, 250, 250), width=10)
    # sofa
    sofa = rng.choice([(90, 110, 130), (130, 100, 85), (100, 120, 100)])
    d.rounded_rectangle([140, 390, 680, 600], radius=30, fill=sofa)
    d.rounded_rectangle([170, 330, 650, 450], radius=30, fill=tuple(min(255, c + 20) for c in sofa))
    d.rounded_rectangle([110, 420, 190, 610], radius=20, fill=sofa)
    d.rounded_rectangle([630, 420, 710, 610], radius=20, fill=sofa)
    # rug + table
    d.ellipse([220, 640, 760, 760], fill=(225, 210, 185))
    d.rectangle([360, 620, 620, 645], fill=(120, 85, 60))
    # lamp & plant
    d.line([(1220, 560), (1220, 300)], fill=(60, 60, 60), width=6)
    d.polygon([(1180, 300), (1260, 300), (1240, 240), (1200, 240)], fill=(245, 230, 190))
    d.rectangle([840, 540, 900, 600], fill=(170, 110, 80))
    d.ellipse([810, 430, 930, 560], fill=(80, 140, 85))
    # picture frame
    d.rectangle([300, 120, 520, 270], fill=(250, 250, 250), outline=(70, 60, 50), width=8)
    d.polygon([(320, 250), (400, 170), (460, 230), (500, 200), (500, 250)], fill=(120, 160, 140))
    return img


GENERATORS = {
    "apartment": (apartment, 4),
    "house": (house, 2),
    "villa": (villa, 2),
    "plot": (plot, 2),
    "commercial": (commercial, 2),
    "interior": (interior, 3),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for category, (fn, n) in GENERATORS.items():
        for i in range(1, n + 1):
            rng = random.Random(f"{category}-{i}")
            img = fn(rng).filter(ImageFilter.SMOOTH)
            if i % 2 == 0:
                img = ImageOps.mirror(img)  # cheap extra variety
            path = OUT / f"{category}_{i}.jpg"
            img.save(path, "JPEG", quality=85, optimize=True)
            print("wrote", path.name)


if __name__ == "__main__":
    main()
