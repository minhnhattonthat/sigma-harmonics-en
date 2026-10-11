"""Give every NFTR font the printable ASCII set (a char missing from a font hangs the game).

Dialogue font (04387, 16px, 3bpp): rasterised from STIX General (OFL, font/), anti-aliased to 8 levels.
Small UI fonts (1bpp 9-13px): the hand-drawn pixel font font/px9.txt.
Existing ASCII glyphs are redrawn in place so a word never mixes two styles.

Orientation comes from CGLP flags (the game is played with the DS sideways):
  0 upright; 2 rotated 90 deg clockwise; 6 rotated 90 deg counter-clockwise. The dialogue font (flags 3, Japanese
  vertical writing) is drawn as flags 2 and dlgfont.py switches its flags, so English runs left-to-right.
Each glyph is drawn upright, left-aligned in its advance box, then rotated into the stored cell.
"""
import struct
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import nftr

FONT_DIR = Path(__file__).resolve().parent.parent / 'font'
ASCII = [chr(c) for c in range(0x20, 0x7F)]
SPACE_ADV = 4
SPACE = 0x2002  # en space: the renderer gives U+0020 and U+3000 a full-cell advance, so English spaces use this
DLG_TTF, DLG_PX = 'STIXGeneral.ttf', 13
BASIC = ImageFont.Layout.BASIC  # not raqm (Pillow's Linux wheels have it): same widths and pixels on every platform


def params(x):
    cglp = nftr._block(x, b'PLGC')
    w, h, size, base, maxw, bpp, flags = struct.unpack_from('<BBHBBBB', cglp, 8)
    return dict(w=w, h=h, size=size, base=base, bpp=bpp, flags=flags)


@lru_cache(None)
def _ttf(name, px):
    return ImageFont.truetype(str(FONT_DIR / name), px, layout_engine=BASIC)


@lru_cache(None)
def px9():
    """{char: rows} from font/px9.txt."""
    out, cur = {}, None
    for line in (FONT_DIR / 'px9.txt').read_text(encoding='utf-8').split('\n'):
        if line.startswith('# '):  # comment; glyph rows never contain spaces
            continue
        if line.startswith('='):
            cur = line[1:2] or ' '  # editors strip the trailing space of "= "
            out[cur] = []
        elif line and cur is not None:
            out[cur].append(line)
    for ch, rows in out.items():
        assert len(rows) == 9 and len({len(r) for r in rows}) == 1, f'px9.txt: bad glyph {ch!r}'
    return out


def raster_ttf(ch, ttf, px, w, h, base, bpp):
    """Upright glyph as rows of levels 0..2^bpp-1 (w x h), and its advance."""
    f = _ttf(ttf, px)
    if ch == ' ':
        return [[0] * w for _ in range(h)], SPACE_ADV
    im = Image.new('L', (w * 2, h), 0)
    ImageDraw.Draw(im).text((2, base), ch, font=f, fill=255, anchor='ls')
    top = (1 << bpp) - 1
    l, _, r, _ = im.point(lambda v: 255 if round(v * top / 255) else 0).getbbox()  # ink that survives quantising
    adv = min(w, r - l)      # ink width; the renderer adds 1 px between glyphs
    return [[round(im.getpixel((l + x, y)) * top / 255) if x < adv else 0 for x in range(w)]
            for y in range(h)], adv


def dlg_ttf():
    return _ttf(DLG_TTF, DLG_PX)


def dlg_glyph(s, p):
    """Dialogue-font glyph for string `s` (one char or a chunk), upright for the player: drawn at its natural
    advance, rotated into the cell like the flags-2 fonts. Widths (left, glyphWidth, advance): glyphWidth is the
    full cell because the blitter copies that many raw-x columns (docs/re/README.md)."""
    f, top = dlg_ttf(), (1 << p['bpp']) - 1
    adv = round(f.getlength(s)) if s != ' ' else SPACE_ADV
    im = Image.new('L', (p['h'], p['w']), 0)  # upright: width along the advance (cell h), height = cell w
    ImageDraw.Draw(im).text((0, p['base']), s, font=f, fill=255, anchor='ls')
    rows = [[round(im.getpixel((x, y)) * top / 255) for x in range(p['h'])] for y in range(p['w'])]
    return pack(orient(rows, 2, p['w'], p['h']), p['bpp'], p['size']), (0, p['w'], adv)


def raster_px9(ch, w, h, base, bpp):
    """Upright pixel glyph placed so its baseline (under px9 row 6) sits 2 rows above the cell baseline,
    as the game's own 9px glyphs fill the cell to the bottom."""
    g = px9()[ch]
    top = (1 << bpp) - 1
    dy = max(0, min(base, h) - 9)
    rows = [[0] * w for _ in range(h)]
    for y, r in enumerate(g):
        if 0 <= y + dy < h:
            for x, c in enumerate(r[:w]):
                rows[y + dy][x] = top if c == '#' else 0
    return rows, min(w, len(g[0]))


def orient(rows, flags, w, h):
    """Upright rows (W_up x H_up) -> stored cell (w x h)."""
    hu, wu = len(rows), len(rows[0])
    out = [[0] * w for _ in range(h)]
    for y in range(hu):
        for x in range(wu):
            v = rows[y][x]
            if not v:
                continue
            if flags == 0:
                out[y][x] = v
            elif flags == 2:
                out[x][hu - 1 - y] = v
            elif flags == 6:
                out[w - 1 - x][y] = v      # anchored to the far side of the cell, like the game's glyphs
            else:
                raise NotImplementedError(f'CGLP flags {flags}')
    return out


def pack(rows, bpp, size):
    bits = ''.join(f'{v:0{bpp}b}' for r in rows for v in r)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)).ljust(size, b'\0')[:size]


def glyphs(x):
    """{code: (bitmap, left, width, advance)} for the full ASCII set in this font's format."""
    p = params(x)
    rotated = p['flags'] in (2, 6)
    wu, hu = (p['h'], p['w']) if rotated else (p['w'], p['h'])
    out = {}
    for ch in ASCII:
        if p['flags'] == 3:  # the dialogue font, switched to flags 2 by dlgfont.py: upright for the player
            bitmap, widths = dlg_glyph(ch, p)
            out[ord(ch)] = (bitmap, *widths)
            out[fullwidth(ch)] = out[ord(ch)]
            continue
        else:
            rows, adv = raster_px9(ch, wu, hu, hu, p['bpp'])
            stored = orient(rows, p['flags'], p['w'], p['h'])
            inked = [x for r in stored for x, v in enumerate(r) if v]
            width = max(inked) + 1 if inked else 0
            adv += 1
        out[ord(ch)] = (pack(stored, p['bpp'], p['size']), 0, width, adv)
        out[fullwidth(ch)] = out[ord(ch)]
    return out


def fullwidth(ch):
    """Full-width twin of an ASCII char: some UI routines only step 3-byte UTF-8, so those tables get these."""
    return SPACE if ch == ' ' else ord(ch) - 0x21 + 0xFF01


def set_glyph(x, idx, bitmap, widths):
    """Overwrite glyph `idx` in place (same size)."""
    x = bytearray(x)
    cglp_at = struct.unpack_from('<I', x, 0x10 + 0x10)[0] - 8
    cwdh_at = struct.unpack_from('<I', x, 0x10 + 0x14)[0] - 8
    size = struct.unpack_from('<H', x, cglp_at + 0xA)[0]
    x[cglp_at + 0x10 + idx * size:cglp_at + 0x10 + (idx + 1) * size] = bitmap
    x[cwdh_at + 0x10 + 3 * idx:cwdh_at + 0x13 + 3 * idx] = bytes(widths)
    return bytes(x)


KEEP = range(0x30, 0x3b)  # the game's own ASCII digits and ':' (play time, counters): drawn into tight canvases


def add_ascii(x):
    """Font bytes with every ASCII glyph present and drawn in our Latin style (native digits and ':' kept)."""
    have = nftr.codes(x)
    gl = glyphs(x)
    keep = () if params(x)['flags'] == 3 else KEEP  # the dialogue font's direction changes, so it takes ours
    new = {}
    for code, g in gl.items():
        idx = nftr.lookup(x, code) if code in have else None
        if idx is None:
            new[code] = g
        elif code != 0x20 and code not in keep:  # keep the game's own space (glyph 0); English uses SPACE
            x = set_glyph(x, idx, g[0], g[1:])
    return nftr.add_glyphs(x, new) if new else x
