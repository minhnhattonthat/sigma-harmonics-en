"""Relabel sprite graphics (RNAN N, RECN cells N+1, RGCN tiles N+2, RLCN palette N+3) in English.

Each cell is a group of OAM pieces drawing 8x8 tiles from the RGCN (1D mapping). Recipes use player-view
coordinates of the cell (the raw cell image rotated 90 deg counter-clockwise, origin at its top-left, 1x), like
scredit. Changed pixels go back into the tiles the pieces use, requantised to each piece's palette; tiles are
edited in place, so a tile shared by several cells (e.g. a "の刻" piece next to every hour) changes in all of them.
Sets whose palette lives elsewhere (battle) use a grey ramp: colour i*17 stands for palette index i.
Recipes: font/sprites.json  {"06421": {"15": {"clear": [box], "wipe": [box], "text": [{...scredit text item...}]}}}
(box = [x0, y0, x1, y1]; `clear` makes pixels transparent, `fill` [x0, y0, x1, y1, r, g, b] paints a colour,
`wipe` copies the column at x0+2 across to x1-2.)

python -X utf8 tools/sprite.py show ID OUT.png [CELL...]     # cells in player view, numbered (ID = the RGCN id)
python -X utf8 tools/sprite.py preview ID OUT.png [CELL...]  # recipe applied, re-rendered from the written tiles
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402
import texedit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def recipes():
    return json.loads((ROOT / 'font' / 'sprites.json').read_text(encoding='utf-8'))


def ncer(b):
    """[[piece dict, ...] per cell], tile index shift. Piece: x, y, w, h, tile (32-byte units), pal, hf, vf, bpp8."""
    i, _ = gfx.block(b, b'KBEC')
    n, ext, off, mapping = struct.unpack_from('<HHII', b, i + 8)
    shift = mapping if mapping < 4 else 0
    base = i + 8 + off
    esz = 16 if ext == 1 else 8
    oams = base + n * esz
    cells = []
    for c in range(n):
        cnt, _, o = struct.unpack_from('<HHI', b, base + c * esz)
        pieces = []
        for k in range(cnt):
            a0, a1, a2 = struct.unpack_from('<HHH', b, oams + o + k * 6)
            y = a0 & 0xFF
            y = y - 256 if y >= 128 else y
            x = a1 & 0x1FF
            x = x - 512 if x >= 256 else x
            w, h = SIZES[(a0 >> 14, a1 >> 14)]
            affine = a0 >> 8 & 1
            pieces.append(dict(x=x, y=y, w=w, h=h, tile=(a2 & 0x3FF) << shift, pal=a2 >> 12, bpp8=a0 >> 13 & 1,
                               hf=0 if affine else a1 >> 12 & 1, vf=0 if affine else a1 >> 13 & 1))
        cells.append(pieces)
    return cells


def _tile_px(pc, tiles, tx, ty, units):
    """Tile list index for tile (tx, ty) inside a piece (1D mapping, 32-byte units)."""
    per_tile = 2 if pc['bpp8'] else 1
    return (pc['tile'] + (ty * (pc['w'] // 8) + tx) * per_tile) // units


def bounds(cell):
    if not cell:
        return 0, 0, 8, 8
    return (min(p['x'] for p in cell), min(p['y'] for p in cell),
            max(p['x'] + p['w'] for p in cell), max(p['y'] + p['h'] for p in cell))


def raw_cell(cell, tiles, pal, bpp):
    """RGBA raw-orientation image of one cell (index 0 transparent) and its origin (x0, y0)."""
    x0, y0, x1, y1 = bounds(cell)
    im = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
    units = 2 if bpp == 8 else 1
    for pc in reversed(cell):  # the first OAM is on top
        for py in range(pc['h']):
            for px in range(pc['w']):
                sx = pc['w'] - 1 - px if pc['hf'] else px
                sy = pc['h'] - 1 - py if pc['vf'] else py
                t = _tile_px(pc, tiles, sx // 8, sy // 8, units)
                if t >= len(tiles):
                    continue
                v = tiles[t][(sy % 8) * 8 + sx % 8]
                if v:
                    c = pal[(pc['pal'] * 16 + v) % len(pal)] if bpp == 4 else pal[v % len(pal)]
                    im.putpixel((pc['x'] - x0 + px, pc['y'] - y0 + py), (*c, 255))
    return im, (x0, y0)


def load(nid):
    import text
    _, c = text.load_rom()
    byid = {f['id']: f for f in c.files}
    return [c.get(byid[nid + k]) for k in (-1, 0, 1)]  # RECN, RGCN, RLCN


def sheet(cells, g, p, scale=2):
    tiles, bpp, _, _, _ = gfx.ncgr(g)
    pal = palette(p)
    ims = [raw_cell(c, tiles, pal, bpp)[0].rotate(90, expand=True) for c in cells]
    cw = max(im.width for im in ims) + 4
    chh = max(im.height for im in ims) + 14
    cols = max(1, min(len(ims), 1200 // (cw * scale)))
    out = Image.new('RGB', (cols * cw, ((len(ims) + cols - 1) // cols) * chh), (255, 0, 255))
    d = ImageDraw.Draw(out)
    for k, im in enumerate(ims):
        x, y = (k % cols) * cw, (k // cols) * chh
        d.text((x + 1, y), str(k), fill=(0, 0, 0))
        bg = Image.new('RGB', im.size, (96, 96, 96))
        bg.paste(im, (0, 0), im)
        out.paste(bg, (x, y + 12))
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def palette(p):
    """RLCN colours, or (sets whose palette is loaded elsewhere) a grey ramp: index i -> grey i*17."""
    return gfx.nclr(p) if p[:4] == b'RLCN' else [(i * 17,) * 3 for i in range(16)] * 16


def edit(view, rec):
    """Recipe on a player-view RGBA cell: `clear` boxes turn transparent, `wipe` boxes copy their clean left column
    across, then `text` items (scredit format). Pixels under 50% alpha end up transparent."""
    im = view.copy()
    px = im.load()
    for x0, y0, x1, y1, *rgb in rec.get('clear', []) + rec.get('fill', []):  # fill: [x0, y0, x1, y1, r, g, b]
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[x, y] = (*rgb, 255) if rgb else (0, 0, 0, 0)
    for box in rec.get('wipe', []):  # copies the clean column at x0+2 across: keeps vertical gradients
        texedit.wipe(im, tuple(box), border=0, mode='column')
    for spec in rec.get('text', []):
        texedit.label(im, tuple(spec['box']), spec['text'], spec.get('size'), spec.get('align', 'center'), 0,
                      spec.get('fill', (255, 255, 255)), spec.get('outline'),
                      ROOT / 'font' / spec.get('font', 'DejaVuSerif.ttf'))
    return im


def apply(e, g, p, recipe):
    """New RGCN bytes with each cell's recipe drawn into the tiles it uses."""
    tiles, bpp, _, _, off = gfx.ncgr(g)
    tiles = [list(t) for t in tiles]
    pal = palette(p)
    cells = ncer(e)
    units = 2 if bpp == 8 else 1
    for key, rec in recipe.items():
        cell = cells[int(key)]
        old, (x0, y0) = raw_cell(cell, tiles, pal, bpp)
        new = edit(old.rotate(90, expand=True), rec).rotate(-90, expand=True)
        po, pn = old.load(), new.load()
        for pc in cell:
            base = pc['pal'] * 16 if bpp == 4 else 0
            n = 16 if bpp == 4 else min(256, len(pal))
            for py in range(pc['h']):
                for px in range(pc['w']):
                    c = pn[pc['x'] - x0 + px, pc['y'] - y0 + py]
                    if c == po[pc['x'] - x0 + px, pc['y'] - y0 + py]:
                        continue
                    sx = pc['w'] - 1 - px if pc['hf'] else px
                    sy = pc['h'] - 1 - py if pc['vf'] else py
                    t = _tile_px(pc, tiles, sx // 8, sy // 8, units)
                    tiles[t][(sy % 8) * 8 + sx % 8] = 0 if c[3] < 128 else min(
                        range(1, n), key=lambda j: sum((a - b) ** 2 for a, b in zip(c[:3], pal[(base + j) % len(pal)])))
    i, _ = gfx.block(g, b'RAHC')
    size = struct.unpack_from('<I', g, i + 0x18)[0]
    data = b''.join(bytes(px) if bpp == 8 else bytes(px[k] | px[k + 1] << 4 for k in range(0, 64, 2)) for px in tiles)
    assert len(data) == size
    return g[:off] + data + g[off + size:]


if __name__ == '__main__':
    cmd, nid, out, only = sys.argv[1], int(sys.argv[2]), sys.argv[3], [int(v) for v in sys.argv[4:]]
    e, g, p = load(nid)
    if cmd == 'preview':
        g = apply(e, g, p, recipes()[f'{nid:05d}'])
    cells = ncer(e)
    sheet([cells[k] for k in only] if only else cells, g, p, 6 if only else 2).save(out)
