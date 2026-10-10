"""Nitro graphics (RGCN tiles, RLCN palette, RCSN screen) <-> PNG.

python -X utf8 tools/gfx.py show NCGR NCLR OUT.png [--screen NSCR] [--cols 32] [--pal N]
"""
import struct
import sys
from pathlib import Path

from PIL import Image


def block(b, magic):
    i = b.find(magic, 0x10)
    assert i >= 0, magic
    return i, struct.unpack_from('<I', b, i + 4)[0]


def ncgr(b):
    """(tiles: list of 64-pixel index lists, bpp, w_tiles, h_tiles, data offset)."""
    i, _ = block(b, b'RAHC')
    h, w, depth = struct.unpack_from('<HHI', b, i + 8)
    size, off = struct.unpack_from('<II', b, i + 0x18), None
    size = struct.unpack_from('<I', b, i + 0x18)[0]
    data_off = i + 0x20
    bpp = 4 if depth == 3 else 8
    data = b[data_off:data_off + size]
    step = 8 * bpp
    tiles = []
    for t in range(len(data) // step):
        tb = data[t * step:(t + 1) * step]
        if bpp == 4:
            px = [v for byte in tb for v in (byte & 15, byte >> 4)]
        else:
            px = list(tb)
        tiles.append(px)
    return tiles, bpp, w, h, data_off


def nclr(b):
    i, _ = block(b, b'TTLP')
    size, off = struct.unpack_from('<II', b, i + 0x10)
    d = b[i + 0x18:i + 0x18 + size]
    out = []
    for k in range(0, len(d) - 1, 2):
        v = struct.unpack_from('<H', d, k)[0]
        out.append(((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31))
    return out


def screen_order(sw, sh):
    """File index of each row-major cell: screens wider than 32 cells are stored as 32-wide blocks, left to right."""
    return [c // 32 * 32 * sh + r * min(32, sw - c // 32 * 32) + c % 32 for r in range(sh) for c in range(sw)]


def nscr(b):
    """(cells wide, cells high, entries in row-major order)."""
    i, _ = block(b, b'NRCS')
    w, h, _, size = struct.unpack_from('<HHII', b, i + 8)
    d = struct.unpack_from(f'<{size // 2}H', b, i + 0x14)
    return w // 8, h // 8, [d[k] for k in screen_order(w // 8, h // 8)]


def render(tiles, pal, bpp, cols=32, screen=None, pal_n=0):
    if screen:
        sw, sh, ents = screen
        im = Image.new('RGB', (sw * 8, sh * 8))
        for k, e in enumerate(ents):
            t, hf, vf, p = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
            if t >= len(tiles):
                continue
            px = tiles[t]
            for y in range(8):
                for x in range(8):
                    v = px[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                    c = pal[(p * 16 + v) % len(pal)] if bpp == 4 else pal[v % len(pal)]
                    im.putpixel(((k % sw) * 8 + x, (k // sw) * 8 + y), c)
        return im
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGB', (cols * 8, rows * 8))
    base = pal_n * 16 if bpp == 4 else 0
    for t, px in enumerate(tiles):
        for y in range(8):
            for x in range(8):
                im.putpixel(((t % cols) * 8 + x, (t // cols) * 8 + y), pal[(base + px[y * 8 + x]) % len(pal)])
    return im


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'show':
        tiles, bpp, w, h, _ = ncgr(Path(a[2]).read_bytes())
        pal = nclr(Path(a[3]).read_bytes())
        scr = nscr(Path(a[a.index('--screen') + 1]).read_bytes()) if '--screen' in a else None
        cols = int(a[a.index('--cols') + 1]) if '--cols' in a else (w if 0 < w < 0xFF else 32)
        pn = int(a[a.index('--pal') + 1]) if '--pal' in a else 0
        print(f'tiles {len(tiles)} bpp {bpp} w {w} h {h} pal {len(pal)}')
        render(tiles, pal, bpp, cols, scr, pn).save(a[4])
