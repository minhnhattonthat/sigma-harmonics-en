"""Extract / insert the UTF-8 string tables in data.cpk.

python -X utf8 tools/text.py extract   # writes missing script/NNNNN.json only (never clobbers English)
Entries: {"id": "NNNNN:iiii", "jp": ..., "en": ""}. Empty "en" means untranslated -> Japanese is kept.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cpk  # noqa: E402
import rom  # noqa: E402
import strtab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / 'rom' / 'Sigma Harmonics (Japan).nds'
SCRIPT = ROOT / 'script'


def skill_script(name):
    """Path of a translate-retro-game skill script (emu.py, sheet.py, ...): $RETRO_SKILL (the skill folder, e.g. a
    clone's skills/translate-retro-game) or the newest copy the Claude Code plugin installed."""
    import os
    if os.environ.get('RETRO_SKILL'):
        return Path(os.environ['RETRO_SKILL']) / 'scripts' / name
    found = sorted(Path.home().glob(f'.claude/plugins/*/*/**/skills/translate-retro-game/scripts/{name}'),
                   key=lambda p: p.stat().st_mtime)
    if not found:
        sys.exit(f'{name} not found: install the translate-retro-game plugin (/plugin) or set RETRO_SKILL to a '
                 'clone of github.com/minhnhattonthat/translate-retro-game/skills/translate-retro-game')
    return found[-1]


def load_rom():
    data = ROM.read_bytes()
    return data, cpk.Cpk(rom.get_cpk(data))


def tables(c):
    """Yield (cpk file entry, decompressed bytes) for every string-table file."""
    for f in c.files:
        if f['usize'] < 8:
            continue
        b = c.get(f)
        if strtab.is_strtab(b):
            yield f, b


def extract(force=False):
    SCRIPT.mkdir(exist_ok=True)
    _, c = load_rom()
    n = 0
    for f, b in tables(c):
        path = SCRIPT / f"{f['name']}.json"
        if path.exists() and not force:
            continue
        rows = [{'id': f"{f['name']}:{i:04d}", 'jp': s, 'en': ''} for i, s in enumerate(strtab.decode(b))]
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        n += 1
    print(f'extract: wrote {n} files')


def load_script():
    """{file id: [rows]} for every script file."""
    return {int(p.stem): json.loads(p.read_text(encoding='utf-8')) for p in sorted(SCRIPT.glob('*.json'))}


def replacements(c, script, transform=None):
    """{id: (stored, usize)} for files whose text changes. transform(row) -> output string (default en or jp)."""
    pick = transform or (lambda r: r['en'] or r['jp'])
    out = {}
    byid = {f['id']: f for f in c.files}
    for fid, rows in script.items():
        f = byid[fid]
        orig = c.get(f)
        new = strtab.encode([pick(r) for r in rows], strtab.tail_pad(orig))
        if new != orig:
            out[fid] = (new, len(new))  # shortcut: stored uncompressed; add a CRILAYLA encoder if ROM space runs out
    return out


if __name__ == '__main__':
    if sys.argv[1:2] == ['extract']:
        extract(force='--force' in sys.argv)
    else:
        print(__doc__)
