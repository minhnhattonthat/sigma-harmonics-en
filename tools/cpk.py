"""CRI CPK archive reader: @UTF tables, TOC/ITOC listing, CRILAYLA decompression.

python -X utf8 tools/cpk.py info  work/data.cpk
python -X utf8 tools/cpk.py list  work/data.cpk
python -X utf8 tools/cpk.py dump  work/data.cpk OUTDIR
"""
import struct
import sys
from pathlib import Path

# column storage
ZERO, CONST, PERROW = 0x10, 0x30, 0x50
FMT = {0: '>B', 1: '>b', 2: '>H', 3: '>h', 4: '>I', 5: '>i', 6: '>Q', 7: '>q', 8: '>f'}


def utf_table(buf, off=0):
    """Parse an @UTF table at buf[off:]. Returns (name, rows) with rows = list of dicts."""
    name, cols, rows = utf_parse(buf, off)
    return name, rows


def utf_build(name, cols, rows):
    """Serialize an @UTF table; inverse of utf_parse for the layout CPKMC 1.40 writes."""
    strings = bytearray(b'<NULL>\0')
    smap = {'<NULL>': 0}

    def sref(s):
        if s not in smap:
            smap[s] = len(strings)
            strings.extend(s.encode('cp932') + b'\0')
        return struct.pack('>I', smap[s])

    data = bytearray()

    def enc(typ, v):
        if typ == 0xA:
            return sref(v)
        if typ == 0xB:
            r = struct.pack('>II', len(data), len(v))
            data.extend(v)
            return r
        return struct.pack(FMT[typ], v)

    name_ref = sref(name)
    colbytes = bytearray()
    for cname, flags, const in cols:
        colbytes += bytes([flags]) + sref(cname)
        if flags & 0xF0 == CONST:
            colbytes += enc(flags & 0xF, const)
    rowbytes = bytearray()
    for r in rows:
        for cname, flags, _ in cols:
            if flags & 0xF0 == PERROW:
                rowbytes += enc(flags & 0xF, r[cname])
    rowlen = len(rowbytes) // len(rows) if rows else 0
    rows_off = 24 + len(colbytes)
    str_off = rows_off + len(rowbytes)
    data_off = (str_off + len(strings) + 7) & ~7
    body = struct.pack('>IIIIHHI', rows_off, str_off, data_off, struct.unpack('>I', name_ref)[0],
                       len(cols), rowlen, len(rows)) + colbytes + rowbytes + strings
    body = body.ljust(data_off, b'\0') + data
    body = body.ljust((len(body) + 7) & ~7, b'\0')
    return b'@UTF' + struct.pack('>I', len(body)) + body


def utf_parse(buf, off=0):
    """Parse an @UTF table at buf[off:]. Returns (name, cols, rows); cols = [(name, flags, const)]."""
    assert buf[off:off + 4] == b'@UTF', buf[off:off + 4]
    b = buf[off + 8:]
    rows_off, str_off, data_off, name_off, ncol, rowlen, nrow = struct.unpack('>IIIIHHI', b[:24])

    def cstr(o):
        o += str_off
        return b[o:b.index(b'\0', o)].decode('cp932')

    def val(typ, p):
        if typ == 0xA:
            return cstr(struct.unpack('>I', b[p:p + 4])[0]), 4
        if typ == 0xB:
            o, n = struct.unpack('>II', b[p:p + 8])
            return bytes(b[data_off + o:data_off + o + n]), 8
        f = FMT[typ]
        return struct.unpack(f, b[p:p + struct.calcsize(f)])[0], struct.calcsize(f)

    cols, p = [], 24
    for _ in range(ncol):
        flags = b[p]
        name = cstr(struct.unpack('>I', b[p + 1:p + 5])[0])
        p += 5
        const = None
        if flags & 0xF0 == CONST:
            const, n = val(flags & 0xF, p)
            p += n
        cols.append((name, flags, const))
    rows = []
    for r in range(nrow):
        p = rows_off + r * rowlen
        row = {}
        for name, flags, const in cols:
            st = flags & 0xF0
            if st == PERROW:
                row[name], n = val(flags & 0xF, p)
                p += n
            elif st == CONST:
                row[name] = const
            else:
                row[name] = None
        rows.append(row)
    return cstr(name_off), cols, rows


def chunk_utf(buf, off):
    """A CPK chunk ('TOC ', 'ITOC', ...) is a 16-byte header then an @UTF table."""
    return utf_table(buf, off + 0x10)


def crilayla_decompress(src):
    """Decompress a CRILAYLA blob (header 'CRILAYLA', u32 usize, u32 csize, data, 0x100-byte raw prefix).
    This game zeroes the 8-byte magic."""
    assert src[:8] in (b'CRILAYLA', bytes(8))
    usize, hdr_off = struct.unpack('<II', src[8:16])
    raw = src[0x10 + hdr_off:0x10 + hdr_off + 0x100]
    out = bytearray(usize + 0x100)
    out[:0x100] = raw
    data = src[0x10:0x10 + hdr_off]
    # bitstream read backwards from the end of data, MSB first per byte
    pos = len(data) - 1
    bits_left = 0
    cur = 0

    def get(n):
        nonlocal pos, bits_left, cur
        v = 0
        while n:
            if bits_left == 0:
                cur = data[pos]
                pos -= 1
                bits_left = 8
            take = min(bits_left, n)
            v = (v << take) | ((cur >> (bits_left - take)) & ((1 << take) - 1))
            bits_left -= take
            n -= take
        return v

    w = len(out) - 1
    end = 0x100
    while w >= end:
        if get(1):
            back = get(13) + 3
            length = 3
            for lvl in (2, 3, 5, 8):
                n = get(lvl)
                length += n
                if n != (1 << lvl) - 1:
                    break
            else:
                while True:
                    n = get(8)
                    length += n
                    if n != 0xFF:
                        break
            for _ in range(length):
                out[w] = out[w + back]
                w -= 1
        else:
            out[w] = get(8)
            w -= 1
    return bytes(out)


class Cpk:
    def __init__(self, data):
        self.data = data
        _, (self.header,) = chunk_utf(data, 0)
        self.align = self.header.get('Align') or 1
        self.files = self._itoc() if self.header.get('ItocOffset') else []
        if self.header.get('TocOffset'):
            self.files = self._toc()

    def _toc(self):
        _, rows = chunk_utf(self.data, self.header['TocOffset'])
        base = min(self.header['TocOffset'], self.header['ContentOffset'])
        return [dict(id=r.get('ID'), name=(r.get('DirName') or '') + '/' + r['FileName'],
                     offset=r['FileOffset'] + base, size=r['FileSize'], usize=r['ExtractSize']) for r in rows]

    def _itoc(self):
        _, (it,) = chunk_utf(self.data, self.header['ItocOffset'])
        entries = {}
        for key in ('DataL', 'DataH'):
            if it.get(key):
                _, rows = utf_table(it[key])
                for r in rows:
                    entries[r['ID']] = (r['FileSize'], r['ExtractSize'])
        off = self.header['ContentOffset']
        out = []
        for i in sorted(entries):
            size, usize = entries[i]
            out.append(dict(id=i, name=f'{i:05d}', offset=off, size=size, usize=usize))
            off += (size + self.align - 1) // self.align * self.align
        return out

    def build(self, replace=None):
        """Rebuild the CPK. replace: {id: (stored_bytes, extract_size)}; stored == extract size means uncompressed."""
        replace = replace or {}
        head = bytearray(0x800)
        content = bytearray()
        rows_l, rows_h = [], []
        for f in self.files:
            stored, usize = replace.get(f['id'], (self.raw(f), f['usize']))
            content += stored
            content += bytes(-len(content) % self.align)
            row = {'ID': f['id'], 'FileSize': len(stored), 'ExtractSize': usize}
            (rows_h if len(stored) > 0xFFFF or usize > 0xFFFF else rows_l).append(row)
        _, (info,) = chunk_utf(self.data, self.header['ItocOffset'])
        _, icols, _ = utf_parse(self.data, self.header['ItocOffset'] + 0x10)
        for key, rows in (('DataL', rows_l), ('DataH', rows_h)):
            n, cols, _ = utf_parse(info[key])
            info[key] = utf_build(n, cols, rows)
        info['FilesL'], info['FilesH'] = len(rows_l), len(rows_h)
        itoc = utf_build('CpkItocInfo', icols, [info])
        itoc = b'ITOC' + struct.pack('<IQ', 0xFF, len(itoc)) + itoc

        hdr = dict(self.header)
        hdr['ItocOffset'] = 0x800 + len(content)
        hdr['ItocSize'] = len(itoc)
        hdr['EnabledDataSize'] = sum(r['FileSize'] for r in rows_l + rows_h)
        hdr['EnabledPackedSize'] = sum(r['ExtractSize'] for r in rows_l + rows_h)
        _, hcols, _ = utf_parse(self.data, 0x10)
        h = utf_build('CpkHeader', hcols, [hdr])
        head[:0x10 + len(h)] = b'CPK ' + struct.pack('<IQ', 0xFF, len(h)) + h
        head[0x7FA:0x800] = b'(c)CRI'
        return bytes(head + content + itoc)

    def raw(self, f):
        return self.data[f['offset']:f['offset'] + f['size']]

    def get(self, f):
        b = self.raw(f)
        if f['size'] != f['usize']:
            b = crilayla_decompress(b)
        return b


def main(argv):
    cmd, path = argv[0], argv[1]
    c = Cpk(Path(path).read_bytes())
    if cmd == 'info':
        for k, v in c.header.items():
            print(k, v if not isinstance(v, bytes) else f'<{len(v)} bytes>')
        print('files', len(c.files))
    elif cmd == 'list':
        for f in c.files:
            print(f"{f['id']}\t{f['name']}\t{f['offset']:#x}\t{f['size']}\t{f['usize']}\t{c.raw(f)[:4]!r}")
    elif cmd == 'dump':
        out = Path(argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for f in c.files:
            (out / f['name'].lstrip('/')).parent.mkdir(parents=True, exist_ok=True)
            (out / f['name'].lstrip('/')).write_bytes(c.get(f))


if __name__ == '__main__':
    main(sys.argv[1:])
