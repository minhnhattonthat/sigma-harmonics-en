"""Build the English ROM.

python -X utf8 tools/build.py            -> build/sigma_en.nds
python -X utf8 tools/build.py --marker   -> build/sigma_marker.nds (every string -> "[file:idx] marker")
python -X utf8 tools/build.py --identity -> rebuild with no edits, assert byte-identical to the original
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rom  # noqa: E402
import text  # noqa: E402

BUILD = text.ROOT / 'build'


def marker(r):
    if r['jp'] == '':
        return ''
    return f"[{r['id']}] The quick brown fox jumps"


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
        rep, out = text.replacements(c, script), BUILD / 'sigma_en.nds'
    BUILD.mkdir(exist_ok=True)
    out.write_bytes(rom.put_cpk(data, c.build(rep)))
    print(f'build: {len(rep)} files changed -> {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
