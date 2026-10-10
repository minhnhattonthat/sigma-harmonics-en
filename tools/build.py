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
import fit  # noqa: E402
import latin  # noqa: E402
import rom  # noqa: E402
import text  # noqa: E402

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
        new = latin.add_ascii(x)
        out[f['id']] = (new, len(new))
    return out


def main(argv):
    data, c = text.load_rom()
    if '--identity' in argv:
        assert rom.put_cpk(data, c.build()) == data, 'identity rebuild differs'
        print('identity: ok')
        return
    script = text.load_script()
    if '--marker' in argv:
        rep, out = text.replacements(c, script, marker), BUILD / 'sigma_marker.nds'
    else:
        meta = batches.load_meta()
        for fid, rows in script.items():
            for r in rows:
                if r['en'] and meta[fid]['form'] == 'dlg':
                    r['en'] = to_fullwidth(fit.fit_dialogue(r['en']), 'P_').replace(' ', chr(latin.SPACE))
                elif r['en']:
                    r['en'] = to_fullwidth(r['en'])
        rep, out = text.replacements(c, script), BUILD / 'sigma_en.nds'
    rep.update(fonts(c))
    BUILD.mkdir(exist_ok=True)
    out.write_bytes(rom.put_cpk(data, c.build(rep)))
    print(f'build: {len(rep)} files changed -> {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
