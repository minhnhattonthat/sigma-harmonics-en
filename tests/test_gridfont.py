import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import gridfont  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402
import text  # noqa: E402

needs_rom = pytest.mark.skipif(not text.ROM.exists(), reason='original ROM not in rom/')


def names(table):
    return sorted({r['en'] for r in text.load_script()[int(table)] if r['en'] and gridfont.is_grid(r['id'])})


@pytest.mark.parametrize('table', sorted(gridfont.STYLES))
def test_every_name_fits_two_lines(table):
    style = gridfont.STYLES[table]
    ns = names(table)
    assert len(ns) > 50
    assert [n for n in ns if gridfont.errors(n, style)] == []
    assert len(gridfont.lines('Heal')) == 1 and len(gridfont.lines('Divine Follow-up Attack')) == 2


def test_tiny_style_chunks_every_name():
    # plain text would be centred from the re-celled glyph widths (+7 px each): "Big Stop" fell off the battle screen
    p = gridfont.Plan(['Big Stop', 'Divine Follow-up Attack'], (), 'tiny')
    one = gridfont.strip(gridfont.lines('Big Stop', 'tiny'), 'px9')
    assert all(ord(c) >= gridfont.CODE0 for c in p.encode('Big Stop')) and len(p.encode('Divine Follow-up Attack')) > 3
    assert not any(any(r) for r in one[11:])  # one px9 line, descenders included, above the battle screen edge
    rows = gridfont.strip(gridfont.lines('Divine Follow-up Attack'), 'tiny')
    assert not any(any(r) for r in rows[11:])  # two 5-row lines (rows 0-4, 6-10) fit the 11 rows above the screen edge


@needs_rom
def test_font_recell_keeps_glyphs_and_adds_chunks():
    _, c = text.load_rom()
    x = c.get({f['id']: f for f in c.files}[gridfont.FONT])
    a = gridfont.Plan(['Self-Heal', 'Divine Self-Heal'], nftr.codes(x))
    b = gridfont.Plan(['Weak Follow-up Attack'], nftr.codes(x) | set(a.code.values()), 'tiny')
    y = b.font(a.font(x), recell=False)
    p = latin.params(y)
    assert (p['w'], p['h'], p['size']) == (16, 9, gridfont.SIZE)
    for cp in sorted(nftr.codes(x))[:40]:  # an old glyph keeps its ink: the 9 old columns sit at columns 7..15
        old, new = nftr.glyph(x, nftr.lookup(x, cp)), nftr.glyph(y, nftr.lookup(y, cp))
        assert gridfont._recell(old) == new
        assert nftr.widths(y, nftr.lookup(y, cp))[1] in (0, nftr.widths(x, nftr.lookup(x, cp))[1] + 7)
    for cp in list(a.code.values()) + list(b.code.values()):
        assert nftr.widths(y, nftr.lookup(y, cp))[1] == 16 and len(nftr.glyph(y, nftr.lookup(y, cp))) == gridfont.SIZE
