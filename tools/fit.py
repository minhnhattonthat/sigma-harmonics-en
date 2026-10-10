"""Measure and wrap English for the game's boxes.

Dialogue (string tables driven by a Sigma script) is drawn with font 04387: auto-wrapped here to
DLG_LINES lines of DLG_PX pixels. UI tables use their own small font (px9 Latin): the English must fit
the Japanese line count and pixel budget (JP chars x cell width).
python -X utf8 tools/fit.py "Some English text" [--ui]   # dry run: prints the wrapped lines and widths
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import latin  # noqa: E402

DLG_PX = 180        # usable line width of the dialogue box (measured: interior ~186 px)
DLG_LINES = 3
GAP = 1             # the renderer adds 1 px after every glyph
CODE = re.compile(r'\$c\d\d')
NL = '\\n'          # line break as stored: a literal backslash + n


@lru_cache(None)
def _dlg_adv():
    out = {}
    for ch in latin.ASCII:
        _, adv = latin.raster_ttf(ch, latin.DLG_TTF, latin.DLG_PX, 16, 16, 13, 3)
        out[ch] = adv + GAP
    return out


@lru_cache(None)
def _ui_adv():
    g = latin.px9()
    return {ch: len(rows[0]) + 1 + GAP for ch, rows in g.items()}


def width(s, ui=False):
    adv = _ui_adv() if ui else _dlg_adv()
    return sum(adv.get(ch, 99) for ch in CODE.sub('', s))


def wrap(s, limit=DLG_PX, ui=False):
    """Greedy wrap on spaces, keeping explicit breaks. Returns the list of lines."""
    lines = []
    for para in s.split(NL):
        cur = ''
        for word in para.split(' '):
            trial = word if not cur else cur + ' ' + word
            if cur and width(trial, ui) > limit:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def balanced(s, limit=DLG_PX, ui=False):
    """Wrap into the fewest lines, then even out line lengths (no one-word widows)."""
    lines = wrap(s, limit, ui)
    if NL in s or len(lines) < 2:
        return lines
    n = len(lines)
    lo, hi = max(width(w, ui) for w in s.split(' ')), limit
    while lo < hi:  # smallest limit that still gives n lines
        mid = (lo + hi) // 2
        if len(wrap(s, mid, ui)) <= n:
            hi = mid
        else:
            lo = mid + 1
    return wrap(s, lo, ui)


def fit_dialogue(s):
    """English as stored for a dialogue line: wrapped with literal \\n. Errors -> ValueError."""
    lines = balanced(s)
    bad = [ln for ln in lines if width(ln) > DLG_PX]
    if bad:
        raise ValueError(f'word wider than the box: {bad[0]!r}')
    if len(lines) > DLG_LINES:
        raise ValueError(f'{len(lines)} lines (max {DLG_LINES})')
    return NL.join(lines)


if __name__ == '__main__':
    ui = '--ui' in sys.argv
    txt = [a for a in sys.argv[1:] if a != '--ui'][0]
    for ln in (wrap(txt, 999, True) if ui else balanced(txt)):
        print(f'{width(ln, ui):4d}px  {ln}')
