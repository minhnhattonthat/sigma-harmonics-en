"""Which CPK graphics files are in VRAM? python -X utf8 tools/vrammatch.py DUMPDIR [--min 8]

Reads DUMPDIR/vram_*.bin (tools/lua/vramdump.lua), indexes every non-blank 32-byte tile, and scores each
decompressed CPK file (work/cpk/NNNNN) by how many of its tiles occur in VRAM. Prints the best files.
"""
import sys
from pathlib import Path

d = Path(sys.argv[1])
minhits = int(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 8
vram = {}
for p in sorted(d.glob('vram_*.bin')):
    b = p.read_bytes()
    for i in range(0, len(b) - 31, 32):
        t = b[i:i + 32]
        if t.count(t[0]) < 32:
            vram.setdefault(t, p.stem)
print(f'{len(vram)} distinct non-blank VRAM tiles')
res = []
for f in sorted(Path('work/cpk').iterdir()):
    b = f.read_bytes()
    if len(b) < 64:
        continue
    hits = {}
    for i in range(0, len(b) - 31, 4):
        t = b[i:i + 32]
        if t in vram:
            hits[vram[t]] = hits.get(vram[t], 0) + 1
    n = sum(hits.values())
    if n >= minhits:
        res.append((n, f.name, b[:4], hits))
for n, name, magic, hits in sorted(res, reverse=True)[:40]:
    print(f'{name} {magic!r} {n} {hits}')
