#!/usr/bin/env python3
"""Build hover.gif — a looping cyan sheet-ghost for the profile README."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

SCALE = 4
CANVAS = (59, 79)  # 236 x 316 after scale, same as a typical profile GIF
FRAMES = 8
DURATION_MS = 150
CYAN = (61, 220, 255, 255)
SPARK = (147, 147, 147, 255)

BODY_ART = """
              #####
           ###     ###
         ##           ##
        #               #
       #                 #
      #                   #
      #                   #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
     #                     #
      #                   #
      #                   #
       #                 #
       #                 #
        #   #    #    # #
         ##   #   #  ##
           ##  #  ##
             ## ##
"""

DIGIT_4 = ["# #", "# #", "###", "  #", "  #"]
DIGIT_2 = ["###", "  #", "###", "#  ", "###"]


def parse_art(art: str) -> tuple[list[tuple[int, int]], int, int]:
    lines = [ln.rstrip("\n") for ln in art.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    width = max(len(ln) for ln in lines)
    lines = [ln.ljust(width) for ln in lines]
    pts = [
        (x, y)
        for y, ln in enumerate(lines)
        for x, ch in enumerate(ln)
        if ch == "#"
    ]
    return pts, width, len(lines)


def parse_glyph(rows: list[str]) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y, row in enumerate(rows)
        for x, ch in enumerate(row)
        if ch == "#"
    ]


BODY, BODY_W, BODY_H = parse_art(BODY_ART)
GLYPH_4 = parse_glyph(DIGIT_4)
GLYPH_2 = parse_glyph(DIGIT_2)
CX = BODY_W // 2


def blit(
    img: Image.Image,
    pts: list[tuple[int, int]],
    ox: int,
    oy: int,
    color: tuple[int, int, int, int] = CYAN,
) -> None:
    w, h = img.size
    put = img.putpixel
    for x, y in pts:
        xx, yy = x + ox, y + oy
        if 0 <= xx < w and 0 <= yy < h:
            put((xx, yy), color)


def sparkle(img: Image.Image, cx: int, cy: int, phase: int) -> None:
    if phase in (6, 7):
        return
    size = {0: 1, 1: 2, 2: 3, 3: 4, 4: 3, 5: 1}[phase]
    w, h = img.size
    put = img.putpixel

    def dot(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h:
            put((x, y), SPARK)

    dot(cx, cy)
    if size >= 2:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            dot(cx + dx, cy + dy)
    if size >= 3:
        for dx, dy in (
            (-2, 0),
            (2, 0),
            (0, -2),
            (0, 2),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 1),
        ):
            dot(cx + dx, cy + dy)
    if size >= 4:
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            dot(cx + dx, cy + dy)


def eyes(blink: bool) -> list[tuple[int, int]]:
    y = 10
    if blink:
        return [(CX - 6, y), (CX - 5, y), (CX + 5, y), (CX + 6, y)]
    return [
        (CX - 7, y),
        (CX - 6, y),
        (CX - 5, y),
        (CX + 5, y),
        (CX + 6, y),
        (CX + 7, y),
    ]


def mouth() -> list[tuple[int, int]]:
    y = 13
    return [(CX - 2, y), (CX - 1, y), (CX, y), (CX + 1, y), (CX + 2, y)]


def wisp(phase: int) -> list[tuple[int, int]]:
    t = 2 * math.pi * phase / FRAMES
    hem = [(x, y) for x, y in BODY if y >= BODY_H - 5]
    x0 = min(x for x, _ in hem)
    y0 = max(y for _, y in hem) - 2
    pts: list[tuple[int, int]] = []
    for i in range(26):
        sway = math.sin(t + i * 0.36) * 1.8
        drift = -i * 0.22 if i < 14 else -14 * 0.22 + (i - 14) * 0.12
        xx = int(round(x0 + drift + sway))
        yy = y0 + i
        pts.append((xx, yy))
        if 5 <= i <= 20 and i % 4 == 0:
            pts.append((xx - 1, yy))
    return pts


def frame(i: int) -> Image.Image:
    img = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    bob = int(round(math.sin(2 * math.pi * i / FRAMES) * 2))
    ox, oy = 10, 6 + bob
    blit(img, BODY, ox, oy)
    blit(img, eyes(i == 5), ox, oy)
    blit(img, mouth(), ox, oy)
    blit(img, GLYPH_4, ox + CX - 5, oy + 17)
    blit(img, GLYPH_2, ox + CX + 1, oy + 17)
    blit(img, wisp(i), ox, oy)
    sparkle(img, ox + BODY_W - 5, oy + 2, i)
    return img.resize((CANVAS[0] * SCALE, CANVAS[1] * SCALE), Image.NEAREST)


def to_indexed(im: Image.Image) -> Image.Image:
    alpha = im.split()[-1]
    mask = alpha.point(lambda a: 255 if a > 128 else 0)
    rgb = Image.new("RGB", im.size, (0, 0, 0))
    rgb.paste(im.convert("RGB"), mask=mask)
    pal = Image.new("P", (1, 1))
    pal.putpalette([0, 0, 0, 61, 220, 255, 147, 147, 147] + [0] * (256 * 3 - 9))
    quantized = rgb.quantize(palette=pal, dither=Image.NONE)
    pixels, matte = quantized.load(), mask.load()
    w, h = quantized.size
    for y in range(h):
        for x in range(w):
            if matte[x, y] == 0:
                pixels[x, y] = 0
    return quantized


def main() -> None:
    out = Path(__file__).resolve().parent / "hover.gif"
    frames = [to_indexed(frame(i)) for i in range(FRAMES)]
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
