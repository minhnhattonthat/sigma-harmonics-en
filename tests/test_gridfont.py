import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import gridfont  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402
import text  # noqa: E402

needs_rom = pytest.mark.skipif(not text.ROM.exists(), reason='original ROM not in rom/')


def grid_names():
    return sorted({r['en'] for r in text.load_script()[int(gridfont.TABLE)] if r['en'] and gridfont.is_grid(r['id'])})


def test_every_grid_name_fits_two_lines():
    names = grid_names()
    assert len(names) > 50
    assert [n for n in names if gridfont.errors(n)] == []
    assert len(gridfont.lines('Heal')) == 1 and len(gridfont.lines('Divine Follow-up Attack')) == 2


@needs_rom
def test_font_recell_keeps_glyphs_and_adds_chunks():
    _, c = text.load_rom()
    x = c.get({f['id']: f for f in c.files}[gridfont.FONT])
    plan = gridfont.Plan(['Self-Heal', 'Divine Self-Heal'], nftr.codes(x))
    y = plan.font(x)
    p = latin.params(y)
    assert (p['w'], p['h'], p['size']) == (16, 9, gridfont.SIZE)
    for cp in sorted(nftr.codes(x))[:40]:  # an old glyph keeps its ink: the 9 old columns sit at columns 7..15
        old, new = nftr.glyph(x, nftr.lookup(x, cp)), nftr.glyph(y, nftr.lookup(y, cp))
        assert gridfont._recell(old) == new
        assert nftr.widths(y, nftr.lookup(y, cp))[1] in (0, nftr.widths(x, nftr.lookup(x, cp))[1] + 7)
    for cp in plan.code.values():
        assert nftr.widths(y, nftr.lookup(y, cp))[1] == 16 and len(nftr.glyph(y, nftr.lookup(y, cp))) == gridfont.SIZE
