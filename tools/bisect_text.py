"""Find which string tables break a route when given marker text.

python -X utf8 tools/bisect_text.py ROUTE [--min ID] [--max ID]
Builds marker variants (fonts always patched) over halves of the candidate set and boots each with
emu.py --smoke; a black final frame (exit 3) means that half holds a culprit.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import rom  # noqa: E402
import text  # noqa: E402

EMU = text.skill_script('emu.py')


def boots(c, data, script, ids, fonts, route, tag):
    rep = text.replacements(c, {k: script[k] for k in ids}, build.marker)
    rep.update(fonts)
    out = text.ROOT / 'build' / 'bisect.nds'
    out.write_bytes(rom.put_cpk(data, c.build(rep)))
    r = subprocess.run([sys.executable, '-X', 'utf8', str(EMU), str(out), '--out', f'work/qa/bisect_{tag}',
                        '--route', route, '--smoke'], cwd=text.ROOT, capture_output=True, text=True)
    ok = r.returncode == 0
    print(f'{tag}: {len(ids)} files {min(ids)}..{max(ids)} -> {"ok" if ok else "BROKEN"}', flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('route')
    ap.add_argument('--min', type=int, default=0)
    ap.add_argument('--max', type=int, default=99999)
    a = ap.parse_args()
    data, c = text.load_rom()
    script = text.load_script()
    fonts = build.fonts(c)
    cand = sorted(k for k in script if a.min <= k <= a.max)
    n = 0
    if boots(c, data, script, cand, fonts, a.route, 'all'):
        print('route passes with every candidate')
        return
    while len(cand) > 1:
        half = cand[:len(cand) // 2]
        n += 1
        cand = cand[len(cand) // 2:] if boots(c, data, script, half, fonts, a.route, str(n)) else half
    print('culprit:', cand[0])


if __name__ == '__main__':
    main()
