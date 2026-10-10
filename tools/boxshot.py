"""Crop the dialogue box from emulator frames, upright and enlarged.

python -X utf8 tools/boxshot.py QA_DIR OUT.png [frame ...]   # default: every f*.png that shows a box
The dialogue box sits on the bottom screen, drawn upside down (the DS is held sideways).
"""
import sys
from pathlib import Path

from PIL import Image

BOX = (60, 280, 256, 384)


def has_box(im):
    g = im.convert('L')
    return sum(1 for x in range(140, 250, 4) for y in range(300, 380, 4) if g.getpixel((x, y)) > 230) > 300


def main(argv):
    d, out = Path(argv[0]), argv[1]
    frames = [d / f'{f}.png' for f in argv[2:]] or sorted(d.glob('f*.png'))
    crops = [Image.open(p).crop(BOX).rotate(180) for p in frames if has_box(Image.open(p))]
    if not crops:
        sys.exit('no frame shows a dialogue box')
    w, h = crops[0].size
    sheet = Image.new('RGB', (w, h * len(crops)))
    for k, c in enumerate(crops):
        sheet.paste(c, (0, k * h))
    sheet.resize((w * 3, h * 3 * len(crops)), Image.NEAREST).save(out)
    print(f'{len(crops)} boxes -> {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
