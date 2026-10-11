"""Package a release: xdelta patch of build/sigma_en.nds against the original ROM, re-applied and compared, then
release/Sigma_Harmonics_EN_vX.Y.zip (patch + README, stored). Prints the hashes the README lists.

python -X utf8 tools/release.py 0.9      # build first: tools/build.py; needs xdelta3 on PATH
"""
import hashlib
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import text  # noqa: E402

BUILT = ROOT / 'build' / 'sigma_en.nds'
README = ROOT / 'docs' / 'release-readme.md'


def hashes(p):
    b = p.read_bytes()
    return {'size': len(b), 'crc32': f'{zlib.crc32(b):08x}', 'md5': hashlib.md5(b).hexdigest(),
            'sha1': hashlib.sha1(b).hexdigest()}


def main(version):
    xd = shutil.which('xdelta3')
    assert xd, 'xdelta3 not on PATH'
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    name = f'Sigma_Harmonics_EN_v{version}'
    patch, check = out / f'{name}.xdelta', out / 'verify.nds'
    subprocess.run([xd, '-e', '-9', '-f', '-s', str(text.ROM), str(BUILT), str(patch)], check=True)
    subprocess.run([xd, '-d', '-f', '-s', str(text.ROM), str(patch), str(check)], check=True)
    assert check.read_bytes() == BUILT.read_bytes(), 'patch does not reproduce the build'
    check.unlink()
    with zipfile.ZipFile(out / f'{name}.zip', 'w', zipfile.ZIP_STORED) as z:  # xdelta is already compressed
        z.write(patch, patch.name)
        z.write(README, 'README.md')
    for label, p in (('original', text.ROM), ('patched', BUILT)):
        print(label, hashes(p))
    print(f'release: {out / name}.zip ({patch.stat().st_size} byte patch)')


if __name__ == '__main__':
    main(sys.argv[1])
