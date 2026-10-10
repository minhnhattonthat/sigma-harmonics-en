"""Translation batches for agents.

python -X utf8 tools/batches.py meta            # build/tables.json: per table form (dlg|ui) and font (needs ROM)
python -X utf8 tools/batches.py split [--chars 3500]   # work/tl/bNNN.tsv + build/terms_bNNN.txt for untranslated text
python -X utf8 tools/batches.py check bNNN      # validate work/tl/bNNN.out.tsv; prints OK or errors
python -X utf8 tools/batches.py merge bNNN      # check, then write English into script/*.json (+ exact-duplicate JP)
python -X utf8 tools/batches.py pairs bNNN      # work/tl/bNNN.pairs.txt for the reviewer
python -X utf8 tools/batches.py apply NAME      # apply fixes in work/tl/NAME.tsv (id<TAB>English) to script/*.json

Input TSV: id<TAB>box<TAB>form<TAB>limit<TAB>jp   (jp line breaks shown as " / ")
Output TSV: id<TAB>English  (dialogue is auto-wrapped by the build; write \\n only in ui text that needs a break)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
TL = ROOT / 'work' / 'tl'
META = ROOT / 'build' / 'tables.json'
SPEAKERS = ROOT / 'build' / 'speakers.json'
GLOSSARY = ROOT / 'glossary.md'
JP = re.compile('[぀-ヿ一-鿿]')
TM_MIN = 10           # JP strings this long or longer share one translation across the game
BOX = {13: 'R', 12: 'L', 11: 'R-thought', 0: 'sys', 2: 'sys', 3: 'sys'}
ALLOWED = set(chr(c) for c in range(0x20, 0x7F))
ORDINAL = re.compile(r'\d(st|nd|rd|th)\b')


def meta():
    _, c = text.load_rom()
    byid = {f['id']: f for f in c.files}
    out = {}
    script = text.load_script()
    for fid in script:
        prev = byid.get(fid - 1)
        head = c.get(prev)[:8] if prev and prev['usize'] else b''
        jp = {ord(ch) for r in script[fid] for ch in r['jp'] if JP.match(ch)}
        if head[:4] == b'RTFN' and len(jp & nftr.codes(c.get(prev))) >= len(jp) / 2:
            out[fid] = {'form': 'ui', 'font': fid - 1, 'cell': _cell(c.get(prev))}
        elif head == b'Sigma000':
            out[fid] = {'form': 'dlg', 'font': 4387, 'cell': 16}
        else:  # no font of its own, or one that can't draw its text: assume the main 16 px font
            out[fid] = {'form': 'ui', 'font': 4387, 'cell': 16}
    META.parent.mkdir(exist_ok=True)
    META.write_text(json.dumps(out, indent=0), encoding='utf-8', newline='\n')
    print(f'meta: {len(out)} tables -> {META}')


def _cell(x):
    p = latin.params(x)
    return p['h'] if p['flags'] in (2, 6) else p['w']


def load_meta():
    return {int(k): v for k, v in json.loads(META.read_text(encoding='utf-8')).items()}


def is_text(jp):
    return bool(JP.search(jp))


UI_WINDOW = 100     # a UI row may use the widest JP line among its table neighbours: list boxes fit their longest entry
_ui_budget = {}


def _jp_budget(jp, cell):
    lines = jp.split(fit.NL)
    return len(lines), max(len(fit.CODE.sub('', ln)) for ln in lines) * (cell + fit.GAP)


def limit_of(row, m):
    """(lines, px) budget for a row."""
    if m['form'] == 'dlg':
        return fit.DLG_LINES, fit.DLG_PX
    if not _ui_budget:
        for rows in text.load_script().values():
            for k, r in enumerate(rows):
                _ui_budget[r['id']] = [r2['jp'] for r2 in rows[max(0, k - UI_WINDOW):k + UI_WINDOW + 1]
                                       if is_text(r2['jp'])]
    near = [_jp_budget(jp, m['cell']) for jp in _ui_budget.get(row['id'], [row['jp']])] or [_jp_budget(row['jp'], m['cell'])]
    px = max(px for _, px in near)
    measured = [v for k, v in MEASURED.items() if row['id'].startswith(k)]
    return max(n for n, _ in near), measured[0] if measured else max(px, PROVISIONAL.get(int(row['id'][:5]), 0))


# Term/skill lists: full names don't fit the JP-sized budget; box width unverified in game (docs/re/verify.md)
PROVISIONAL = {4741: 156, 4726: 210}
# Widths measured in game (id prefix -> px); override the budgets above
MEASURED = {
    '06413': 128,       # field location label, 128 px to the screen edge after the dlgfont.PATCH canvas move
    '04695:003': 54,    # save/load card chapter, before the fixed hour column
    '04703:003': 54,
    '04700': 113,       # save/load card location line, to the card border (narrow font: ~0.82 px per lint px)
    '04708': 113,
}
TERM_EXEMPT = ('04695:003', '04703:003')  # save card chapter: numerals only (I, Hidden III), no room for "Movement"


def errors(row, en, m):
    """Mechanical problems with an English line (empty list = fine)."""
    out = []
    bad = sorted(set(ch for ch in en if ch not in ALLOWED and ch not in row['jp']))  # JP's own chars are in the font
    if bad:
        out.append(f'non-ASCII {bad}')
    if fit.CODE.findall(en) != fit.CODE.findall(row['jp']):
        out.append(f"colour codes {fit.CODE.findall(row['jp'])} != {fit.CODE.findall(en)}")
    if re.search(r'\$(?!c\d\d)', en):
        out.append("stray '$' (only $cNN colour codes are allowed)")
    if ORDINAL.search(en):
        out.append('ordinal suffix after a number (rephrase)')
    nlines, px = limit_of(row, m)
    if m['form'] == 'dlg':
        try:
            fit.fit_dialogue(en)
        except ValueError as e:
            out.append(f'too long for the box: {e}')
    else:
        ui = m['font'] != 4387
        lines = en.split(fit.NL)
        if len(lines) > nlines:
            out.append(f'{len(lines)} lines, max {nlines}')
        wide = [f'{fit.width(ln, ui)}px' for ln in lines if fit.width(ln, ui) > px]
        if wide:
            out.append(f'line too wide {wide} (max {px}px)')
    return out


def glossary():
    """[(jp, en, avoid)] from the glossary tables."""
    rows = []
    for line in GLOSSARY.read_text(encoding='utf-8').split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.startswith('|') and len(cells) >= 2 and JP.search(cells[0]):
            avoid = [a.strip() for a in cells[4].split(',')] if len(cells) > 4 and cells[4] else []
            rows.append((cells[0], cells[1], avoid))
    return rows


def term_errors(jp, en, terms):
    out = []
    for tj, te, avoid in sorted(terms, key=lambda t: -len(t[0])):
        if tj not in jp:
            continue
        jp = jp.replace(tj, '\0')  # a longer term owns its span (時の調律者 is not 時の調律)
        if not any(v.strip().lower() in en.lower() for v in te.split(';')):  # ';' lists accepted short forms
            out.append(f'glossary: {tj} -> {te} missing')
        for a in avoid:
            if a and re.search(r'\b' + re.escape(a) + r'\b', en):
                out.append(f'glossary: avoid {a!r}')
    return out


def split(chars=3500):
    TL.mkdir(parents=True, exist_ok=True)
    script = text.load_script()
    m = load_meta()
    spk = json.loads(SPEAKERS.read_text(encoding='utf-8')) if SPEAKERS.exists() else {}
    seen = set()
    todo = []
    for fid in sorted(script):
        for r in script[fid]:
            if not is_text(r['jp']) or r['en']:
                continue
            if len(r['jp']) >= TM_MIN:
                if r['jp'] in seen:
                    continue
                seen.add(r['jp'])
            todo.append((fid, r))
    existing = sorted(TL.glob('b*.tsv'))
    n = len([p for p in existing if not p.name.endswith('.out.tsv')])
    batches, cur, size = [], [], 0
    for fid, r in todo:
        if cur and size + len(r['jp']) > chars:
            batches.append(cur)
            cur, size = [], 0
        cur.append((fid, r))
        size += len(r['jp'])
    if cur:
        batches.append(cur)
    terms = glossary()
    for k, b in enumerate(batches, n + 1):
        name = f'b{k:03d}'
        lines = []
        for fid, r in b:
            box = '/'.join(sorted({BOX.get(s[1], 'L') for s in spk.get(r['id'], [])})) or '-'
            nl, px = limit_of(r, m[fid])
            lines.append('\t'.join([r['id'], box, m[fid]['form'], f'{nl}x{px}px', r['jp'].replace(fit.NL, ' / ')]))
        (TL / f'{name}.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
        jp_all = ''.join(r['jp'] for _, r in b)
        rows = [f'{tj}\t{te}' + (f"\tavoid: {', '.join(av)}" if av else '') for tj, te, av in terms if tj in jp_all]
        (ROOT / 'build' / f'terms_{name}.txt').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    print(f'split: {len(todo)} entries -> {len(batches)} batches (b{n + 1:03d}..b{n + len(batches):03d})')


def read_out(name):
    out = {}
    path = TL / f'{name}.out.tsv'
    for ln in path.read_text(encoding='utf-8-sig').split('\n'):
        if not ln.strip():
            continue
        if '\t' not in ln:
            raise ValueError(f'{name}: line without a tab: {ln[:60]!r}')
        k, v = ln.split('\t', 1)
        if k in out:
            raise ValueError(f'{name}: duplicate id {k}')
        out[k] = v.strip()
    return out


def check(name, quiet=False):
    ids = [ln.split('\t', 1)[0] for ln in (TL / f'{name}.tsv').read_text(encoding='utf-8').split('\n') if ln]
    try:
        out = read_out(name)
    except (OSError, ValueError) as e:
        print(e)
        return False
    script = text.load_script()
    rows = {r['id']: (fid, r) for fid, rs in script.items() for r in rs}
    m = load_meta()
    terms = glossary()
    errs = []
    missing = [i for i in ids if i not in out]
    extra = [i for i in out if i not in ids]
    if missing:
        errs.append(f'missing ids: {missing[:10]}{"..." if len(missing) > 10 else ""}')
    if extra:
        errs.append(f'unknown ids: {extra[:10]}')
    for i, en in out.items():
        if i not in rows:
            continue
        fid, r = rows[i]
        if not en:
            errs.append(f'{i}: empty')
            continue
        for e in errors(r, en, m[fid]) + term_errors(r['jp'], en, terms):
            errs.append(f'{i}: {e}')
    for e in errs:
        print(e)
    if not errs and not quiet:
        print('OK')
    return not errs


def merge(name):
    if not check(name, quiet=True):
        sys.exit(f'merge {name}: refused (fix the errors above)')
    out = read_out(name)
    script = text.load_script()
    m = load_meta()
    by_jp = {}  # keyed by font too: the same JP in a smaller UI font needs its own (shorter) English
    for fid, rs in script.items():
        for r in rs:
            if r['id'] in out:
                r['en'] = out[r['id']]
                if len(r['jp']) >= TM_MIN:
                    by_jp[r['jp'], m[fid]['font']] = r['en']
    n = len(out)
    for fid, rs in script.items():
        for r in rs:
            if not r['en'] and (r['jp'], m[fid]['font']) in by_jp:
                r['en'] = by_jp[r['jp'], m[fid]['font']]
                n += 1
    for fid, rs in script.items():
        path = text.SCRIPT / f'{fid:05d}.json'
        new = json.dumps(rs, ensure_ascii=False, indent=1) + '\n'
        if path.read_text(encoding='utf-8') != new:
            path.write_text(new, encoding='utf-8', newline='\n')
    print(f'merge {name}: {n} entries written')


def apply(name):
    """Apply work/tl/<name>.tsv (id<TAB>English, any ids) to script/*.json after the usual checks.
    Holds work/tl/.apply.lock so parallel fixers don't overwrite each other's script files."""
    import os
    import time
    lock = TL / '.apply.lock'
    for _ in range(600):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL)
            break
        except FileExistsError:
            time.sleep(0.5)
    else:
        sys.exit(f'apply {name}: {lock} held for 5 min; delete it if no apply is running')
    try:
        _apply(name)
    finally:
        os.close(fd)
        lock.unlink()


def _apply(name):
    path = TL / f'{name}.tsv'
    fixes = dict(ln.split('\t', 1) for ln in path.read_text(encoding='utf-8-sig').split('\n') if '\t' in ln)
    script = text.load_script()
    m = load_meta()
    terms = glossary()
    errs, done = [], 0
    for fid, rs in script.items():
        for r in rs:
            if r['id'] not in fixes:
                continue
            en = fixes.pop(r['id']).strip()
            e = errors(r, en, m[fid]) + term_errors(r['jp'], en, terms)
            if e:
                errs += [f"{r['id']}: {x}" for x in e]
            else:
                r['en'] = en
                done += 1
    errs += [f'{i}: unknown id' for i in fixes]
    for e in errs:
        print(e)
    if errs:
        sys.exit(f'apply {name}: refused, nothing written')
    for fid, rs in script.items():
        p = text.SCRIPT / f'{fid:05d}.json'
        new = json.dumps(rs, ensure_ascii=False, indent=1) + '\n'
        if p.read_text(encoding='utf-8') != new:
            p.write_text(new, encoding='utf-8', newline='\n')
    print(f'apply {name}: {done} lines written')


def pairs(name):
    out = read_out(name)
    script = text.load_script()
    lines = []
    for fid, rs in script.items():
        for k, r in enumerate(rs):
            if r['id'] not in out:
                continue
            for c in rs[max(0, k - 2):k]:
                lines.append(f"   {c['id']} | {c['jp']} / {c['en']}")
            lines.append(f">> {r['id']} | {r['jp']}\n   EN: {r['en']}")  # merged English, incl. later fixes
    (TL / f'{name}.pairs.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(f'pairs: {TL / (name + ".pairs.txt")}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'meta':
        meta()
    elif cmd == 'split':
        split(int(sys.argv[sys.argv.index('--chars') + 1]) if '--chars' in sys.argv else 3500)
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2]) else 1)
    elif cmd == 'merge':
        merge(sys.argv[2])
    elif cmd == 'apply':
        apply(sys.argv[2])
    elif cmd == 'pairs':
        pairs(sys.argv[2])
