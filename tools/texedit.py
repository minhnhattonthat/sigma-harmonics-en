"""Relabel the game's UI textures (title buttons, menus) in English.

Each button is a connected opaque region. Its face (inside a border) is wiped by copying, row by row, a clean
column from the button's left edge across the face, then the English label is drawn centred with a dark outline
and quantised back to the texture's own palette. Recipes live in font/textures.json:
  {"08376": {"0": "Save", "2": "Load", ...}, ...}   keys = component index printed by `list`.
Optional per-component list form: ["Label", size_px] or {"text":..., "size":..., "box":[x0,y0,x1,y1]} for a
manual box (for text that is not a separate button, e.g. a label strip on a background).

python -X utf8 tools/texedit.py list ID            # components with their boxes, and a numbered preview
python -X utf8 tools/texedit.py preview ID OUT.png  # apply the recipe, save an enlarged preview
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import tex  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / 'font' / 'textures.json'
FONT = ROOT / 'font' / 'DejaVuSans-Bold.ttf'
BORDER = 3


def components(im, min_area=60):
    """Bounding boxes of 4-connected opaque regions, sorted top-left first."""
    w, h = im.size
    a = im.getchannel('A').load()
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(h):
        for x in range(w):
            if a[x, y] < 128 or seen[y][x]:
                continue
            stack, x0, y0, x1, y1, n = [(x, y)], x, y, x, y, 0
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                n += 1
                x0, y0, x1, y1 = min(x0, cx), min(y0, cy), max(x1, cx), max(y1, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and a[nx, ny] >= 128:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if n >= min_area:
                boxes.append((x0, y0, x1 + 1, y1 + 1))
    return sorted(boxes, key=lambda b: (b[1] // 8, b[0]))


def wipe(im, box, border=BORDER, mode='column'):
    """Erase the face of `box`: copy the clean column just inside the left border across each row, or
    (mode='row') fill each row with its most common colour, for faces whose text touches the left edge."""
    x0, y0, x1, y1 = box
    px = im.load()
    cx = x0 + border + 2
    for y in range(y0 + border, y1 - border):
        if mode == 'row':
            row = [px[x, y] for x in range(x0 + border, x1 - border)]
            dark = [p for p in row if p[3] >= 128 and sum(p[:3]) < 300] or row  # text is the bright part
            c = max(set(dark), key=dark.count)
            xs = range(x0 + border, x1 - border)
        else:
            c = px[cx, y]
            xs = range(cx, x1 - border - 2)
        for x in xs:
            px[x, y] = c


def label(im, box, text, size=None, align='center', border=BORDER, fill=(255, 255, 255), outline=(16, 16, 32), font=FONT):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0 - 2 * border - (4 if border else 0), y1 - y0 - 2 * border
    size = size or max(7, min(14, bh - 4))
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    while True:  # shrink until it fits the face ('\n' gives two lines)
        f = ImageFont.truetype(str(font), size)
        l, t, r, b = d.multiline_textbbox((0, 0), text, font=f, spacing=0, align='center')
        if (r - l <= bw and b - t <= bh) or size <= 7:
            break
        size -= 1
    tx = (x0 + 1 - l) if align == 'left' else x0 + (x1 - x0 - (r - l)) // 2 - l
    ty = y0 + (y1 - y0 - (b - t)) // 2 - t
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)) if outline else ():
        d.multiline_text((tx + dx, ty + dy), text, font=f, fill=tuple(outline) + (255,), spacing=0, align='center')
    d.multiline_text((tx, ty), text, font=f, fill=tuple(fill) + (255,), spacing=0, align='center')
    im.alpha_composite(layer)


def apply(tid, recipe, b=None):
    """(edited RGBA image, new texture bytes); b = original texture bytes (default: work/cpk dump)."""
    b = b if b is not None else (ROOT / 'work' / 'cpk' / tid).read_bytes()
    im = tex.image(b)
    comps = components(im)
    for key, spec in recipe.items():
        if key.startswith('_'):
            continue
        if isinstance(spec, str):
            spec = {'text': spec}
        elif isinstance(spec, list):
            spec = {'text': spec[0], 'size': spec[1]}
        box = tuple(spec['box']) if 'box' in spec else comps[int(key)]
        if spec.get('clear'):  # text drawn straight on a transparent area: erase to transparent
            im.paste((0, 0, 0, 0), box)
        elif spec.get('wipe', True):
            wipe(im, box, spec.get('border', BORDER), spec.get('wipe_mode', 'column'))
        if spec['text']:
            label(im, box, spec['text'], spec.get('size'), spec.get('align', 'center'), 0 if spec.get('clear') else spec.get('border', BORDER),
                  spec.get('fill', (255, 255, 255)), spec.get('outline', (16, 16, 32)), ROOT / 'font' / spec.get('font', FONT.name))
    return im, tex.encode(im, b)


def recipes():
    return json.loads(RECIPES.read_text(encoding='utf-8')) if RECIPES.exists() else {}


def preview(im, out, comps=None):
    bg = Image.new('RGBA', im.size, (0, 90, 0, 255))
    bg.alpha_composite(im)
    if comps:
        d = ImageDraw.Draw(bg)
        for k, (x0, y0, x1, y1) in enumerate(comps):
            d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 0, 255, 255))
            d.text((x0 + 1, y0), str(k), fill=(255, 255, 0, 255))
    bb = im.getbbox()
    bg.crop(bb).resize(((bb[2] - bb[0]) * 3, (bb[3] - bb[1]) * 3), Image.NEAREST).save(out)


if __name__ == '__main__':
    cmd, tid = sys.argv[1], sys.argv[2]
    if cmd == 'list':
        im = tex.image((ROOT / 'work' / 'cpk' / tid).read_bytes())
        comps = components(im)
        for k, c in enumerate(comps):
            print(k, c)
        preview(im, str(ROOT / 'work' / 'qa' / f'comp_{tid}.png'), comps)
    elif cmd == 'preview':
        im, _ = apply(tid, recipes()[tid])
        preview(im, sys.argv[3])
