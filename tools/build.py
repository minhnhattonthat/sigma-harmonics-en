"""Build the English ROM.

python -X utf8 tools/build.py            -> build/sigma_en.nds
python -X utf8 tools/build.py --marker   -> build/sigma_marker.nds (every string -> "[file:idx] marker")
python -X utf8 tools/build.py --identity -> rebuild with no edits, assert byte-identical to the original
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402
import dlgfont  # noqa: E402
import fit  # noqa: E402
import gridfont  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402
import rom  # noqa: E402
import text  # noqa: E402
import scredit  # noqa: E402
import sprite  # noqa: E402
import texedit  # noqa: E402

BUILD = text.ROOT / 'build'
JP = re.compile('[぀-ヿ一-鿿]')


MARK_DLG = {k: v['form'] == 'dlg' for k, v in batches.load_meta().items()} if batches.META.exists() else {}
MARK_LINES =['The quick brown fox', 'jumps over the lazy dog.', 'Sphinx of black quartz!']


def marker(r):
    """'[file:idx]' then pangram lines, keeping the original line count; non-text (digits, blanks) kept."""
    if not JP.search(r['jp']):
        return r['jp']
    n = r['jp'].count('\\n') + 1
    f, i = r['id'].split(':')
    s = '\\n'.join([f'[{int(f)}:{int(i)}] ' + MARK_LINES[0]] + MARK_LINES[1:n])
    return s if MARK_DLG.get(int(f), True) else to_fullwidth(s)


CTRL = re.compile(r'(\$c\d\d|\\n)')


def to_fullwidth(s, chars=' ~'):
    """Swap ASCII in [chars[0], chars[1]] for the full-width twins, which the fonts draw with the same narrow
    Latin glyphs. UI routines (e.g. location names, table 6413) hang on any 1-byte UTF-8, so UI text swaps all;
    the dialogue renderer clips the glyph after any of 0x50-0x5F (P-Z [ \\ ] ^ _), so dialogue swaps only those.
    Control codes ($cNN, \\n) stay ASCII."""
    lo, hi = chars
    return ''.join(p if CTRL.fullmatch(p) else ''.join(chr(latin.fullwidth(ch)) if lo <= ch <= hi else ch for ch in p)
                   for p in CTRL.split(s))


def fonts(c):
    """Every NFTR gets the ASCII glyphs it lacks."""
    out = {}
    for f in c.files:
        if f['usize'] < 4 or c.raw(f)[:4] not in (b'RTFN', bytes(4)):
            continue
        x = c.get(f)
        if x[:4] != b'RTFN':
            continue
        new = latin.add_ascii(x, condensed=f['id'] == gridfont.BANNER_FONT)
        out[f['id']] = (new, len(new))
    return out


def main(argv):
    data, c = text.load_rom()
    if '--identity' in argv:
        assert rom.put_cpk(data, c.build()) == data, 'identity rebuild differs'
        print('identity: ok')
        return
    script = text.load_script()
    byid = {f['id']: f for f in c.files}
    plan = None
    if '--marker' in argv:
        rep, out = text.replacements(c, script, marker), BUILD / 'sigma_marker.nds'
    else:
        meta = batches.load_meta()
        dlg = []
        for fid, rows in script.items():
            for r in rows:
                if r['en'] and meta[fid]['form'] == 'dlg':
                    r['en'] = fit.fit_dialogue(r['en'])
                    dlg.append(r)
                elif r['en'] and not gridfont.is_grid(r['id']):  # grid names: see gridfont, encoded below
                    r['en'] = to_fullwidth(r['en'])
        keep = {ch for rows in script.values() for r in rows if not r['en'] for ch in r['jp']}  # still Japanese
        taken, grids = set(nftr.codes(c.get(byid[gridfont.FONT]))), {}
        for style in sorted(set(gridfont.STYLES.values())):  # chunk codes of every style share the font's free range
            grids[style] = gridfont.Plan([r['en'] for rows in script.values() for r in rows
                                          if r['en'] and gridfont.style_of(r['id']) == style], taken, style)
            taken |= set(grids[style].code.values())
        plan = dlgfont.Plan([r['en'] for r in dlg], dlgfont.slots(c.get(byid[dlgfont.FONT]), keep))
        for r in dlg:
            r['en'] = plan.encode(r['en'])
        names = script[5609]
        assert len(names) == gridfont.BANNER
        names += [{'id': f'05609:{gridfont.BANNER + k:04d}', 'jp': r['jp'], 'en': to_fullwidth(r['en'] or r['jp'])}
                  for k, r in enumerate(names[gridfont.FIRST:])]  # plain copies for the battle banner
        for rows in script.values():
            for r in rows:
                if r['en'] and gridfont.is_grid(r['id']):
                    r['en'] = to_fullwidth(grids[gridfont.style_of(r['id'])].encode(r['en']))
        rep, out = text.replacements(c, script), BUILD / 'sigma_en.nds'
    rep.update(fonts(c))
    if plan:
        new = plan.font(rep[dlgfont.FONT][0])
        rep[dlgfont.FONT] = (new, len(new))
        new = rep[gridfont.FONT][0]
        for k, style in enumerate(grids):
            new = grids[style].font(new, recell=k == 0)  # the cell grows once
        rep[gridfont.FONT] = (new, len(new))
    for tid, recipe in texedit.recipes().items():  # English UI textures (font/textures.json)
        _, new = texedit.apply(tid, recipe, c.get(byid[int(tid)]))
        rep[int(tid)] = (new, len(new))
    for sid, recipe in scredit.recipes().items():  # English full-screen graphics (font/screens.json)
        n = int(sid)
        _, g, s = scredit.apply(*(c.get(byid[n + k]) for k in range(3)), recipe)
        rep[n], rep[n + 2] = (g, len(g)), (s, len(s))
    for sid, recipe in sprite.recipes().items():  # English sprite labels (font/sprites.json)
        n = int(sid)
        g = sprite.apply(*(c.get(byid[n + k]) for k in (-1, 0, 1)), recipe)
        rep[n] = (g, len(g))
    BUILD.mkdir(exist_ok=True)
    new_rom = rom.put_cpk(data, c.build(rep))
    out.write_bytes(dlgfont.patch_arm9(new_rom) if plan else new_rom)
    print(f'build: {len(rep)} files changed -> {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
