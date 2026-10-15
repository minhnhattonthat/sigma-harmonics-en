"""Build or patch a Sigma Harmonics battery save (.dsv) and fix its checksums.

python -X utf8 tools/debug/mksave.py IN.dsv|new OUT.dsv [--slot 0] [--state game.bin] [--set OFF=VAL[:SIZE]]..
       [--card OFF=VAL[:SIZE]].. [--unlock]

Layout (arm9 0x205b3f0 / 0x205e1a0): 0x00 "SIGMA V000.001 \\0"; 0x10 three 0x34-byte slot cards; 0xac + slot*0x3540
the slots. In RAM the card and state sit together at 0x215ef10 (card 0x34 bytes, then the state 0x3540 bytes).
Card: +8 chapter (0xff = empty slot), +0xa room (scenario script 5914+n; 1 = New Game's room), +0x10 = XOR of the
card's first 12 words with that field zeroed. State +0x3218 = XOR of the state's words below 0x353c, itself excluded.
IN "new" starts from an empty save. --state takes game.bin from tools/debug/capture.lua (card + state, 0x3574
bytes) or a bare 0x3540-byte state. --set writes VAL (int, 0x ok) little-endian, SIZE bytes (default 1), at state
offset OFF; --card the same at card offset OFF.
"""
import argparse
import struct
from pathlib import Path

CARDS, SLOT0, SIZE, SUM, CARD = 0x10, 0xac, 0x3540, 0x3218, 0x34
MAGIC = b'SIGMA V000.001 \0'
# DeSmuME's footer for a 64 KB EEPROM save (size, padded size, type 3, address bytes 2, mem size, 0)
FOOTER = (b'|<--Snip above here to create a raw sav by excluding this DeSmuME savedata footer:'
          + struct.pack('<6I', 0x10000, 0x10000, 3, 2, 0x10000, 0) + b'|-DESMUME SAVE-|')


def xor_words(b, end, skip):
    x = 0
    for i in range(0, end, 4):
        if i != skip:
            x ^= struct.unpack_from('<I', b, i)[0]
    return x


def empty():
    save = bytearray(b'\xff' * 0x10000) + FOOTER
    save[:16] = MAGIC
    for slot in range(3):
        card = bytearray(CARD)
        card[8:12] = b'\xff\xff\xff\x00'
        struct.pack_into('<II', card, 0x2c, 0x353c, 0x30)
        save[CARDS + slot * CARD:CARDS + (slot + 1) * CARD] = card
        fix(save, slot, state=False)
    return save


def fix(save, slot, state=True):
    if state:
        o = SLOT0 + slot * SIZE
        st = bytearray(save[o:o + SIZE])
        struct.pack_into('<I', st, SUM, xor_words(st, 0x353c, SUM))
        save[o:o + SIZE] = st
    d = CARDS + slot * CARD
    card = bytearray(save[d:d + CARD])
    struct.pack_into('<I', card, 0x10, xor_words(card, 0x30, 0x10))
    save[d:d + CARD] = card


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--slot', type=int, default=0)
    ap.add_argument('--state')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--card', action='append', default=[])
    ap.add_argument('--unlock', action='store_true', help='every field-menu button and all 13 Shiki cards')
    a = ap.parse_args()
    if a.unlock:  # menu button i is greyed unless state +0x1b0+i != 0 (0x20492c8); card k: 12-byte record at +0x18
        a.set = ['0x1b0=0x0101010101010101:8'] + [f'{0x18 + 12 * k:#x}=0x010101:3' for k in range(13)] + a.set
    save = empty() if a.src == 'new' else bytearray(Path(a.src).read_bytes())
    o, d = SLOT0 + a.slot * SIZE, CARDS + a.slot * CARD
    if a.state:
        st = Path(a.state).read_bytes()
        assert len(st) in (SIZE, CARD + SIZE), f'state must be {SIZE:#x} or {CARD + SIZE:#x} bytes'
        if len(st) > SIZE:
            save[d:d + CARD], st = st[:CARD], st[CARD:]
        save[o:o + SIZE] = st
    for base, sets in ((o, a.set), (d, a.card)):
        for s in sets:
            off, val = s.split('=')
            val, n = (val.split(':') + ['1'])[:2]
            save[base + int(off, 0):base + int(off, 0) + int(n)] = int(val, 0).to_bytes(int(n), 'little')
    fix(save, a.slot)
    Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
    Path(a.dst).write_bytes(save)


if __name__ == '__main__':
    main()
