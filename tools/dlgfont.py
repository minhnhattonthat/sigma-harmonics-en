"""Dialogue bubbles read left-to-right on the sideways DS (docs/re/README.md, Text engine).

The game draws vertical Japanese: one OBJ sprite per glyph, stepping down the player's screen. PATCH turns the
layout code (0x200d35c, 0x200d864) so glyphs step right and lines step down; font 04387 gets CGLP flags 2.
A bubble holds at most MAX_RECORDS records (one per glyph, one per line break; the 61st overwrites the count and
crashes), so English is packed into chunk glyphs of up to CHUNK px, drawn at their natural spacing into font
slots the English doesn't use (kanji). Each line starts with a spacer glyph that centres it, unless the bubble
would run out of records.
"""
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402
import gridfont  # noqa: E402
import latin  # noqa: E402
import nftr  # noqa: E402

FONT = 4387
MAX_RECORDS = 60
CHUNK = 16                 # max chunk advance: the glyph cell is 16 px along the advance
SPACERS = range(1, 31)     # centring pads (DLG_PX / 2)
CURSOR_PAD = 24            # spacer before the page cursor on its own line (centred in game: work/qa/dlg3)

# (address, original word, new word): arm9 is uncompressed at 0x02000000
PATCH = [
    (0x200d3bc, 0xe59d0014, 0xe59d0018),  # ldr r0, [sp, #0x18]  char canvas raw width = text height
    (0x200d3c4, 0xe59d1018, 0xe59d1014),  # ldr r1, [sp, #0x14]  char canvas raw height = text width
    (0x200d4b8, 0xb0877000, 0xe1a00000),  # nop                  no x nudge for narrow glyphs
    (0x200d4c4, 0xc0477000, 0xe1a00000),  # nop
    (0x200d5ac, 0xe1a0100b, 0xe3a01008),  # mov r1, #8           draw centre x: cell origin x = 8 + 8 - 16 = 0
    (0x200d5b0, 0xe1a020a2, 0xe1a0200b),  # mov r2, fp           draw centre y = advance / 2
    (0x200d628, 0xe2860001, 0xe1a00006),  # mov r0, r6           advance = glyph advance, no extra 1 px
    (0x200d778, 0xe3500003, 0xe350000c),  # cmp r0, #12          parser: up to 12 lines (was 3)
    (0x200d88c, 0xe7900006, 0xe3a00037),  # mov r0, #55          first line: y = base - 55
    (0x200d8d0, 0xe59a2008, 0xe2877001),  # add r7, r7, #1       newline: x = x0 - 14 * line, y = base - 55
    (0x200d8d4, 0xe59f0110, 0xe1a00207),  # mov r0, r7, lsl #4
    (0x200d8d8, 0xe3a0100c, 0xe0400087),  # sub r0, r0, r7, lsl #1
    (0x200d8dc, 0xe0200192, 0xe0490000),  # sub r0, sb, r0
    (0x200d8e0, 0xe2877001, 0xe58a0010),  # str r0, [sl, #0x10]
    (0x200d8e4, 0xe0800107, 0xe3a00037),  # mov r0, #55
    (0x200d8e8, 0xe510000c, 0xe0450000),  # sub r0, r5, r0
    (0x200d8ec, 0xe0450000, 0xe58a0014),  # str r0, [sl, #0x14]
    (0x200d8f0, 0xe58a9010, 0xea00000d),  # b 0x200d92c
    (0x200d920, 0xe59a1010, 0xe59a1014),  # ldr r1, [sl, #0x14]  per char: y += advance (was x -= advance)
    (0x200d924, 0xe0410000, 0xe0810000),  # add r0, r1, r0
    (0x200d928, 0xe58a0010, 0xe58a0014),  # str r0, [sl, #0x14]
    # not dialogue: field location label (table 06413) canvas starts at tile row 8, not 12 (128 px room, was 96)
    (0x2048a10, 0xe3a0c00c, 0xe3a0c008),  # mov ip, #8
]
PATCH += gridfont.PATCH  # Descent skill grid rects (static data)


def patch_arm9(rom):
    """ROM bytes with PATCH applied; asserts every original word first."""
    rom = bytearray(rom)
    off, _, ram = struct.unpack_from('<III', rom, 0x20)
    for addr, old, new in PATCH:
        at = off + addr - ram
        assert struct.unpack_from('<I', rom, at)[0] == old, f'arm9 0x{addr:x}: unexpected code'
        struct.pack_into('<I', rom, at, new)
    return bytes(rom)


def adv(s):
    return latin.dlg_adv(s)


def _greedy(text, ok):
    """Split text into the longest pieces that `ok` accepts (single chars always)."""
    out, i = [], 0
    while i < len(text):
        k = i + 1
        while k < len(text) and ok(text[i:k + 1]):
            k += 1
        out.append(text[i:k])
        i = k
    return out


def _parts(line):
    """[(is_code, text)]: $cNN colour codes stay as they are, between chunks."""
    out, pos = [], 0
    for m in fit.CODE.finditer(line):
        if m.start() > pos:
            out.append((False, line[pos:m.start()]))
        out.append((True, m.group()))
        pos = m.end()
    if pos < len(line):
        out.append((False, line[pos:]))
    return out


class Plan:
    """Chunk vocabulary for a set of wrapped dialogue strings, and the codepoints it is drawn into."""

    def __init__(self, texts, slots):
        freq = collections.Counter()
        singles = set()
        for t in texts:
            for ln in t.split(fit.NL):
                for is_code, s in _parts(ln):
                    if not is_code:
                        singles |= set(s)
                        freq.update(_greedy(s, lambda c: adv(c) <= CHUNK))
        slots = list(slots)
        need = len(SPACERS) + len(singles)
        assert len(slots) >= need, f'{len(slots)} font slots < {need}'
        self.code = {}  # chunk text (or ('pad', n)) -> codepoint
        for n in SPACERS:
            self.code[('pad', n)] = slots.pop(0)
        for ch in sorted(singles):
            self.code[ch] = slots.pop(0)
        for chunk, _ in freq.most_common():
            if not slots:
                break
            if len(chunk) > 1:
                self.code[chunk] = slots.pop(0)

    def encode(self, text):
        """Wrapped English (literal \\n breaks) -> the codepoint string the bubble draws. ValueError if over budget."""
        lines = []
        for ln in text.split(fit.NL):
            out, width = [], 0
            for is_code, s in _parts(ln):
                if is_code:
                    out.append(s)
                    continue
                for chunk in _greedy(s, lambda c: c in self.code and adv(c) <= CHUNK):
                    out.append(chr(self.code[chunk]))
                    width += adv(chunk)
            lines.append((out, width))
        records = sum(1 for out, _ in lines for p in out if not p.startswith('$')) + len(lines) - 1
        pads = [(fit.DLG_PX - w) // 2 for _, w in lines]
        centre = records + sum(1 for p in pads if p > 0) <= MAX_RECORDS
        if records > MAX_RECORDS:
            raise ValueError(f'{records} glyph records, max {MAX_RECORDS}')
        out = fit.NL.join(
            (chr(self.code[('pad', min(p, SPACERS[-1]))]) if centre and p > 0 else '') + ''.join(out)
            for (out, _), p in zip(lines, pads))
        # the page cursor is drawn after the last glyph: a last line holding only a spacer centres it under the text
        if len(lines) < fit.DLG_LINES and records + 2 + (len(pads) if centre else 0) <= MAX_RECORDS:
            out += fit.NL + chr(self.code[('pad', CURSOR_PAD)])
        return out

    def font(self, x):
        """Font 04387 bytes: flags 2 and every planned glyph drawn into its slot."""
        p = latin.params(x)
        for key, cp in self.code.items():
            idx = nftr.lookup(x, cp)
            if isinstance(key, tuple):
                bitmap, widths = bytes(p['size']), (0, 0, key[1])  # glyphWidth 0: the blitter draws nothing
            else:
                bitmap, widths = latin.dlg_glyph(key, p, bubble=True)
            x = latin.set_glyph(x, idx, bitmap, widths)
        x = bytearray(x)
        x[bytes(x).find(b'PLGC') + 15] = 2
        return bytes(x)


def slots(x, keep):
    """Codepoints of font x free for chunks: CJK ideographs not in `keep` (chars still drawn as Japanese).
    U+4E00 is skipped: the layout code adds 6 px after it."""
    return sorted(c for c in nftr.codes(x) if 0x4E01 <= c <= 0x9FFF and chr(c) not in keep)
