"""Apply Echo renames from a TSV (JP name<TAB>new EN) across every table, and normalise the Echo-get template.

Old English comes from build/echoes.tsv (run tools/echoes.py first). A rename replaces the old name only in rows
whose JP contains the JP name (dialogue, Echo list 04390, title tables), so unrelated text is never touched.
Template: "Obtained/Created the [X] Echo!" -> "Obtained/Created the Echo [X]!" (avoids "the [The ...] Echo").
python -X utf8 tools/echo_pass.py work/tl/echo_renames.tsv [--dry]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import text  # noqa: E402

TEMPLATE = re.compile(r'\b(Obtained|Created) the \[([^\]]+)\] Echo\b')


def main(argv):
    old = {jp: en for jp, en, _ in (l.split('\t') for l in (text.ROOT / 'build' / 'echoes.tsv').read_text(encoding='utf-8').splitlines())}
    renames = [l.split('\t') for l in Path(argv[0]).read_text(encoding='utf-8').splitlines() if l.strip()]
    counts = {jp: 0 for jp, _ in renames}
    tmpl = 0
    for p in sorted(text.SCRIPT.glob('*.json')):
        rows = json.loads(p.read_text(encoding='utf-8'))
        changed = False
        for r in rows:
            en = r['en']
            for jp, new in renames:  # list copies vary the trailing ellipsis
                if jp.rstrip('…') in r['jp'] and old.get(jp) and old[jp] != new and old[jp] in en:
                    en = en.replace(old[jp], new)
                    counts[jp] += 1
            en, n = TEMPLATE.subn(r'\1 the Echo [\2]', en)
            tmpl += n
            if en != r['en']:
                r['en'], changed = en, True
        if changed and '--dry' not in argv:
            p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    for jp, new in renames:
        print(f'{counts[jp]:3d}  {jp} : {old.get(jp, "?")} -> {new}')
    print(f'template: {tmpl} lines')


if __name__ == '__main__':
    main(sys.argv[1:])
