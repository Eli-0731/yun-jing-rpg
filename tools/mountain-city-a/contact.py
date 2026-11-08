"""Contact sheet of every <ID>_option*.png in art/references/<ID>/ -> _contact.jpg (review only, not committed)."""
import sys
from pathlib import Path
from PIL import Image
for d in sys.argv[1:]:
    d = Path(d); ims = [Image.open(p).convert('RGB') for p in sorted(d.glob('*_option*.png'))]
    if not ims: continue
    w = 760; ims = [im.resize((w, int(im.height * w / im.width))) for im in ims]
    h = max(im.height for im in ims); cols = 2; rows = (len(ims) + 1) // 2
    s = Image.new('RGB', (w * cols, h * rows), (200, 200, 200))
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
    s.save(d / '_contact.jpg', quality=85)
    print(d.name, len(ims))
