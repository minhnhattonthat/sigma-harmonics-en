"""The game's texture files (CPK entries starting 04 00 00 00): header of six u32
(fmt=4 [256-colour], wcode, hcode, palette bytes, 0, data bytes), the BGR555 palette (padded to 4), then
linear 8bpp pixels, width 8<<wcode, height 8<<hcode. Colour 0 is transparent.

python -X utf8 tools/tex.py show FILE OUT.png
python -X utf8 tools/tex.py sheet OUT.png FILE...      # several on one image, labelled by name
python -X utf8 tools/tex.py find [--max-h 32]           # list texture files, by size
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def parse(b):
    fmt, wc, hc, pal_n, _, size = struct.unpack_from('<6I', b)
    assert fmt in BPP, fmt
    w, h = 8 << wc, 8 << hc
    pal_off = 24
    data_off = pal_off + (pal_n + 3) // 4 * 4
    pal = [struct.unpack_from('<H', b, pal_off + 2 * i)[0] for i in range(pal_n // 2)]
    return w, h, pal, data_off, size


BPP = {3: 4, 4: 8}  # GX formats: 3 = 16-colour, 4 = 256-colour


def is_tex(b):
    if len(b) < 24 or b[0] not in BPP or b[1:4] != bytes(3):
        return False
    fmt, wc, hc, pal_n, z, size = struct.unpack_from('<6I', b)
    return wc < 8 and hc < 8 and size == (8 << wc) * (8 << hc) * BPP[fmt] // 8 and len(b) >= 24 + pal_n + size - 4


def pixels(b):
    w, h, pal, off, size = parse(b)
    if b[0] == 4:
        return list(b[off:off + w * h])
    return [v for byte in b[off:off + size] for v in (byte & 15, byte >> 4)]


def rgb(v):
    return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)


def image(b):
    w, h, pal, off, _ = parse(b)
    im = Image.new('RGBA', (w, h))
    px = pixels(b)
    im.putdata([(0, 0, 0, 0) if v == 0 else rgb(pal[v]) + (255,) if v < len(pal) else (255, 0, 255, 255) for v in px])
    return im


def encode(im, b):
    """Replace the pixels of texture bytes `b` with RGBA image `im` (same size), quantised to b's palette."""
    w, h, pal, off, size = parse(b)
    cols = [rgb(v) for v in pal]
    idx, cache = [], {}
    orig, before = pixels(b), list(image(b).getdata())
    for i, (r, g, bl, a) in enumerate(im.convert('RGBA').getdata()):
        if (r, g, bl, a) == before[i]:  # untouched pixel: keep its index (palettes repeat colours)
            idx.append(orig[i])
            continue
        if a < 128:
            idx.append(0)
            continue
        key = (r, g, bl)
        if key not in cache:
            cache[key] = min(range(1, len(cols)), key=lambda k: (cols[k][0] - r) ** 2 + (cols[k][1] - g) ** 2 + (cols[k][2] - bl) ** 2)
        idx.append(cache[key])
    out = bytearray(b)
    if b[0] == 4:
        out[off:off + w * h] = bytes(idx)
    else:
        out[off:off + size] = bytes(idx[i] | idx[i + 1] << 4 for i in range(0, len(idx), 2))
    return bytes(out)


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'show':
        image(Path(a[2]).read_bytes()).save(a[3])
    elif a[1] == 'sheet':
        ims = [(Path(f).name, image(Path(f).read_bytes())) for f in a[3:]]
        W = max(i.width for _, i in ims)
        H = sum(i.height + 12 for _, i in ims)
        sheet = Image.new('RGB', (W, H), (60, 60, 60))
        d = ImageDraw.Draw(sheet)
        y = 0
        for n, i in ims:
            d.text((0, y), n, fill=(255, 255, 0))
            sheet.paste(i, (0, y + 12), i)
            y += i.height + 12
        sheet.save(a[2])
    elif a[1] == 'find':
        maxh = int(a[a.index('--max-h') + 1]) if '--max-h' in a else 9999
        for p in sorted(Path('work/cpk').iterdir()):
            b = p.read_bytes()
            if is_tex(b):
                w, h, pal, _, _ = parse(b)
                if h <= maxh:
                    print(p.name, w, h, len(pal))
