"""Disassemble the original arm9 (load 0x02000000, no overlays).

python -X utf8 tools/dis.py ADDR [N] [--thumb]     # N instructions from ADDR (hex)
python -X utf8 tools/dis.py --refs ADDR             # words equal to ADDR (literal pools) and BL/BLX calls to it
"""
import struct
import sys
from functools import lru_cache
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parent.parent
BASE = 0x02000000


@lru_cache(None)
def arm9():
    import ndspy.rom
    return ndspy.rom.NintendoDSRom.fromFile(ROOT / 'rom/Sigma Harmonics (Japan).nds').arm9


def dis(addr, n=40, thumb=False):
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM)
    a9 = arm9()
    out = []
    for ins in md.disasm(a9[addr - BASE:addr - BASE + n * 4], addr):
        out.append(f'{ins.address:08x}  {ins.mnemonic:8} {ins.op_str}')
        if len(out) >= n:
            break
    return out


def refs(target):
    """(literal-pool word addresses, ARM BL call sites, Thumb BL call sites) pointing at target."""
    a9 = arm9()
    lits, arm, thumb = [], [], []
    for i in range(0, len(a9) - 3, 2):
        w = struct.unpack_from('<I', a9, i)[0]
        pc = BASE + i
        if i % 4 == 0:
            if w in (target, target | 1):
                lits.append(pc)
            if w >> 24 in (0xEB, 0xFA):  # BL / BLX imm
                off = (w & 0xFFFFFF) - ((w & 0x800000) << 1)
                dest = pc + 8 + off * 4 + ((w >> 23 & 2) if w >> 24 == 0xFA else 0)
                if dest == target:
                    arm.append(pc)
        hi, lo = w & 0xFFFF, w >> 16
        if hi >> 11 == 0x1E and lo >> 11 in (0x1F, 0x1D):  # Thumb BL / BLX pair
            off = ((hi & 0x7FF) << 12 | (lo & 0x7FF) << 1)
            off -= (off & 0x400000) << 1
            dest = pc + 4 + off
            if lo >> 11 == 0x1D:
                dest &= ~3
            if dest == target:
                thumb.append(pc)
    return lits, arm, thumb


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == '--refs':
        lits, arm, thumb = refs(int(a[1], 16))
        print('literals', [hex(x) for x in lits]); print('arm BL', [hex(x) for x in arm]); print('thumb BL', [hex(x) for x in thumb])
    else:
        print('\n'.join(dis(int(a[0], 16), int(a[1]) if len(a) > 1 and a[1].isdigit() else 40, '--thumb' in a)))
