import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import dlgfont  # noqa: E402
import fit  # noqa: E402
import text  # noqa: E402

needs_rom = pytest.mark.skipif(not text.ROM.exists(), reason='original ROM not in rom/')


def test_hyphenate_fits_and_prefers_own_hyphen():
    pieces = fit.hyphenate('Himekago-san-no-okusama', 40)
    assert all(fit.width(p) <= 40 for p in pieces)
    assert ''.join(pieces).replace('--', '-').replace('-', '') == 'Himekagosannookusama'.replace('-', '')
    assert not any(p.endswith('--') for p in pieces)
    assert pieces[0].endswith('-') and fit.hyphenate('cat', 40) == ['cat']
    assert fit.hyphenate('Handprints...', fit.DLG_PX)[0] == 'Hand-'  # not 'Handp-': keeps the 'pr' together


def test_plan_encodes_within_budget_and_centres():
    texts = [fit.fit_dialogue('This is the living room. ' * 2), fit.fit_dialogue('Hm?')]
    p = dlgfont.Plan(texts, range(0x5000, 0x5000 + 400))
    enc = p.encode(texts[1])
    pad = {cp: key[1] for key, cp in p.code.items() if isinstance(key, tuple)}
    assert ord(enc[0]) in pad and abs(pad[ord(enc[0])] * 2 + dlgfont.adv('Hm?') - fit.DLG_PX) <= 1
    long = p.encode(texts[0])
    assert sum(1 for ch in long if ord(ch) >= 0x5000) + long.count(fit.NL) <= dlgfont.MAX_RECORDS
    with pytest.raises(ValueError):
        p.encode(fit.NL.join(['Hm?'] * 61))


def test_chunked_line_looks_like_unchunked_line():
    """Bubble placement: each chunk at the pen, but an odd-advance glyph lands 1 px early (centred at advance / 2),
    which dlg_glyph(bubble=True) offsets. Chunk boundaries then add no gap and eat no space."""
    from PIL import Image, ImageChops
    import latin  # noqa: E402
    line = 'He was made to grip the floor too.'
    want = latin.dlg_image(line, 260, 16, 12)
    got, pen = Image.new('L', (260, 16), 0), 0
    for chunk in dlgfont._greedy(line, lambda c: len(c) <= 2 or c in (' to', 'was')):
        adv = dlgfont.adv(chunk)
        g = latin.dlg_image(chunk, 16, 16, 12, adv % 2)
        got = ImageChops.lighter(got, _at(got.size, g, pen - adv % 2))
        pen += adv
    # overlapping anti-aliased edges blend slightly differently; under one 3 bpp level (255 / 7) is the same pixel
    assert pen == dlgfont.adv(line) and ImageChops.difference(got, want).getextrema()[1] < 255 // 7


def _at(size, im, x):
    from PIL import Image
    out = Image.new('L', size, 0)
    out.paste(im, (x, 0))
    return out


@needs_rom
def test_arm9_patch_matches_original_code():
    data, _ = text.load_rom()
    assert dlgfont.patch_arm9(data) != data  # asserts every original word inside
