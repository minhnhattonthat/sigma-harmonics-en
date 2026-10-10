"""Relabel full-screen tile graphics (RGCN tiles N, RLCN palette N+1, RCSN screen N+2) in English.

The game is held sideways: the player sees the raw screen rotated 90 deg counter-clockwise, so recipes use
player-view coordinates (192x256). Steps: render the screen, rotate to player view, wipe boxes (each row filled
with its most common dark colour, which keeps vertical gradients), draw labels with texedit.label, rotate back,
then requantise only the changed pixels to each cell's own palette and write them into its tile.
Recipes live in font/screens.json:
  {"00063": {"wipe": [[x0, y0, x1, y1], ...], "text": [{"text": "...", "box": [x0, y0, x1, y1], "size": 20,
             "font": "DejaVuSerif.ttf", "fill": [255, 255, 255], "outline": null}, ...]}}

python -X utf8 tools/scredit.py preview ID OUT.png   # apply the recipe, save the player view (2x)
python -X utf8 tools/scredit.py show ID OUT.png      # original, player view (2x)
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402
import texedit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / 'font' / 'screens.json'


def recipes():
    return json.loads(RECIPES.read_text(encoding='utf-8')) if RECIPES.exists() else {}


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
    """New RGCN bytes with `new_raw` (raw-orientation RGB image) written into the tiles."""
    tiles, bpp, _, _, off = gfx.ncgr(g)
    pal = gfx.nclr(p)
    sw, sh, ents = gfx.nscr(s)
    old = gfx.render(tiles, pal, bpp, screen=(sw, sh, ents))
    po, pn = old.load(), new_raw.load()
    tiles = [list(t) for t in tiles]
    owner = {}
    for k, e in enumerate(ents):
        t, hf, vf, pi = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
        base, n = (pi * 16, 16) if bpp == 4 else (0, len(pal))
        cand = range(1, n)  # index 0 is transparent
        cx, cy = (k % sw) * 8, (k // sw) * 8
        changed = False
        for y in range(8):
            for x in range(8):
                c = pn[cx + x, cy + y]
                if c == po[cx + x, cy + y]:
                    continue
                changed = True
                i = min(cand, key=lambda j: sum((a - b) ** 2 for a, b in zip(c, pal[(base + j) % len(pal)])))
                tiles[t][(7 - y if vf else y) * 8 + (7 - x if hf else x)] = i
        if changed:
            owner[t] = k
    for t, k in owner.items():  # an edited tile must not be drawn by any other cell
        assert sum(1 for e in ents if e & 0x3FF == t) == 1, f'tile {t} (cell {k}) is reused elsewhere: needs re-tiling'
    out = bytearray(g)
    step = 8 * bpp
    for t, px in enumerate(tiles):
        b = bytes(px) if bpp == 8 else bytes(px[i] | px[i + 1] << 4 for i in range(0, 64, 2))
        out[off + t * step:off + (t + 1) * step] = b
    return bytes(out)


def apply(g, p, s, recipe):
    """(edited player-view image, new RGCN bytes)."""
    im = edit(player_view(g, p, s), recipe)
    return im, encode(g, p, s, im.rotate(-90, expand=True))


if __name__ == '__main__':
    import text
    cmd, nid, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    _, c = text.load_rom()
    byid = {f['id']: f for f in c.files}
    g, p, s = (c.get(byid[nid + k]) for k in range(3))
    if cmd == 'show':
        im = player_view(g, p, s)
    else:
        _, new = apply(g, p, s, recipes()[f'{nid:05d}'])
        im = player_view(new, p, s)  # re-render from the written tiles: shows what the game will draw
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(out)
