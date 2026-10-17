"""Two-line skill names. Font 05611 (9x9 1bpp) draws them: the engine puts one line in a canvas, so a long name
becomes a run of 9-column chunk glyphs holding two lines of pixel Latin, and the font's cell is made 16 rows tall
(nftr recell: every glyph shifted 7 columns, since flags 2 stores the vertical axis as columns).

Table 05609 rows 152-223 are the skill names of BOTH the Descent grid (3 columns x 7 rows of 62 px cells; PATCH moves
the 21 rects to tile-aligned y and a 16 px height so the canvas holds a taller glyph) and the battle cards (62 px
wide, only ~11 rows from y=245 to the screen edge). So a name that fits one line of plain text stays plain, and a
longer one is two lines of a 3x5 uppercase font in rows 0-4 and 6-10, which fits both. ('px9' style, two lines of
the 9 px font, needs 16 rows: fine for Descent, cut off in battle.) 04985/06365 hold the same names, drawn plain.
Only these screens draw with 05611 (headers use 04725), so nothing else changes.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402

FONT = 5611
STYLES = {'05609': 'tiny'}    # the Descent grid and the battle cards read the SAME table, so one style serves both
FIRST, LAST = 152, 223        # string indices both screens read (docs/re/verify.md)
CELL = 58                     # px a one-line (px9) name may use; wider ones go on two lines
MAXLINE = 62                  # px of a two-line half: the cell pitch
ROWS, SLICE, OLDW, SIZE = 16, 9, 9, 18   # glyph rows (upright height), columns per chunk, old cell width, bytes/glyph
# top row of each line (px9 caps rows 0-6, desc 7-8); one line ends at row 10, the last the battle screen shows
LINE_Y = {'px9': {1: (2,), 2: (0, 8)}, 'tiny': {2: (0, 6)}}
CODE0, CODE1 = 0xF900, 0xFE00  # chunk codes: CJK compatibility range, free in the font (catch-all CMAP block)

# 3x5 uppercase pixel font (M, N, W wider); '#' ink
TINY = {}
for _ch, _rows in {
    'A': '.#. #.# ### #.# #.#', 'B': '##. #.# ##. #.# ##.', 'C': '.## #.. #.. #.. .##', 'D': '##. #.# #.# #.# ##.',
    'E': '### #.. ##. #.. ###', 'F': '### #.. ##. #.. #..', 'G': '.## #.. #.# #.# .##', 'H': '#.# #.# ### #.# #.#',
    'I': '### .#. .#. .#. ###', 'J': '..# ..# ..# #.# .#.', 'K': '#.# #.# ##. #.# #.#', 'L': '#.. #.. #.. #.. ###',
    'M': '#...# ##.## #.#.# #...# #...#', 'N': '#..# ##.# #.## #..# #..#', 'O': '.#. #.# #.# #.# .#.',
    'P': '##. #.# ##. #.. #..', 'Q': '.#. #.# #.# ##. .##', 'R': '##. #.# ##. #.# #.#', 'S': '.## #.. .#. ..# ##.',
    'T': '### .#. .#. .#. .#.', 'U': '#.# #.# #.# #.# ###', 'V': '#.# #.# #.# #.# .#.',
    'W': '#...# #...# #.#.# ##.## #...#', 'X': '#.# #.# .#. #.# #.#', 'Y': '#.# #.# .#. .#. .#.',
    'Z': '### ..# .#. #.. ###', '-': '... ... ### ... ...', '!': '# # # . #', "'": '# # . . .', '.': '. . . . #',
    '0': '.#. #.# #.# #.# .#.', '1': '.#. ##. .#. .#. ###', '2': '##. ..# .#. #.. ###', '3': '##. ..# .#. ..# ##.',
    '4': '#.# #.# ### ..# ..#', '5': '### #.. ##. ..# ##.', '6': '.## #.. ##. #.# .#.', '7': '### ..# .#. .#. .#.',
    '8': '.#. #.# .#. #.# .#.', '9': '.#. #.# .## ..# ##.',
}.items():
    TINY[_ch] = _rows.split()
TINY[' '] = ['.'] * 5

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

# The battle action banner (0x202b060 -> 0x205cfac) draws the same rows with font 05610, which has no chunk glyphs,
# so player skills came out blank. Rows 224-295 are plain copies of 152-223 and the banner reads row + 72 for rows
# >= 152 (enemy skills are rows 0-151). Room: 0x205d234 returns the object in r0, and strd zeroes the 4 stack args.
BANNER = LAST + 1             # first plain copy; 05609 has exactly 224 rows
BANNER_FONT = 5610            # gets the condensed Latin (font/px9c.txt): the banner shows only ~88 px of a name
assert (FIRST, LAST - FIRST + 1) == (152, 72)  # the cmp / add immediates below
PATCH += [
    (0x202b088, 0xe58d2000, 0xe3a03000),  # mov r3, #0
    (0x202b08c, 0xe58d2004, 0xe1cd20f0),  # strd r2, r3, [sp]
    (0x202b090, 0xe58d2008, 0xe1cd20f8),  # strd r2, r3, [sp, #8]
    (0x202b098, 0xe1a00005, 0xe3540098),  # cmp r4, #152         (was mov r0, r5: r0 is already r5)
    (0x202b0a0, 0xe58d200c, 0xa2833048),  # addge r3, r3, #72    row of the plain copy
]


def style_of(row_id):
    """'px9' / 'tiny' for a row drawn through this module, else None."""
    t, i = row_id.split(':')
    return STYLES.get(t) if FIRST <= int(i) <= LAST else None


def is_grid(row_id):
    return style_of(row_id) is not None


def _glyph(style, ch):
    return TINY[ch.upper()] if style == 'tiny' else latin.px9()[ch]


def _adv(style, ch):
    """Advance with 1 blank column between glyphs; a word space is 2 px (the strip is composed pixel-exact)."""
    return 2 if ch == ' ' else len(_glyph(style, ch)[0]) + 1


def px(s, style='px9'):
    return sum(_adv(style, ch) for ch in s) - 1 if s else 0


def lines(name, style='px9'):
    """[line]: one px9 line if it fits a cell, else the most even two-line split at a space or hyphen."""
    plain = fit.width(name, ui=True)  # ordinary text spaces every glyph by advance + 1 (wider than the strip)
    if (px(name) if style == 'px9' else plain) <= CELL:
        return [name]
    cuts = [m.end() for m in re.finditer(r'[ -]', name)]
    best = min(((max(px(name[:k].rstrip(), style), px(name[k:], style)), k) for k in cuts), default=None)
    if best is None:
        raise ValueError(f'{name!r}: no break point')
    return [name[:best[1]].rstrip(), name[best[1]:]]


def strip(ls, style='px9'):
    """Rows (16 x W) of 0/1: each line centred under the other."""
    w = max(px(s, style) for s in ls)
    rows = [[0] * w for _ in range(ROWS)]
    for s, y0 in zip(ls, LINE_Y[style][len(ls)]):
        x = (w - px(s, style)) // 2
        for ch in s:
            for y, r in enumerate(_glyph(style, ch)):
                for dx, c in enumerate(r):
                    if c == '#' and y0 + y < ROWS:
                        rows[y0 + y][x + dx] = 1
            x += _adv(style, ch)
    return rows


def slices(name, style='px9'):
    """[(bytes of 16 x 9 bits, columns used)] 9-column slices of a name's strip; a one-line name is a px9 line."""
    ls = lines(name, style)
    rows = strip(ls, 'px9' if len(ls) == 1 else style)
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
    """Chunk glyphs of every name of one style and the codes they are drawn into."""

    def __init__(self, names, taken=(), style='px9'):
        self.style = style
        self.names = sorted({n for n in names if self.chunked(n)})
        free = (c for c in range(CODE0, CODE1) if c not in taken)
        self.code = {s: next(free) for s in sorted({s for n in self.names for s in slices(n, style)})}

    def chunked(self, name):
        """Every name is drawn as chunks: the battle cards centre plain text from the re-celled glyphs' widths, which
        put "Big Stop" ~20 px left of its card (off screen under the first card)."""
        return True

    def encode(self, name):
        if not self.chunked(name):
            return name
        return ''.join(chr(self.code[s]) for s in slices(name, self.style))

    def font(self, x, recell=True):
        """Font bytes with every chunk added; recell=True first makes the cell 16 rows tall (once per font). Glyph
        width = the full 16 columns the blitter copies; advance = columns - 1 (the UI renderer adds 1 px)."""
        p = latin.params(x)
        assert (p['w'], p['h'], p['bpp'], p['flags']) == (OLDW if recell else 16, 9, 1, 2), p
        assert not set(self.code.values()) & nftr.codes(x), 'chunk codes overlap the font'
        new = {}
        for (bits, n), cp in self.code.items():
            rows = [list(bits[y * SLICE:(y + 1) * SLICE]) for y in range(ROWS)]
            new[cp] = (latin.pack(latin.orient(rows, 2, 16, 9), 1, SIZE), 0, 16, n - 1)
        return nftr.add_glyphs(x, new, recell=(16, SIZE, _recell, 16 - OLDW) if recell else None)


def errors(name, style='px9'):
    """Problems drawing `name` (empty list = fine)."""
    try:
        ls = lines(name, style)
    except ValueError as e:
        return [str(e)]
    out = []
    if len(ls) == 1 and px(name) > CELL:  # one line is always drawn as a px9 strip (slices)
        out.append(f'one-line px9 width {px(name)} > {CELL}px')
    if len(ls) == 2 and max(px(s, style) for s in ls) > MAXLINE:
        out.append(f'two-line width {[px(s, style) for s in ls]} > {MAXLINE}px')
    if style == 'tiny' and len(ls) == 2:
        bad = sorted({ch for ch in name if ch != ' ' and ch.upper() not in TINY})
        if bad:
            out.append(f'no 3x5 glyph for {bad}')
    return out
