"""Reach any story event or room from a cold boot, no user save and no playthrough.

python -X utf8 tools/debug/tour.py [TABLE ..] [--rooms [N ..]] [--scenes [NAME ..]] [--rom build/sigma_en.nds]
                                    [--out work/qa/events] [--jobs 4] [--frames N] [--host 4086] [--rebase]
                                    [--chapter C] [--sweep]

Events (default): TABLE is a dialogue text table id (script/NNNNN.json; its script is TABLE-1). No TABLE = every
dialogue table in tools/tables.json. Each run starts New Game; warp.lua swaps the opening event's files for the
event's, then taps through its dialogue. Scripts branch on the save card's chapter byte: --chapter C plays
them in chapter C; --sweep retries every event that showed under half its rows in each chapter and keeps the best.
Rooms (--rooms): N is the room byte of the save card (scenario script 5914+N). No N = every room. A base game
struct is captured once from a New Game run (OUT/base/game.bin; --rebase redoes it), mksave.py turns it into a
save with that room, and the run Continues from it (tools/routes/continue.txt).
Scenes (--scenes): named screens from tools/debug/scenes.json (field, battle, menu, descent, ...). No NAME = all.
Per case: OUT/<id>/f*.png, sheet.png (frames after the warp), log.txt. OUT/report.tsv: id, result (ok [rows shown/total,
missing rows] / no-warp / blank / exit N). Exit 1 if any case is not ok. Read the sheets: ok only means it ran and showed a picture.
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCENES = json.loads((HERE / 'scenes.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(ROOT / 'tools'))
import text  # noqa: E402
EMU = text.skill_script('emu.py')
SHEET = EMU.with_name('sheet.py')


def dialogue_tables():
    meta = json.loads((ROOT / 'tools/tables.json').read_text(encoding='utf-8'))
    return sorted(int(k) for k, v in meta.items() if v['form'] == 'dlg')


def all_rooms(rom):
    import cpk
    import rom as romfs
    c = cpk.Cpk(romfs.get_cpk(Path(rom).read_bytes()))
    sig = {f['id'] for f in c.files if f['usize'] and c.get(f)[:8] == b'Sigma000'}
    return [n for n in range(1, 256) if 5914 + n in sig and 5914 + n < 6060]


def emu(out, args):
    cmd = [sys.executable, '-X', 'utf8', str(EMU), *args, '--out', str(out)]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).returncode


def verdict(code, out, need):
    log = (out / 'log.txt').read_text(encoding='utf-8', errors='replace') if (out / 'log.txt').exists() else ''
    if any(out.glob('f*.png')):
        subprocess.run([sys.executable, str(SHEET), str(out), '--from', '2000', '--changed', '0.02', '--max', '24'],
                       cwd=ROOT, capture_output=True)
    return 'blank' if code == 3 else f'exit {code}' if code else 'no-warp' if need not in log else 'ok'


def rows_of(table):
    return len(json.loads((ROOT / f'script/{table:05d}.json').read_text(encoding='utf-8')))


FIELD_HOST = 4512  # first field event: field events crash in the opening's place; it loads ~2400 frames later


def play(table, a, out, frames, chapter, host):
    """One cold-boot run of the event; chapter = save-card chapter byte set as it loads (scripts branch on it).
    Returns (verdict, set of text rows the dialogue fetched: warp.lua logs "msg 2 <row>")."""
    poke = ['--var', f'CHAPTER={chapter}'] if chapter else []
    frames += 2400 if host == FIELD_HOST else 0
    code = emu(out, [a.rom, '--route', str(HERE / 'newgame.txt'), '--frames', str(frames),
                     '--timeout', str(frames // 15 + 180), '--shot-every', '60', '--mash', '40', '--mash-key', 't128,96',
                     '--script', str(HERE / 'warp.lua'), '--var', f'TABLE={table}', '--var', f'HOST={host}', *poke])
    res = verdict(code, out, 'warp ')
    log = (out / 'log.txt').read_text(encoding='utf-8', errors='replace') if res == 'ok' else ''
    return res, {int(x) for x in re.findall(r'^msg 2 (\d+)$', log, re.M) if int(x) < rows_of(table)}


def event(table, a):
    out = Path(a.out) / f'{table:05d}'
    rows = rows_of(table)
    frames = a.frames or min(3000 + 90 * rows, 45000)  # ~2 taps per line; the warp lands ~frame 2300
    chapter, host = a.chapter or 0, a.host
    res, shown = play(table, a, out, frames, chapter, host)
    if res.startswith('exit') and res != 'exit 124' and host != FIELD_HOST:  # emulator crash: retry in the field
        host = FIELD_HOST
        res, shown = play(table, a, out, frames, chapter, host)
    if a.sweep and res == 'ok' and len(shown) * 2 < rows:  # mostly unseen: try the other chapters (short probes)
        probes = {c: len(play(table, a, out / f'ch{c}', min(frames, 6000), c, host)[1]) for c in range(8)}
        best = max(probes, key=probes.get)
        if probes[best] > probes[chapter]:
            chapter = best
            res, shown = play(table, a, out, frames, chapter, host)
    if res == 'ok':  # unshown rows: other choice branches, lines needing more story context, or a stall
        res += f' {len(shown)}/{rows} ch{chapter} host{host}' + (
            f' missing {sorted(set(range(rows)) - shown)}' if len(shown) < rows else '')
    return res


def base(a):
    """New Game game struct (save card + state) captured at frame 5400: the start for every built save."""
    b = Path(a.out) / 'base'
    if a.rebase or not (b / 'game.bin').exists():
        emu(b, [a.rom, '--route', str(ROOT / 'tools/routes/newgame.txt'), '--frames', '5401',
                '--script', str(HERE / 'capture.lua'), '--var', 'CAPTURE_AT=5400'])
    return b / 'game.bin'


def save(out, a, args):
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(HERE / 'mksave.py'), 'new', str(out / 'scene.dsv'),
                    '--state', str(base(a)), *args], cwd=ROOT, check=True)
    return ['--sav', str(out / 'scene.dsv')]


def room(n, a):
    out = Path(a.out) / f'r{n:03d}'
    code = emu(out, [a.rom, '--route', str(ROOT / 'tools/routes/continue.txt'), *save(out, a, ['--card', f'0xa={n}']),
                     '--frames', '4200', '--shot-every', '60', '--smoke'])
    return verdict(code, out, '')


def scene(name, a):
    s, out = SCENES[name], Path(a.out) / name
    route = s['route']
    sav = []
    if 'save' in s:
        sav = save(out, a, s['save'])
        route = ';'.join(f'{line.split("#")[0].strip()}' for line in
                         (ROOT / 'tools/routes/continue.txt').read_text(encoding='utf-8').splitlines()
                         if line.split('#')[0].strip()) + ';' + route
    code = emu(out, [a.rom, '--route-str', route, *sav, '--shot-every', '60', '--smoke', *s.get('args', [])])
    return verdict(code, out, '')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ids', nargs='*', type=int)
    ap.add_argument('--rooms', action='store_true')
    ap.add_argument('--scenes', nargs='*')
    ap.add_argument('--rom', default='build/sigma_en.nds')
    ap.add_argument('--out')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--frames', type=int, default=0, help='events: default 3000 + 90 per text row')
    ap.add_argument('--host', type=int, default=4086)
    ap.add_argument('--chapter', type=int, help='events: save-card chapter byte (0-7) to play them in')
    ap.add_argument('--sweep', action='store_true', help='events showing under half their rows: retry chapters 0-7')
    ap.add_argument('--rebase', action='store_true')
    a = ap.parse_args()
    a.out = a.out or ('work/qa/scenes' if a.scenes is not None else 'work/qa/rooms' if a.rooms else 'work/qa/events')
    if a.scenes is not None:
        base(a)
        ids, fn, name = a.scenes or [k for k in SCENES if not k.startswith('_')], scene, '{}'
    elif a.rooms:
        base(a)
        ids, fn, name = a.ids or all_rooms(a.rom), room, 'r{:03d}'
    else:
        ids, fn, name = a.ids or dialogue_tables(), event, '{:05d}'

    def one(i):
        res = fn(i, a)
        print(name.format(i), res, flush=True)
        return i, res

    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(one, ids))
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / 'report.tsv').write_text(''.join(f'{name.format(i)}\t{r}\n' for i, r in results), encoding='utf-8')
    bad = [name.format(i) for i, r in results if not r.startswith('ok')]
    print(f'{len(results) - len(bad)}/{len(results)} ok' + (f'; not ok: {bad}' if bad else ''))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
