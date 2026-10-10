"""Preview a font's glyphs as stored (no un-rotation): python tools/fontview.py FONT OUT.png [chars]"""
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import latin  # noqa: E402
import nftr  # noqa: E402


def bitmap(x, idx):
    p = latin.params(x)
    bits = ''.join(f'{b:08b}' for b in nftr.glyph(x, idx))
    bpp, top = p['bpp'], (1 << p['bpp']) - 1
    return [[int(bits[(y * p['w'] + i) * bpp:(y * p['w'] + i + 1) * bpp], 2) * 255 // top
             for i in range(p['w'])] for y in range(p['h'])]


def sheet(x, chars, scale=4, cols=16):
    p = latin.params(x)
    w, h = p['w'] + 1, p['h'] + 1
    rows = (len(chars) + cols - 1) // cols
    im = Image.new('L', (cols * w, rows * h), 60)
    for k, ch in enumerate(chars):
        idx = nftr.lookup(x, ord(ch))
        if idx is None:
            continue
        b = bitmap(x, idx)
        for y in range(p['h']):
            for i in range(p['w']):
                im.putpixel(((k % cols) * w + i, (k // cols) * h + y), 255 - b[y][i])
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


if __name__ == '__main__':
    x = Path(sys.argv[1]).read_bytes()
    chars = sys.argv[3] if len(sys.argv) > 3 else ''.join(latin.ASCII)
    sheet(x, chars).save(sys.argv[2])
