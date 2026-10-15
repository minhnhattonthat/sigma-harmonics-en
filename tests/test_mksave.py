import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'debug'))
import mksave  # noqa: E402


def test_new_save_from_game_struct(tmp_path):
    game = bytes(range(256)) * (0x3574 // 256) + bytes(0x3574 % 256)
    (tmp_path / 'game.bin').write_bytes(game)
    out = tmp_path / 'out.dsv'
    subprocess.run([sys.executable, str(ROOT / 'tools/debug/mksave.py'), 'new', str(out), '--state',
                    str(tmp_path / 'game.bin'), '--card', '0xa=7', '--set', '0x100=0x1234:2'], check=True)
    s = out.read_bytes()
    assert len(s) == 0x10000 + len(mksave.FOOTER) and s[:16] == mksave.MAGIC
    st = s[mksave.SLOT0:mksave.SLOT0 + mksave.SIZE]
    assert st[0x100:0x102] == b'\x34\x12'
    assert struct.unpack_from('<I', st, mksave.SUM)[0] == mksave.xor_words(st, 0x353c, mksave.SUM)
    for slot in range(3):
        card = s[mksave.CARDS + slot * mksave.CARD:mksave.CARDS + (slot + 1) * mksave.CARD]
        assert struct.unpack_from('<I', card, 0x10)[0] == mksave.xor_words(card, 0x30, 0x10)
    assert s[mksave.CARDS + 0xa] == 7 and s[mksave.CARDS + mksave.CARD + 8] == 0xff  # slot 1 stays empty
