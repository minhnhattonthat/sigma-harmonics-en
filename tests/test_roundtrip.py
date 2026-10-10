import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import cpk  # noqa: E402
import rom  # noqa: E402
import strtab  # noqa: E402
import text  # noqa: E402

needs_rom = pytest.mark.skipif(not text.ROM.exists(), reason='original ROM not in rom/')


@pytest.fixture(scope='module')
def orig():
    return text.load_rom()


@needs_rom
def test_identity_rebuild(orig):
    data, c = orig
    assert rom.put_cpk(data, c.build()) == data


@needs_rom
def test_strtab_roundtrip_and_script_matches_rom(orig):
    _, c = orig
    script = text.load_script()
    seen = set()
    for f, b in text.tables(c):
        s = strtab.decode(b)
        assert strtab.encode(s, strtab.tail_pad(b)) == b
        assert [r['jp'] for r in script[f['id']]] == s, f['name']
        seen.add(f['id'])
    assert seen == set(script)


def test_utf_build_roundtrip():
    cols = [('ID', 0x52, None), ('FileSize', 0x54, None), ('Name', 0x5A, None), ('K', 0x34, 7)]
    rows = [{'ID': 1, 'FileSize': 70000, 'Name': 'a', 'K': 7}, {'ID': 2, 'FileSize': 3, 'Name': 'あ', 'K': 7}]
    b = cpk.utf_build('T', cols, rows)
    assert cpk.utf_parse(b) == ('T', cols, rows)


@needs_rom
def test_screen_edit_roundtrip(orig):
    import scredit
    _, c = orig
    byid = {f['id']: f for f in c.files}
    for n in (63, 93, 2624, 1118):  # 8bpp, 4bpp with per-tile palettes, 72 tiles sharing a blank one, 64 wide
        g, p, s = (c.get(byid[n + k]) for k in range(3))
        im = scredit.player_view(g, p, s)
        assert scredit.encode(g, p, s, im.rotate(-90, expand=True)) == (g, s)  # untouched image: bytes unchanged
        fill = [214, 82, 165] if n == 93 else [255, 255, 255]  # 4bpp cells only have their palette's colours
        recipe = {'text': [{'text': 'Test', 'box': [0, 0, 192, 256], 'size': 40, 'fill': fill}]}
        ed, ng, ns = scredit.apply(g, p, s, recipe)
        assert ng != g
        back = scredit.player_view(ng, p, ns)  # every changed pixel lands; colours only shift by quantisation
        diff = sum(1 for a, b in zip(back.getdata(), ed.getdata()) if sum(abs(x - y) for x, y in zip(a, b)) > 96)
        assert diff < 0.01 * back.width * back.height, diff


def test_script_ids_stable():
    for p in sorted(text.SCRIPT.glob('*.json')):
        rows = json.loads(p.read_text(encoding='utf-8'))
        assert [r['id'] for r in rows] == [f'{p.stem}:{i:04d}' for i in range(len(rows))], p.name
