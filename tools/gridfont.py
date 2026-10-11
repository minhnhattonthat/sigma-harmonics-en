"""Descent skill grid (table 05609 rows FIRST..LAST, font 05611): three category columns of 62 px cells.

The grid draws each name as one line of the 9 px font 05611 into a 2-tile canvas, so a long name cannot wrap. Instead
the font's cell is made 16 rows tall (nftr recell: every glyph shifted 7 columns, since flags 2 stores the vertical
axis as columns) and each grid name becomes a run of 9-column chunk glyphs holding one or two lines of the game's 9 px
pixel Latin (latin.px9). PATCH moves the 21 grid rects to tile-aligned y and a 16 px height so the canvas holds it.
Only the grid draws with 05611 (the header uses 04725), so nothing else changes.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402

TABLE, FONT = '05609', 5611
FIRST, LAST = 152, 223        # string indices the grid reads (docs/re/verify.md)
CELL = 58                     # px a one-line name may use; wider ones go on two lines
MAXLINE = 62                  # px of a two-line half: the cell pitch
ROWS, SLICE, OLDW, SIZE = 16, 9, 9, 18   # glyph rows (upright height), columns per chunk, old cell width, bytes/glyph
LINE_Y = {1: (4,), 2: (0, 8)}  # top row of each line: px9 caps are rows 0-6, descenders 7-8
CODE0, CODE1 = 0xF900, 0xFE00  # chunk codes: CJK compatibility range, free in the font (catch-all CMAP block)

# the 21 grid rects: descriptor table 0x20c3b58 (28 bytes each, entries 5-25: x, y, w, h, ...), 7 rows x 3 columns
DESC = 0x20C3B58


def _rect_patch():
    out = []
    for i in range(5, 26):
        y = 134 + 16 * ((i - 5) % 7)
        out += [(DESC + i * 0x1C + 4, y, y - 6),    # y: start on a tile row so a 16 px canvas takes 2 tiles
                (DESC + i * 0x1C + 12, 10, ROWS)]   # h: 10 -> 16
    return out


PATCH = _rect_patch()


def is_grid(row_id):
    t, i = row_id.split(':')
    return t == TABLE and FIRST <= int(i) <= LAST


def _adv(ch):
    """px9 advance with 1 blank column between glyphs; a word space is 2 px (the strip is composed pixel-exact)."""
    return 2 if ch == ' ' else len(latin.px9()[ch][0]) + 1


def px(s):
    return sum(_adv(ch) for ch in s) - 1 if s else 0


def lines(name):
    """[line]: one line if it fits a cell, else the most even two-line split at a space or hyphen."""
    if px(name) <= CELL:
        return [name]
    cuts = [m.end() for m in re.finditer(r'[ -]', name)]
    best = min(((max(px(name[:k].rstrip()), px(name[k:])), k) for k in cuts), default=None)
    if best is None:
        raise ValueError(f'{name!r}: no break point')
    return [name[:best[1]].rstrip(), name[best[1]:]]


def strip(ls):
    """Rows (16 x W) of 0/1: each line centred under the other."""
    g = latin.px9()
    w = max(px(s) for s in ls)
    rows = [[0] * w for _ in range(ROWS)]
    for s, y0 in zip(ls, LINE_Y[len(ls)]):
        x = (w - px(s)) // 2
        for ch in s:
            for y, r in enumerate(g[ch]):
                for dx, c in enumerate(r):
                    if c == '#' and y0 + y < ROWS:
                        rows[y0 + y][x + dx] = 1
            x += _adv(ch)
    return rows


def slices(name):
    """[(bytes of 16 x 9 bits, columns used)] 9-column slices of a name's strip."""
    rows = strip(lines(name))
    w = len(rows[0])
    return [(bytes(v for r in rows for v in (r[x:x + SLICE] + [0] * SLICE)[:SLICE]), min(SLICE, w - x))
            for x in range(0, w, SLICE)]


def _recell(g):
    """Old 9x9 flags-2 glyph (81 bits, row = advance axis) -> 16-column cell: columns shift right by 7."""
    bits = ''.join(f'{b:08b}' for b in g)[:OLDW * OLDW]
    rows = [bits[r * OLDW:(r + 1) * OLDW] for r in range(OLDW)]
    out = ''.join('0' * (16 - OLDW) + r for r in rows)
    out += '0' * (-len(out) % 8)
    return int(out, 2).to_bytes(len(out) // 8, 'big').ljust(SIZE, b'\0')


class Plan:
    """Unique slices of every grid name and the codes they are drawn into."""

    def __init__(self, names, taken=()):
        self.names = sorted(set(names))
        free = (c for c in range(CODE0, CODE1) if c not in taken)
        self.code = {s: next(free) for s in sorted({s for n in self.names for s in slices(n)})}

    def encode(self, name):
        return ''.join(chr(self.code[s]) for s in slices(name))

    def font(self, x):
        """Font bytes: cell 16 rows tall, every chunk added. Glyph width = the full 16 columns the blitter copies;
        advance = columns - 1 (the UI renderer adds 1 px after a glyph)."""
        p = latin.params(x)
        assert (p['w'], p['h'], p['bpp'], p['flags']) == (OLDW, 9, 1, 2), p
        assert not set(self.code.values()) & nftr.codes(x), 'chunk codes overlap the font'
        new = {}
        for (bits, n), cp in self.code.items():
            rows = [list(bits[y * SLICE:(y + 1) * SLICE]) for y in range(ROWS)]
            new[cp] = (latin.pack(latin.orient(rows, 2, 16, 9), 1, SIZE), 0, 16, n - 1)
        return nftr.add_glyphs(x, new, recell=(16, SIZE, _recell, 16 - OLDW))


def errors(name):
    """Problems drawing `name` in a grid cell (empty list = fine)."""
    try:
        ls = lines(name)
    except ValueError as e:
        return [str(e)]
    if len(ls) == 2 and max(px(s) for s in ls) > MAXLINE:
        return [f'two-line width {[px(s) for s in ls]} > {MAXLINE}px']
    return []
