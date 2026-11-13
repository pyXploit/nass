"""Render the same Arabic text with and without nass.

Uses PIL's BASIC layout engine, which — unlike Raqm, browsers, and matplotlib
3.11+ — draws one glyph per code point and never reorders.

    python examples/shaping_demo.py docs/shaping.png
"""

from __future__ import annotations

import sys

from PIL import Image, ImageDraw, ImageFont

import nass

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE = 40
CASES = [
    ("مرحبا بالعالم", "plain"),
    ("السلام عليكم", "greeting"),
    ("لا إله إلا الله", "lam-alef"),
    ("كـــتاب", "tatweel"),
    ("صفحة 123", "digits"),
]


def main(out: str) -> None:
    font = ImageFont.truetype(FONT, SIZE, layout_engine=ImageFont.Layout.BASIC)
    label = ImageFont.truetype(FONT, 16)

    width, row = 900, 132
    img = Image.new("RGB", (width, 56 + row * len(CASES)), (244, 241, 234))
    draw = ImageDraw.Draw(img)
    draw.text((30, 18), "raw (top)   vs   nass.display() (red)", font=label, fill=(120, 115, 105))

    y = 56
    for text, note in CASES:
        draw.text((30, y), note, font=label, fill=(150, 145, 135))
        draw.text((30, y + 22), text, font=font, fill=(12, 11, 10))
        draw.text((30, y + 22 + SIZE + 10), nass.display(text), font=font, fill=(226, 61, 28))
        y += row

    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/shaping.png")
