"""Write a new data.cpk into the ROM image without disturbing anything else.

NitroFS here holds two files: data/data.cpk (FAT id 0) then data/sound_data.sdat (id 1), at the end of the ROM.
We keep the cpk start, move sdat right after the new cpk (0x200-aligned), fix the FAT, the used-size field
and the header CRC, and pad with 0xFF to the cartridge size.
"""
import struct

CART = 128 << 20


def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def files(rom):
    fat = struct.unpack_from('<I', rom, 0x48)[0]
    return fat, [struct.unpack_from('<II', rom, fat + 8 * i) for i in range(2)]


def get_cpk(rom):
    _, ((s, e), _) = files(rom)
    return rom[s:e]


def put_cpk(rom, cpk):
    fat, ((cs, ce), (ss, se)) = files(rom)
    assert ss >= ce and se == struct.unpack_from('<I', rom, 0x80)[0], 'unexpected layout'
    sdat = rom[ss:se]
    out = bytearray(rom[:cs])
    out += cpk
    out += b'\xFF' * (-len(out) % 0x200)
    new_ss = len(out)
    out += sdat
    used = len(out)
    if used > CART:
        raise ValueError(f'ROM overflow by {used - CART} bytes')
    out += b'\xFF' * (CART - used)
    struct.pack_into('<IIII', out, fat, cs, cs + len(cpk), new_ss, new_ss + len(sdat))
    struct.pack_into('<I', out, 0x80, used)
    struct.pack_into('<H', out, 0x15E, crc16(out[:0x15E]))
    return bytes(out)
