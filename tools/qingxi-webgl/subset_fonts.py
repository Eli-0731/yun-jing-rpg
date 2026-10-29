"""Cut the bundled Noto fonts down for the browser build.

The full Noto Sans TC / Serif TC variable fonts are 27.5 MB in the WebGL download. The game only needs
Traditional Chinese text, so the subset keeps:
  - the 5,401 common characters of Big5 level 1 (A440-C67E), which covers everyday Traditional Chinese;
  - every character used in the game's own text (scripts, layout data, Resources text);
  - ASCII, Latin-1, general and CJK punctuation, arrows, fullwidth forms.
Each variable font is pinned to one weight (Sans 400 for text, Serif 600 for titles).

python tools/qingxi-webgl/subset_fonts.py
Sources: art/fonts/Noto*TC-Variable.ttf (SIL OFL 1.1). Output: apps/game/Assets/YunJing/Resources/Fonts/*-Subset.ttf
"""
import glob
import os

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "art", "fonts")
OUT = os.path.join(ROOT, "apps", "game", "Assets", "YunJing", "Resources", "Fonts")


def characters():
    chars = set()
    for hi in range(0xA4, 0xC7):            # Big5 level 1: A440..C67E
        for lo in list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF)):
            if (hi, lo) > (0xC6, 0x7E):
                break
            try:
                chars.add(bytes([hi, lo]).decode("big5"))
            except UnicodeDecodeError:
                pass
    for a, b in [(0x20, 0x7E), (0xA0, 0xFF), (0x2000, 0x206F), (0x2190, 0x21FF), (0x2460, 0x24FF),
                 (0x25A0, 0x25FF), (0x3000, 0x303F), (0x30FB, 0x30FB), (0xFF00, 0xFFEF)]:
        chars.update(chr(c) for c in range(a, b + 1))
    patterns = ["apps/game/Assets/**/*.cs", "apps/game/Assets/**/*.json", "apps/game/Assets/**/*.txt",
                "tools/qingxi-terrain/*.json"]
    for pattern in patterns:
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            try:
                with open(path, encoding="utf-8") as f:
                    chars.update(ch for ch in f.read() if ord(ch) > 0x7F)
            except (UnicodeDecodeError, OSError):
                pass
    return chars


def build(source, weight, target, chars):
    font = TTFont(os.path.join(SRC, source))
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": weight})
    options = subset.Options()
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    sub = subset.Subsetter(options)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(font)
    path = os.path.join(OUT, target)
    font.save(path)
    print(f"{target}: {len(font.getGlyphOrder())} glyphs, {os.path.getsize(path) / 1e6:.2f} MB")


if __name__ == "__main__":
    chars = characters()
    print(f"{len(chars)} characters")
    build("NotoSansTC-Variable.ttf", 400, "NotoSansTC-Subset.ttf", chars)
    build("NotoSerifTC-Variable.ttf", 600, "NotoSerifTC-Subset.ttf", chars)
