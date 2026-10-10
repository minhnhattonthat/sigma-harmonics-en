"""Find button rectangles in a texture: runs of 'border' rows/cols along a probe line.

python -X utf8 tools/texprobe.py ID x=55 y=10 ...   # prints colour runs along each vertical (x=) / horizontal (y=) line
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tex  # noqa: E402

im = tex.image((Path(__file__).resolve().parent.parent / 'work' / 'cpk' / sys.argv[1]).read_bytes())
px = im.load()
for arg in sys.argv[2:]:
    axis, v = arg.split('=')
    v = int(v)
    n = im.size[1] if axis == 'x' else im.size[0]
    runs, prev, start = [], None, 0
    for i in range(n):
        c = px[v, i] if axis == 'x' else px[i, v]
        bright = 'T' if c[3] < 128 else ('B' if sum(c[:3]) > 450 else ('m' if sum(c[:3]) > 200 else 'd'))
        if bright != prev:
            if prev is not None:
                runs.append(f'{prev}{start}-{i - 1}')
            prev, start = bright, i
    runs.append(f'{prev}{start}-{n - 1}')
    print(arg, ' '.join(runs))
