"""Build the two install icons from the simple Qingxi training-yard mark."""

from pathlib import Path
from PIL import Image, ImageDraw


for size in (192, 512):
    scale = size / 192
    image = Image.new("RGB", (size, size), "#18392f")
    draw = ImageDraw.Draw(image)
    points = [(35, 125), (96, 56), (157, 125)]
    draw.line([(round(x * scale), round(y * scale)) for x, y in points], fill="#d9c494", width=round(12 * scale), joint="curve")
    for start, end in (((43, 137), (149, 137)), ((66, 92), (66, 137)), ((126, 92), (126, 137))):
        draw.line(tuple((round(x * scale), round(y * scale)) for x, y in (start, end)), fill="#a6b99e", width=round(10 * scale))
    cx, cy, radius = 96 * scale, 113 * scale, 9 * scale
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill="#d9c494")
    image.save(Path(__file__).with_name(f"icon-{size}.png"))
