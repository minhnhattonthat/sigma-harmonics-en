"""Measure and wrap English for the game's boxes.

Dialogue (string tables driven by a Sigma script) is drawn with font 04387: reflowed here to
DLG_LINES lines of DLG_PX pixels, then packed into chunk glyphs by dlgfont.py. UI tables use their own small font (px9 Latin): the English must fit
the Japanese line count and pixel budget (JP chars x cell width).
python -X utf8 tools/fit.py "Some English text" [--ui]   # dry run: prints the wrapped lines and widths
"""
import math
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import latin  # noqa: E402

DLG_PX = 62         # line width in the bubble, text left-to-right for the player (interior 64 px; dlgfont.py)
DLG_LINES = 12      # bubble interior 184 px at a 14 px line step
GAP = 1             # UI renderers add 1 px after every glyph (dialogue glyphs carry their natural advance)
CODE = re.compile(r'\$c\d\d')
NL = '\\n'          # line break as stored: a literal backslash + n


@lru_cache(None)
def _ui_adv():
    g = latin.px9()
    return {ch: len(rows[0]) + 1 + GAP for ch, rows in g.items()}


def width(s, ui=False):
    s = CODE.sub('', s)
    if ui:
        return sum(_ui_adv().get(ch, 99) for ch in s)
    return math.ceil(latin.dlg_ttf().getlength(s))  # dialogue font: natural advance, as dlgfont draws it


def hyphenate(word, limit, ui=False):
    """A word wider than the line, split into pieces that fit, each but the last ending in '-'."""
    out = []
    while width(word, ui) > limit and len(word) > 1:
        piece = lambda k: word[:k] if word[k - 1] == '-' else word[:k] + '-'  # noqa: E731
        fits = [k for k in range(1, len(word)) if width(piece(k), ui) <= limit] or [1]
        k = max(fits, key=lambda k: (_break_score(word, k), k))
        out.append(piece(k))
        word = word[k:]
    return out + [word]


SUFFIXES = ('ing', 'ment', 'tion', 'sion', 'ness', 'able', 'ible', 'ful', 'less', 'ous', 'ive', 'est', 'ance',
            'ence', 'ity', 'ism', 'ist', 'ize', 'ise', 'ward', 'some', 'ship', 'hood', 'er', 'ed', 'ly')
VOWELS = set('aeiouyAEIOUY')


def _break_score(word, k):
    """How good a hyphen break before word[k] is: own hyphen > before a suffix > between two consonants.
    Fewer than 3 letters on either side is worst."""
    head, tail = word[:k], word[k:]
    letters = lambda s: sum(c.isalpha() for c in s)  # noqa: E731
    if head.endswith('-'):
        return 4
    if letters(head) < 3 or letters(tail.rstrip('.,!?;:)]>"\'')) < 3:
        return 0
    if tail.lower().rstrip('.,!?;:)]>"\'').startswith(SUFFIXES):
        return 3
    if head[-1].isalpha() and tail[0].isalpha() and head[-1] not in VOWELS and tail[0] not in VOWELS:
        return 2
    return 1


def wrap(s, limit=DLG_PX, ui=False):
    """Greedy wrap on spaces, keeping explicit breaks. Returns the list of lines."""
    lines = []
    for para in s.split(NL):
        cur = ''
        for word in (p for w in para.split(' ') for p in hyphenate(w, limit, ui)):
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
    lo, hi = min(max(width(w, ui) for w in s.split(' ')), limit), limit
    while lo < hi:  # smallest limit that still gives n lines
        mid = (lo + hi) // 2
        if len(wrap(s, mid, ui)) <= n:
            hi = mid
        else:
            lo = mid + 1
    return wrap(s, lo, ui)


def fit_dialogue(s):
    """English as stored for a dialogue line: wrapped with literal \\n. Errors -> ValueError.
    Translators' breaks were written for the old 3-line box, so the text is reflowed."""
    lines = balanced(s.replace(NL, ' '))
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
