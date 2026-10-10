"""Echo names already settled in dialogue: build/echoes.tsv (JP name<TAB>EN name<TAB>id).

Source lines: 【X】\\nの刻音を手に入れた！ / を生みだした！ -> "Obtained/Created the [Y] Echo!".
UI tables (the Echo list 04390, Super Reasoning screens) must reuse these names.
python -X utf8 tools/echoes.py
"""
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import text  # noqa: E402

JP = re.compile(r'【(.+?)】(?:\\n)?の刻音を(?:手に入れた|生みだした)')
EN = re.compile(r'\[(.+?)\] Echo')


def main():
    seen = collections.defaultdict(collections.Counter)
    first = {}
    for rows in text.load_script().values():
        for r in rows:
            mj, me = JP.search(r['jp']), EN.search(r['en'])
            if mj and me:
                seen[mj.group(1)][me.group(1)] += 1
                first.setdefault(mj.group(1), r['id'])
    out = text.ROOT / 'build' / 'echoes.tsv'
    lines, clashes = [], []
    for jp, c in sorted(seen.items()):
        en = c.most_common(1)[0][0]
        lines.append(f'{jp}\t{en}\t{first[jp]}')
        if len(c) > 1:
            clashes.append(f'{jp}: {dict(c)}')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(f'echoes: {len(lines)} names -> {out}; {len(clashes)} with variant English')
    for c in clashes:
        print('  ', c)


if __name__ == '__main__':
    main()
