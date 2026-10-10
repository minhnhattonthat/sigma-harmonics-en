"""NFTR font read/patch helpers (from the tokyo-majin-gakuen-kenpuuchou repo).

NFTR: 'RTFN', u32 file size @8, u16 header size @0xC, u16 block count @0xE, then blocks
[magic, u32 size, ...]. FINF @0x10 holds pointers (block start + 8) to CGLP @+0x10, CWDH @+0x14,
CMAP @+0x18. CGLP: cell w @+8, h @+9, u16 bytes/glyph @+0xA, 2bpp bitmaps @+0x10 (MSB-first).
CWDH: u16 first @+8, last @+0xA, u32 next @+0xC, 3 bytes/glyph @+0x10 (left, glyph width, advance).
CMAP: u16 first @+8, last @+0xA, u16 type @+0xC, u32 next @+0x10, data @+0x14. Codes are Unicode.
"""
import struct


STROKE, SHADOW, CORNER = 1, 2, 3     # palette indices used by the game's glyphs (stroke + drop shadow)


def _pad(b):
    return bytearray(b) + bytes(-len(b) % 4)


def _blocks(x):
    hs, n = struct.unpack_from('<HH', x, 0xC)
    p, out = hs, []
    for _ in range(n):
        size, = struct.unpack_from('<I', x, p + 4)
        out.append([bytes(x[p:p + 4]), bytearray(x[p:p + size])])
        p += size
    return bytes(x[:hs]), out


def _block(x, magic):
    _, blocks = _blocks(x)
    return next(b for t, b in blocks if t == magic)


def info(x):
    cglp, cwdh = _block(x, b'PLGC'), _block(x, b'HDWC')
    return cglp[8], cglp[9], struct.unpack_from('<H', cwdh, 0xA)[0] + 1


def glyph(x, i):
    cglp = _block(x, b'PLGC')
    cs, = struct.unpack_from('<H', cglp, 0xA)
    return bytes(cglp[0x10 + i * cs:0x10 + (i + 1) * cs])


def widths(x, i):
    return tuple(_block(x, b'HDWC')[0x10 + 3 * i:0x13 + 3 * i])


def render(rows, cell_w, cell_h):
    h, w = len(rows), len(rows[0])

    def ink(x, y):
        return 0 <= y < h and 0 <= x < w and rows[y][x] == '#'

    px = [STROKE if ink(x, y) else SHADOW if ink(x - 1, y) or ink(x, y - 1)
          else CORNER if ink(x - 1, y - 1) else 0
          for y in range(cell_h) for x in range(cell_w)]
    px += [0] * (-len(px) % 4)
    return bytes(px[i] << 6 | px[i + 1] << 4 | px[i + 2] << 2 | px[i + 3] for i in range(0, len(px), 4))


def lookup(x, code):
    """Glyph index as the game finds it: the FIRST CMAP block whose range holds the code decides."""
    p, = struct.unpack_from('<I', x, 0x10 + 0x18)
    while p:
        b = p - 8
        first, last, typ = struct.unpack_from('<HHH', x, b + 8)
        nxt, = struct.unpack_from('<I', x, b + 0x10)
        d = b + 0x14
        if first <= code <= last:
            if typ == 0:
                return struct.unpack_from('<H', x, d)[0] + code - first
            if typ == 1:
                g, = struct.unpack_from('<H', x, d + 2 * (code - first))
                return None if g == 0xFFFF else g
            for k in range(struct.unpack_from('<H', x, d)[0]):
                c, g = struct.unpack_from('<HH', x, d + 2 + 4 * k)
                if c == code:
                    return g
            return None
        p = nxt
    return None


def _map_code(blk, code, idx):
    """Point `code` at glyph `idx` inside the CMAP block that owns its range."""
    first, typ = struct.unpack_from('<H', blk, 8)[0], struct.unpack_from('<H', blk, 0xC)[0]
    if typ == 1:
        struct.pack_into('<H', blk, 0x14 + 2 * (code - first), idx)
    elif typ == 2:
        count, = struct.unpack_from('<H', blk, 0x14)
        pairs = dict(struct.unpack_from('<HH', blk, 0x16 + 4 * k) for k in range(count))
        pairs[code] = idx                       # the game binary-searches, so keep codes sorted
        blk[:] = _pad(blk[:0x14] + struct.pack('<H', len(pairs))
                      + b''.join(struct.pack('<HH', c, g) for c, g in sorted(pairs.items())))
    else:
        raise ValueError(f'U+{code:04X} falls in a direct CMAP block')


def add_glyphs(x, new):
    """Append glyphs and map their codes in the existing CMAP chain. The game stops at the first
    CMAP block whose range holds a code, so new codes must go into the block that owns them."""
    head, blocks = _blocks(x)
    tags = [t for t, _ in blocks]
    finf, cglp, cwdh = (blocks[tags.index(t)][1] for t in (b'FNIF', b'PLGC', b'HDWC'))
    cs, = struct.unpack_from('<H', cglp, 0xA)
    first, last = struct.unpack_from('<HH', cwdh, 8)
    if first != 0:
        raise ValueError('expected a single CWDH block covering all glyphs')
    at, p = {}, len(head)                       # original chain, followed by pointer
    for _, b in blocks:
        at[p + 8] = b
        p += len(b)
    chain, ptr = [], struct.unpack_from('<I', finf, 0x18)[0]
    while ptr:
        chain.append(at[ptr])
        ptr, = struct.unpack_from('<I', at[ptr], 0x10)
    n = last + 1
    codes = sorted(new)
    cglp[:] = _pad(cglp[:0x10 + n * cs] + b''.join(new[c][0] for c in codes))
    cwdh[:] = _pad(cwdh[:0x10 + 3 * n] + b''.join(bytes(new[c][1:]) for c in codes))
    struct.pack_into('<H', cwdh, 0xA, n + len(codes) - 1)
    for k, c in enumerate(codes):
        owner = next((b for b in chain if struct.unpack_from('<H', b, 8)[0] <= c
                      <= struct.unpack_from('<H', b, 0xA)[0]), None)
        if owner is None:
            raise ValueError(f'no CMAP block covers U+{c:04X}')
        _map_code(owner, c, n + k)
    offs, p = [], len(head)
    for _, b in blocks:
        struct.pack_into('<I', b, 4, len(b))
        offs.append(p)
        p += len(b)
    ptr = {id(b): o + 8 for (_, b), o in zip(blocks, offs)}
    struct.pack_into('<III', finf, 0x10, ptr[id(cglp)], ptr[id(cwdh)], ptr[id(chain[0])])
    for a, b in zip(chain, chain[1:] + [None]):
        struct.pack_into('<I', a, 0x10, ptr[id(b)] if b is not None else 0)
    hdr = bytearray(head)
    struct.pack_into('<I', hdr, 8, p)
    return bytes(hdr) + b''.join(b for _, b in blocks)


def codes(x) -> set:
    """Every code any CMAP block of the font maps."""
    out = set()
    p, = struct.unpack_from('<I', x, 0x10 + 0x18)
    while p:
        b = p - 8
        first, last, typ = struct.unpack_from('<HHH', x, b + 8)
        d = b + 0x14
        if typ == 0:
            out.update(range(first, last + 1))
        elif typ == 1:
            out.update(c for c in range(first, last + 1)
                       if struct.unpack_from('<H', x, d + 2 * (c - first))[0] != 0xFFFF)
        else:
            out.update(struct.unpack_from('<H', x, d + 2 + 4 * k)[0]
                       for k in range(struct.unpack_from('<H', x, d)[0]))
        p, = struct.unpack_from('<I', x, b + 0x10)
    return out
