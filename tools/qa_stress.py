"""QA build: the hardest real dialogue strings shown in the opening scene (table 04086).

python -X utf8 tools/qa_stress.py   -> build/qa/sigma_stress.nds, prints which row got which string
Picks the bubbles with the most glyph records, 12 lines, colour codes and hyphen breaks, and puts them in the
opening rows the route tools/routes/newgame.txt + taps reaches, so one emulator run shows them all.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402
import build  # noqa: E402
import dlgfont  # noqa: E402
import fit  # noqa: E402
import text  # noqa: E402

ROWS = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13]


def pick(script):
    meta = batches.load_meta()
    dlg = [r for fid, rows in script.items() if meta[fid]['form'] == 'dlg' for r in rows if r['en']]
    wrapped = {r['id']: fit.fit_dialogue(r['en']) for r in dlg}
    plan = dlgfont.Plan(list(wrapped.values()), range(0x5000, 0x5000 + 1305))

    def records(i):
        e = plan.encode(wrapped[i])
        return sum(1 for ch in e if ord(ch) >= 0x5000) + e.count(fit.NL)
    by_rec = sorted(wrapped, key=records, reverse=True)
    twelve = [i for i in by_rec if wrapped[i].count(fit.NL) == fit.DLG_LINES - 1]
    colour = [i for i in by_rec if fit.CODE.search(wrapped[i])]
    hyph = sorted(wrapped, key=lambda i: wrapped[i].count('-' + fit.NL), reverse=True)
    out = []
    for group, n in ((by_rec, 4), (twelve, 3), (colour, 2), (hyph, 2)):
        out += [i for i in group if i not in out][:n]
    return out


def main():
    orig = text.load_script
    chosen = sys.argv[1].split(',') if len(sys.argv) > 1 else pick(orig())  # or explicit ids for ROWS
    src = {r['id']: r['en'] for rows in orig().values() for r in rows}

    def load_script():
        s = orig()
        for row, i in zip(ROWS, chosen):
            s[4086][row]['en'] = src[i]
        return s
    text.load_script = load_script
    build.BUILD = text.ROOT / 'build' / 'qa'
    build.main([])
    (build.BUILD / 'sigma_en.nds').replace(build.BUILD / 'sigma_stress.nds')
    for row, i in zip(ROWS, chosen):
        print(f'04086:{row:04d} <- {i}: {src[i][:70]}')


if __name__ == '__main__':
    main()
