"""Relabel full-screen tile graphics (RGCN tiles N, RLCN palette N+1, RCSN screen N+2) in English.

The game is held sideways: the player sees the raw screen rotated 90 deg counter-clockwise, so recipes use
player-view coordinates (192x256). Steps: render the screen, rotate to player view, wipe boxes (each row filled
with its most common dark colour, which keeps vertical gradients), draw labels with texedit.label, rotate back,
then requantise only the changed pixels to each cell's own palette and write them into its tile.
4bpp screens: each 8x8 cell can only show the 16 colours of its own palette, so draw text in a colour the
original text used (check with `preview`: a wrong colour shows up as a shifted hue).
Recipes live in font/screens*.json (merged; an id may appear in only one file):
  {"00063": {"wipe": [[x0, y0, x1, y1], ...], "text": [{"text": "...", "box": [x0, y0, x1, y1], "size": 20,
             "font": "DejaVuSerif.ttf", "fill": [255, 255, 255], "outline": null}, ...]}}

python -X utf8 tools/scredit.py preview ID OUT.png   # apply the recipe, save the player view (2x)
python -X utf8 tools/scredit.py show ID OUT.png      # original, player view (2x)
"""
import collections
import json
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402
import texedit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def recipes():
    """All recipes from font/screens*.json (one file per group of screens)."""
    out = {}
    for p in sorted(ROOT.glob('font/screens*.json')):
        new = json.loads(p.read_text(encoding='utf-8'))
        assert not set(new) & set(out), f'{p.name}: ids defined twice: {sorted(set(new) & set(out))}'
        out.update(new)
    return out


def player_view(g, p, s):
    tiles, bpp, _, _, _ = gfx.ncgr(g)
    return gfx.render(tiles, gfx.nclr(p), bpp, screen=gfx.nscr(s)).rotate(90, expand=True)


def edit(im, recipe):
    im = im.convert('RGBA')
    for box in recipe.get('wipe', []):
        texedit.wipe(im, tuple(box), border=0, mode='row')
    for spec in recipe.get('text', []):
        texedit.label(im, tuple(spec['box']), spec['text'], spec.get('size'), spec.get('align', 'center'), 0,
                      spec.get('fill', (255, 255, 255)), spec.get('outline'), ROOT / 'font' / spec.get('font', 'DejaVuSerif.ttf'))
    return im.convert('RGB')


def encode(g, p, s, new_raw):
    """(new RGCN, new RCSN) drawing `new_raw` (raw-orientation RGB image). A changed cell edits its tile in place
    when no other cell uses it, else is pointed at an identical or appended tile (screens often share a blank tile)."""
    tiles, bpp, _, _, off = gfx.ncgr(g)
    pal = gfx.nclr(p)
    sw, sh, ents = gfx.nscr(s)
    old = gfx.render(tiles, pal, bpp, screen=(sw, sh, ents))
    po, pn = old.load(), new_raw.load()
    n_old = len(tiles)
    tiles = [list(t) for t in tiles]
    ents = list(ents)
    uses = collections.Counter(e & 0x3FF for e in ents)
    index = {tuple(t): i for i, t in reversed(list(enumerate(tiles)))}
    for k, e in enumerate(ents):
        t, hf, vf, pi = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
        base, n = (pi * 16, 16) if bpp == 4 else (0, len(pal))
        cand = range(1, n)  # index 0 is transparent
        cx, cy = (k % sw) * 8, (k // sw) * 8
        src = lambda y, x: (7 - y if vf else y) * 8 + (7 - x if hf else x)  # noqa: E731
        block = [tiles[t][src(y, x)] for y in range(8) for x in range(8)]  # screen orientation
        changed = False
        for y in range(8):
            for x in range(8):
                c = pn[cx + x, cy + y]
                if c != po[cx + x, cy + y]:
                    changed = True
                    block[y * 8 + x] = min(cand, key=lambda j: sum((a - b) ** 2 for a, b in zip(c, pal[(base + j) % len(pal)])))
        if not changed:
            continue
        if uses[t] == 1:  # only this cell draws the tile: edit it in place, keeping its flips
            for y in range(8):
                for x in range(8):
                    tiles[t][src(y, x)] = block[y * 8 + x]
            continue
        uses[t] -= 1  # shared tile: point this cell at an identical tile or a new one
        nt = index.get(tuple(block))
        if nt is None:
            nt = len(tiles)
            tiles.append(block)
            index[tuple(block)] = nt
        uses[nt] += 1
        ents[k] = nt | pi << 12
    i, _ = gfx.block(g, b'RAHC')
    h = struct.unpack_from('<H', g, i + 8)[0] or 1
    while len(tiles) % h:  # keep the height field, pad to whole columns
        tiles.append([0] * 64)
    w = len(tiles) // h
    limit = min(1024, max(n_old, sw * sh))  # never more tiles than the screen has cells
    assert len(tiles) <= limit, f'{len(tiles)} tiles > {limit}'
    data = b''.join(bytes(px) if bpp == 8 else bytes(px[i] | px[i + 1] << 4 for i in range(0, 64, 2)) for px in tiles)
    size = struct.unpack_from('<I', g, i + 0x18)[0]
    out = bytearray(g[:off] + data + g[off + size:])
    if len(data) != size:
        grow = len(data) - size
        struct.pack_into('<I', out, 8, len(out))
        struct.pack_into('<I', out, i + 4, struct.unpack_from('<I', g, i + 4)[0] + grow)
        struct.pack_into('<HH', out, i + 8, h, w)
        struct.pack_into('<I', out, i + 0x18, len(data))
        j = out.find(b'SOPC', i)
        if j >= 0:
            struct.pack_into('<HH', out, j + 0xC, w, h)
    j, _ = gfx.block(s, b'NRCS')
    new_s = bytearray(s)
    struct.pack_into(f'<{len(ents)}H', new_s, j + 0x14, *ents)
    return bytes(out), bytes(new_s)


def apply(g, p, s, recipe):
    """(edited player-view image, new RGCN bytes, new RCSN bytes)."""
    im = edit(player_view(g, p, s), recipe)
    return (im, *encode(g, p, s, im.rotate(-90, expand=True)))


if __name__ == '__main__':
    import text
    cmd, nid, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    _, c = text.load_rom()
    byid = {f['id']: f for f in c.files}
    g, p, s = (c.get(byid[nid + k]) for k in range(3))
    if cmd == 'show':
        im = player_view(g, p, s)
    else:
        _, ng, ns = apply(g, p, s, recipes()[f'{nid:05d}'])
        im = player_view(ng, p, ns)  # re-render from the written data: shows what the game will draw
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(out)
