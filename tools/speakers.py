"""Speaker ids for every string, read from the Sigma scripts (CPK entry N-1 drives string table N).

Script bytecode bits used here: 06 <i32> = push; 13 <u32 func> <u8 0> <u8 argc> = call builtin.
Message call 0xECEC(a, b, expr, char_id, side, msg_index). Other calls whose last arg is a message index
are recorded by function id. Writes build/speakers.json: {"NNNNN:iiii": [char_id, ...]}.
python -X utf8 tools/speakers.py [--stats]
"""
import collections
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import text  # noqa: E402

MSG = 0xECEC


def calls(b):
    """Yield (func, args) for every builtin call whose args are all literal pushes."""
    for i in range(8, len(b) - 7):
        if b[i] != 0x13 or b[i + 5] != 0:
            continue
        func, argc = struct.unpack_from('<I', b, i + 1)[0], b[i + 6]
        args, j = [], i
        while len(args) < argc and j >= 5 and b[j - 5] == 6:
            args.insert(0, struct.unpack_from('<i', b, j - 4)[0])
            j -= 5
        if len(args) == argc:
            yield func, args


def main():
    _, c = text.load_rom()
    byid = {f['id']: f for f in c.files}
    script = text.load_script()
    out = collections.defaultdict(list)
    funcs = collections.Counter()
    for fid, rows in script.items():
        s = byid.get(fid - 1)
        if not s or s['usize'] < 8:
            continue
        b = c.get(s)
        if b[:8] != b'Sigma000':
            continue
        cl = list(calls(b))
        # the message routine is script-local (func = code offset): pick the 6-arg call covering most indices
        cover = collections.defaultdict(set)
        for func, args in cl:
            if len(args) == 6 and 0 <= args[5] < len(rows):
                cover[func].add(args[5])
        if not cover:
            continue
        msg = max(cover, key=lambda f: len(cover[f]))
        funcs[tuple(sorted((len(v) for v in cover.values()), reverse=True)[:3])] += 1
        for func, args in cl:
            if func == msg and len(args) == 6 and 0 <= args[5] < len(rows):
                key = rows[args[5]]['id']
                if args[2:4] not in out[key]:
                    out[key].append(args[2:4])
    path = text.ROOT / 'build' / 'speakers.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=0), encoding='utf-8', newline='\n')
    total = sum(len(r) for r in script.values())
    print(f'speakers: {len(out)}/{total} strings have a speaker -> {path}')
    if '--stats' in sys.argv:
        ids = collections.Counter(tuple(v) for vs in out.values() for v in vs)
        print('char ids', ids.most_common(60))
        print('cover patterns', funcs.most_common(15))


if __name__ == '__main__':
    main()
