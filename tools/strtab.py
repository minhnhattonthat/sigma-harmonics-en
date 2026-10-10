"""String-table files inside data.cpk: u32 LE (offset, length) pairs, then NUL-terminated UTF-8 strings.

The first entry's offset equals the table size (8 * count). `length` includes the NUL.
"""
import struct


def is_strtab(b):
    if len(b) < 8:
        return False
    first = struct.unpack_from('<I', b)[0]
    if first == 0 or first % 8 or first > len(b):
        return False
    n = first // 8
    end = first
    for i in range(n):
        o, l = struct.unpack_from('<II', b, i * 8)
        if o != end or l == 0 or o + l > len(b) or b[o + l - 1] != 0:
            return False
        end = o + l
    if b[end:].strip(b'\0'):
        return False
    try:
        decode(b)
    except UnicodeDecodeError:
        return False
    return True


def decode(b):
    n = struct.unpack_from('<I', b)[0] // 8
    out = []
    for i in range(n):
        o, l = struct.unpack_from('<II', b, i * 8)
        out.append(b[o:o + l - 1].decode('utf-8'))
    return out


def tail_pad(b):
    """Bytes after the last string (alignment padding), kept for identity rebuilds."""
    n = struct.unpack_from('<I', b)[0] // 8
    o, l = struct.unpack_from('<II', b, (n - 1) * 8)
    return b[o + l:]


def encode(strings, pad=b''):
    head = bytearray()
    body = bytearray()
    base = 8 * len(strings)
    for s in strings:
        e = s.encode('utf-8') + b'\0'
        head += struct.pack('<II', base + len(body), len(e))
        body += e
    return bytes(head + body + pad)
