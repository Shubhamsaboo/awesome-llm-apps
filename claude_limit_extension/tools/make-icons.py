#!/usr/bin/env python3
"""Generate PNG toolbar icons for the extension.

Deterministic output: rounded-rect gradient from Claude orange to a darker
burnt-orange, with a stylised "C" glyph and a bottom gauge tick to hint at
"limits". Run once, commit the PNGs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CLAUDE_ORANGE = (204, 120, 92)
CLAUDE_ORANGE_DARK = (160, 88, 64)
CLAUDE_CREAM = (246, 240, 234)
INK = (27, 27, 27)


def rounded_gradient(size: int) -> Image.Image:
    """Rounded square with a diagonal gradient orange -> darker orange."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    px = grad.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            r = int(CLAUDE_ORANGE[0] * (1 - t) + CLAUDE_ORANGE_DARK[0] * t)
            g = int(CLAUDE_ORANGE[1] * (1 - t) + CLAUDE_ORANGE_DARK[1] * t)
            b = int(CLAUDE_ORANGE[2] * (1 - t) + CLAUDE_ORANGE_DARK[2] * t)
            px[x, y] = (r, g, b, 255)

    # Rounded mask
    radius = max(2, size // 5)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def draw_glyph(img: Image.Image) -> None:
    """A soft 'C' + a small semicircular gauge at the bottom."""
    size = img.width
    draw = ImageDraw.Draw(img)

    # Big 'C' — arc, not text, so we don't depend on a font being present.
    stroke_w = max(2, size // 10)
    pad = size * 0.20
    box = (pad, pad, size - pad, size - pad)
    draw.arc(box, start=45, end=315, fill=CLAUDE_CREAM, width=stroke_w)

    # A tiny gauge tick — three short arcs bottom-left, hinting at "limits".
    tick_y = size * 0.86
    tick_len = size * 0.09
    tick_gap = size * 0.04
    tick_w = max(1, size // 24)
    for i in range(3):
        x0 = size * 0.18 + i * (tick_len + tick_gap)
        draw.line([(x0, tick_y), (x0 + tick_len, tick_y)], fill=CLAUDE_CREAM, width=tick_w)


def render(size: int) -> Image.Image:
    """Anti-aliased render: draw at 4× then downscale."""
    scale = 4 if size <= 48 else 2
    big_size = size * scale
    img = rounded_gradient(big_size)
    draw_glyph(img)
    if scale > 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="Output icons directory")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    for size in (16, 32, 48, 128):
        img = render(size)
        target = args.out / f"icon-{size}.png"
        img.save(target, format="PNG", optimize=True)
        print(f"wrote {target} ({size}x{size})")


if __name__ == "__main__":
    main()
